import ctypes
from ctypes import cast, POINTER
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

def get_volume_interface():
    """Obtiene la interfaz de control de volumen maestro de Windows."""
    try:
        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
        return cast(interface, POINTER(IAudioEndpointVolume))
    except:
        return None

def set_system_volume(level):
    """Establece el volumen del sistema (0 a 100)."""
    try:
        volume = get_volume_interface()
        if volume:
            # Escalar de 0-100 a 0.0-1.0
            volume.SetMasterVolumeLevelScalar(level / 100.0, None)
    except Exception as e:
        print(f"Error estableciendo volumen: {e}")

def get_current_volume():
    """Obtiene el volumen actual del sistema (0 a 100)."""
    try:
        volume = get_volume_interface()
        if volume:
            current_vol = volume.GetMasterVolumeLevelScalar()
            return int(current_vol * 100)
    except:
        pass
    return 50
