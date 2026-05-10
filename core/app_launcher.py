import subprocess
import os
import psutil
import ctypes

# Constantes de Windows
SW_RESTORE = 9

# Lista global para rastrear procesos lanzados en la sesión actual
# Ahora guarda: {'process': proc, 'app_info': app_info}
_launched_processes = []

def bring_app_to_front(pid):
    """
    Encuentra las ventanas asociadas a un PID y las trae al primer plano.
    """
    def callback(hwnd, extra):
        if ctypes.windll.user32.IsWindowVisible(hwnd):
            lp_pid = ctypes.c_ulong()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(lp_pid))
            if lp_pid.value == pid:
                # Recuperar la lista desde el puntero extra
                hwnds = ctypes.cast(extra, ctypes.py_object).value
                hwnds.append(hwnd)
        return True

    hwnds = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_void_p)
    
    # Pasamos la lista como un objeto de Python convertido a puntero void
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
    
    # Soporte para cuando se pasa solo el path (compatibilidad)
    if isinstance(app_info, str):
        app_info = {'path': app_info, 'name': os.path.basename(app_info)}
        
    path = app_info.get('path', '')
    
    # 1. Limpiar procesos muertos y verificar si ya está abierta
    _launched_processes = [p for p in _launched_processes if p['process'].poll() is None]
    
    for item in _launched_processes:
        if item['app_info'].get('path') == path:
            # Ya está abierta, traer al frente
            bring_app_to_front(item['process'].pid)
            return True

    # 2. Si no está abierta, lanzarla
    try:
        if not os.path.exists(path):
            print(f"Error: No se encontró el ejecutable en {path}")
            return False
        
        proc = subprocess.Popen(path)
        _launched_processes.append({'process': proc, 'app_info': app_info})
        return True
    except Exception as e:
        print(f"Error al lanzar la aplicación: {e}")
        return False

def get_running_apps():
    """
    Devuelve la lista de aplicaciones que están actualmente en ejecución.
    """
    global _launched_processes
    # Limpiar procesos muertos
    _launched_processes = [p for p in _launched_processes if p['process'].poll() is None]
    return _launched_processes

def close_all_launched_apps():
    """
    Cierra todos los procesos que fueron abiertos por el lanzador.
    """
    global _launched_processes
    for item in _launched_processes:
        proc = item['process']
        try:
            parent = psutil.Process(proc.pid)
            for child in parent.children(recursive=True):
                child.terminate()
            parent.terminate()
        except:
            pass
    
    _launched_processes = []
    return True
