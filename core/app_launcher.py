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


def _path_exists_robust(path: str) -> bool:
    """Comprueba si un path es ejecutable, incluyendo reparse points de MSIX.

    Los shims de WindowsApps (p.ej. ``ms-teams.exe`` para el paquete MSIX
    de Teams) son archivos de 0 bytes con un reparse point. ``os.path.exists``
    los trata como no existentes en algunos casos, mientras que
    ``os.path.isfile`` los reconoce correctamente como archivos.
    """
    if not path:
        return False
    try:
        if os.path.isfile(path):
            return True
    except OSError:
        return False
    # Si no es un archivo regular, comprobar si al menos existe la ruta
    # (cubre ``shell:appsfolder\...`` o rutas del PATH tipo ``ms-teams``).
    return os.path.exists(path)


def _is_msix_apps_shim(path: str) -> bool:
    """Detecta si un path es un shim de WindowsApps (MSIX App Execution Alias)."""
    if not path:
        return False
    norm = os.path.normpath(path).lower()
    return "\\windowsapps\\" in norm and norm.endswith(".exe")


def _process_matches_shim(proc, shim_path: str) -> bool:
    """Considera que un proceso coincide con un shim MSIX si:
      * su ejecutable es el shim exacto, o
      * su ejecutable está en la misma carpeta WindowsApps y comparte nombre
        de archivo (porque la versión del paquete cambia con cada update).
    """
    try:
        exe = proc.exe()
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return False
    if not exe:
        return False
    try:
        if os.path.normpath(exe).lower() == os.path.normpath(shim_path).lower():
            return True
    except OSError:
        pass
    shim_norm = os.path.normpath(shim_path).lower()
    exe_norm = os.path.normpath(exe).lower()
    shim_dir, shim_name = os.path.split(shim_norm)
    exe_dir, exe_name = os.path.split(exe_norm)
    if shim_name and shim_name == exe_name and "\\windowsapps\\" in exe_dir:
        return True
    return False


def find_running_process_by_path(path):
    """
    Busca si existe algún proceso en ejecución cuyo ejecutable coincida con 'path'.
    Intenta ser flexible con formatos de ruta de Windows.
    Para shims MSIX (WindowsApps\\ms-*.exe), busca por nombre de archivo
    en cualquier subcarpeta de WindowsApps porque la versión del paquete
    cambia con cada actualización.
    """
    if not path:
        return None

    # Expandir variables de entorno (ej: %LocalAppData%)
    path = os.path.expandvars(path)
    if not _path_exists_robust(path) and not _is_msix_apps_shim(path):
        return None

    target_path = os.path.normpath(path).lower()
    is_shim = _is_msix_apps_shim(path)

    for proc in psutil.process_iter(['exe']):
        try:
            exe = proc.info.get('exe')
            if not exe:
                continue
            if os.path.normpath(exe).lower() == target_path:
                return proc
            # Intento adicional: samefile (más robusto con symlinks/shortpaths)
            try:
                if os.path.samefile(exe, path):
                    return proc
            except Exception:
                pass
            # Shims MSIX: aceptar cualquier proceso con el mismo nombre de exe
            if is_shim and _process_matches_shim(proc, path):
                return proc
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    return None

def bring_app_to_front(pid, app_path=None):
    """
    Encuentra las ventanas asociadas a un PID (o a un ejecutable) y las trae al primer plano.
    Retorna True si encontró y activó al menos una ventana visible, False de lo contrario.
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

    if not hwnds:
        return False

    for hwnd in hwnds:
        # SW_RESTORE (9) restaura la ventana si está minimizada y la activa
        ctypes.windll.user32.ShowWindow(hwnd, SW_RESTORE)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
    return True

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
        activated = bring_app_to_front(existing_proc.pid, expanded_path)
        if activated:
            # Sincronizar con la lista de seguimiento
            if not any(p['app_info'].get('path') == path for p in _launched_processes):
                _launched_processes.append({'process': existing_proc, 'app_info': app_info})
            log_app_launched(
                app_info.get('name', os.path.basename(expanded_path)),
                expanded_path,
                pid=existing_proc.pid,
            )
            return None
        else:
            logger.info("El proceso %d (%s) está en ejecución pero no tiene ventanas visibles. Intentando relanzar para despertar.", existing_proc.pid, expanded_path)

    # 2. Si no está abierta (o si está corriendo en segundo plano sin ventanas visibles), lanzarla
    try:
        if not _path_exists_robust(expanded_path):
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
            except Exception:
                continue

        for app in configured_apps:
            path = app.get('path')
            if not path:
                continue

            expanded_path = os.path.expandvars(path)
            norm_path = os.path.normpath(expanded_path).lower()
            is_shim = _is_msix_apps_shim(expanded_path)

            if norm_path in seen_paths:
                continue

            # Coincidencia exacta por ruta
            proc = system_procs.get(norm_path)
            if not proc and is_shim:
                # Shims MSIX: buscar por nombre de archivo en WindowsApps
                shim_name = os.path.basename(norm_path)
                for sys_path, sys_proc in system_procs.items():
                    if "\\windowsapps\\" in sys_path and os.path.basename(sys_path) == shim_name:
                        proc = sys_proc
                        break

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
