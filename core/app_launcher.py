import subprocess
import os

def launch_application(path):
    """
    Lanza una aplicación externa dado su path.
    """
    try:
        if not os.path.exists(path):
            print(f"Error: No se encontró el ejecutable en {path}")
            return False
        
        # Usamos Popen para que sea no bloqueante para nuestra app UI
        subprocess.Popen(path)
        return True
    except Exception as e:
        print(f"Error al lanzar la aplicación: {e}")
        return False
