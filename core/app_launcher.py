import subprocess
import os
import psutil
import ctypes

from core.audit import log_app_launched, log_app_closed, log_app_launch_failed
from core.logger import get_logger

logger = get_logger("core.app_launcher")

# Constantes de Windows
SW_RESTORE = 9

# Lista global para rastrear procesos lanzados en la sesión actual
# Ahora guarda: {'process': proc, 'app_info': app_info}
_launched_processes = []

def find_running_process_by_path(path):
    """
    Busca si existe algún proceso en ejecución cuyo ejecutable coincida con 'path'.
    Intenta ser flexible con formatos de ruta de Windows.
    """
    if not path:
        return None
    
    # Expandir variables de entorno (ej: %LocalAppData%)
    path = os.path.expandvars(path)
    if not os.path.exists(path):
        return None
    
    target_path = os.path.normpath(path).lower()
    
    for proc in psutil.process_iter(['exe']):
        try:
            exe = proc.info.get('exe')
            if exe:
                if os.path.normpath(exe).lower() == target_path:
                    return proc
                # Intento adicional: samefile (más robusto con symlinks/shortpaths)
                try:
                    if os.path.samefile(exe, path):
                        return proc
                except: pass
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def bring_app_to_front(pid, app_path=None):
    """
    Encuentra las ventanas asociadas a un PID (o a un ejecutable) y las trae al primer plano.
    """
    target_path = os.path.normpath(os.path.expandvars(app_path)).lower() if app_path else None
    
    def callback(hwnd, extra):
        if ctypes.windll.user32.IsWindowVisible(hwnd):
            lp_pid = ctypes.c_ulong()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(lp_pid))
            
            match = False
            if lp_pid.value == pid:
                match = True
            elif target_path:
                try:
                    p = psutil.Process(lp_pid.value)
                    exe = p.exe()
                    if exe:
                        if os.path.normpath(exe).lower() == target_path:
                            match = True
                        else:
                            try:
                                if os.path.samefile(exe, target_path):
                                    match = True
                            except: pass
                except: pass
            
            if match:
                hwnds = ctypes.cast(extra, ctypes.py_object).value
                hwnds.append(hwnd)
        return True

    hwnds = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)
    ctypes.windll.user32.EnumWindows(WNDENUMPROC(callback), ctypes.py_object(hwnds))

    for hwnd in hwnds:
        # SW_RESTORE (9) restaura la ventana si está minimizada y la activa
        ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
        ctypes.windll.user32.SetForegroundWindow(hwnd)

def launch_application(app_info):
    """
    Lanza una aplicación externa o la trae al frente si ya está abierta.
    """
    global _launched_processes
    
    if isinstance(app_info, str):
        app_info = {'path': app_info, 'name': os.path.basename(app_info)}
        
    path = app_info.get('path', '')
    expanded_path = os.path.expandvars(path)
    
    # 1. Verificar si ya hay una instancia corriendo en el sistema
    existing_proc = find_running_process_by_path(expanded_path)
    if existing_proc:
        bring_app_to_front(existing_proc.pid, expanded_path)
        # Sincronizar con la lista de seguimiento
        if not any(p['app_info'].get('path') == path for p in _launched_processes):
            _launched_processes.append({'process': existing_proc, 'app_info': app_info})
        log_app_launched(
            app_info.get('name', os.path.basename(expanded_path)),
            expanded_path,
            pid=existing_proc.pid,
        )
        return None

    # 2. Si no está abierta, lanzarla
    try:
        if not os.path.exists(expanded_path):
            error_msg = f"No se encontró el ejecutable:\n{expanded_path}"
            log_app_launch_failed(
                app_info.get('name', os.path.basename(expanded_path)),
                expanded_path,
                error=error_msg,
            )
            return error_msg

        proc = subprocess.Popen(expanded_path)
        _launched_processes.append({'process': proc, 'app_info': app_info})
        log_app_launched(
            app_info.get('name', os.path.basename(expanded_path)),
            expanded_path,
            pid=proc.pid,
        )
        return None
    except Exception as e:
        error_msg = f"No se pudo abrir la aplicación:\n{e}"
        log_app_launch_failed(
            app_info.get('name', os.path.basename(expanded_path)),
            expanded_path,
            error=str(e),
        )
        return error_msg

def get_running_apps(configured_apps=None):
    """
    Devuelve la lista de aplicaciones que están actualmente en ejecución.
    Combina el seguimiento de procesos lanzados con un escaneo del sistema para mayor robustez.
    """
    global _launched_processes
    
    active_list = []
    seen_paths = set()

    # 1. Primero, revisar los procesos que ya estábamos siguiendo
    for item in list(_launched_processes):
        p = item['process']
        path = item['app_info'].get('path')
        is_alive = False
        try:
            if hasattr(p, 'poll'): # Objeto Popen de subprocess
                is_alive = p.poll() is None
            else: # Objeto Process de psutil
                is_alive = p.is_running() and p.status() != psutil.STATUS_ZOMBIE
        except: pass
        
        if is_alive:
            active_list.append(item)
            if path: seen_paths.add(os.path.normpath(os.path.expandvars(path)).lower())
        else:
            # Si el proceso que lanzamos murió (ej: Chrome delegó), 
            # intentamos re-detectar por su ruta inmediatamente
            if path:
                new_p = find_running_process_by_path(path)
                if new_p:
                    item['process'] = new_p
                    active_list.append(item)
                    seen_paths.add(os.path.normpath(os.path.expandvars(path)).lower())

    # 2. Si se proporcionan las apps configuradas, buscamos las que faltan (ej: abiertas antes del kiosco)
    if configured_apps:
        # Optimización: Escanear todos los procesos una sola vez y cachear por ejecutable
        system_procs = {}
        for proc in psutil.process_iter(['exe']):
            try:
                exe = proc.info.get('exe')
                if exe:
                    system_procs[os.path.normpath(exe).lower()] = proc
            except: continue
            
        for app in configured_apps:
            path = app.get('path')
            if not path: continue
            
            expanded_path = os.path.expandvars(path)
            norm_path = os.path.normpath(expanded_path).lower()
            
            if norm_path not in seen_paths:
                # Buscar en el cache de procesos del sistema
                proc = system_procs.get(norm_path)
                if proc:
                    active_list.append({'process': proc, 'app_info': app})
                    seen_paths.add(norm_path)

    _launched_processes = active_list
    return _launched_processes

def close_single_app(pid):
    """
    Cierra el proceso con el PID dado y lo elimina de la lista de seguimiento.
    Devuelve True si se terminó correctamente, False si el proceso no se encontró.
    """
    global _launched_processes
    for item in list(_launched_processes):
        if item['process'].pid == pid:
            app_name = item['app_info'].get('name', '')
            app_path = item['app_info'].get('path', '')
            try:
                parent = psutil.Process(pid)
                for child in parent.children(recursive=True):
                    child.terminate()
                parent.terminate()
            except Exception:
                pass
            _launched_processes = [p for p in _launched_processes if p['process'].pid != pid]
            log_app_closed(app_name, app_path, pid=pid)
            return True
    return False


def close_all_launched_apps():
    """
    Cierra todos los procesos que fueron abiertos por el lanzador.
    """
    global _launched_processes
    for item in _launched_processes:
        proc = item['process']
        app_name = item['app_info'].get('name', '')
        app_path = item['app_info'].get('path', '')
        try:
            parent = psutil.Process(proc.pid)
            for child in parent.children(recursive=True):
                child.terminate()
            parent.terminate()
        except:
            pass
        log_app_closed(app_name, app_path, pid=proc.pid)

    _launched_processes = []
    return True
