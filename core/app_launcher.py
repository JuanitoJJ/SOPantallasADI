import subprocess
import os
import psutil

# Lista global para rastrear procesos lanzados en la sesión actual
_launched_processes = []

def launch_application(path):
    """
    Lanza una aplicación externa y guarda la referencia al proceso.
    """
    try:
        if not os.path.exists(path):
            print(f"Error: No se encontró el ejecutable en {path}")
            return False
        
        # Usamos Popen y guardamos el objeto
        proc = subprocess.Popen(path)
        _launched_processes.append(proc)
        return True
    except Exception as e:
        print(f"Error al lanzar la aplicación: {e}")
        return False

def close_all_launched_apps():
    """
    Cierra todos los procesos que fueron abiertos por el lanzador durante la sesión.
    """
    global _launched_processes
    for proc in _launched_processes:
        try:
            # Intentar terminar de forma elegante
            parent = psutil.Process(proc.pid)
            for child in parent.children(recursive=True):
                child.terminate()
            parent.terminate()
        except:
            # Si falla, simplemente ignorar (el proceso puede haber sido cerrado ya)
            pass
    
    _launched_processes = []
    return True
