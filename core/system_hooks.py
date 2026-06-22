import ctypes
from ctypes import wintypes
import threading
from core.logger import get_logger


logger = get_logger("core.system_hooks")


WH_KEYBOARD_LL = 13
HC_ACTION = 0
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104

VK_LWIN = 0x5B
VK_RWIN = 0x5C
VK_ESCAPE = 0x1B
VK_F4 = 0x73
VK_F11 = 0x7A
VK_TAB = 0x09
VK_LMENU = 0xA4
VK_RMENU = 0xA5
VK_LCONTROL = 0xA2
VK_RCONTROL = 0xA3
VK_LSHIFT = 0xA0
VK_RSHIFT = 0xA1


KBDLLHOOKSTRUCT = ctypes.c_uint * 4

LowLevelKeyboardProc = ctypes.WINFUNCTYPE(
    ctypes.c_int,
    ctypes.c_int,
    wintypes.WPARAM,
    ctypes.POINTER(KBDLLHOOKSTRUCT),
)

GetModuleHandleW = ctypes.windll.kernel32.GetModuleHandleW
GetModuleHandleW.restype = wintypes.HMODULE
GetModuleHandleW.argtypes = [wintypes.LPCWSTR]

SetWindowsHookExW = ctypes.windll.user32.SetWindowsHookExW
SetWindowsHookExW.restype = wintypes.HHOOK
SetWindowsHookExW.argtypes = [ctypes.c_int, LowLevelKeyboardProc, wintypes.HINSTANCE, wintypes.DWORD]

UnhookWindowsHookEx = ctypes.windll.user32.UnhookWindowsHookEx
UnhookWindowsHookEx.restype = wintypes.BOOL
UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]

CallNextHookEx = ctypes.windll.user32.CallNextHookEx
CallNextHookEx.restype = ctypes.c_int
CallNextHookEx.argtypes = [wintypes.HHOOK, ctypes.c_int, wintypes.WPARAM, ctypes.POINTER(KBDLLHOOKSTRUCT)]

GetMessageW = ctypes.windll.user32.GetMessageW
GetMessageW.argtypes = [
    ctypes.POINTER(ctypes.c_uint * 6),
    wintypes.HWND,
    wintypes.UINT,
    wintypes.UINT,
]
GetMessageW.restype = wintypes.BOOL

TranslateMessage = ctypes.windll.user32.TranslateMessage
DispatchMessageW = ctypes.windll.user32.DispatchMessageW

PostThreadMessageW = ctypes.windll.user32.PostThreadMessageW
PostThreadMessageW.restype = wintypes.BOOL
PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]

WM_QUIT = 0x0012


class KioskManager:
    _instance = None
    _lock = threading.Lock()
    _blocked_keys = [
        "L/R Windows",
        "Alt+Tab",
        "Ctrl+Esc",
        "Alt+F4",
        "Shift+F10",
        "F11",
    ]

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self.is_active = False
        self._hook_id = None
        self._hook_thread = None
        self._thread_id = None
        self._should_stop = threading.Event()
        self._hook_thread_failed = False

    @property
    def blocked_keys(self):
        return self._blocked_keys

    def _should_block(self, vk_code: int, msg: int) -> bool:
        if msg not in (WM_KEYDOWN, WM_SYSKEYDOWN):
            return False

        if vk_code in (VK_LWIN, VK_RWIN, VK_ESCAPE, VK_F4, VK_F11):
            return True

        if vk_code == VK_TAB and (GetAsyncKeyState(VK_LMENU) & 0x8000 or GetAsyncKeyState(VK_RMENU) & 0x8000):
            return True

        if vk_code == VK_ESCAPE and (GetAsyncKeyState(VK_LCONTROL) & 0x8000 or GetAsyncKeyState(VK_RCONTROL) & 0x8000):
            return True

        if vk_code == VK_F10 and (GetAsyncKeyState(VK_LSHIFT) & 0x8000 or GetAsyncKeyState(VK_RSHIFT) & 0x8000):
            return True

        return False

    def _low_level_keyboard_handler(self, n_code, w_param, l_param):
        if n_code == HC_ACTION and l_param:
            vk_code = l_param.contents[0]
            if self._should_block(vk_code, w_param):
                logger.debug("Tecla bloqueada VK=0x%X", vk_code)
                return 1
        return CallNextHookEx(self._hook_id, n_code, w_param, l_param)

    def _hook_proc(self):
        try:
            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32

            GetAsyncKeyState = user32.GetAsyncKeyState
            GetAsyncKeyState.restype = ctypes.c_short
            GetAsyncKeyState.argtypes = [ctypes.c_int]
            globals()["GetAsyncKeyState"] = GetAsyncKeyState

            h_module = GetModuleHandleW(None)
            proc = LowLevelKeyboardProc(self._low_level_keyboard_handler)
            self._hook_id = SetWindowsHookExW(WH_KEYBOARD_LL, proc, h_module, 0)

            if not self._hook_id:
                logger.error("No se pudo instalar el hook de teclado")
                self._hook_thread_failed = True
                return

            self._thread_id = kernel32.GetCurrentThreadId()
            logger.info("Hook de teclado instalado (thread %d)", self._thread_id)

            msg = (ctypes.c_uint * 6)()
            while not self._should_stop.is_set():
                ret = GetMessageW(msg, None, 0, 0)
                if ret == 0 or ret == -1:
                    break
                TranslateMessage(msg)
                DispatchMessageW(msg)

            if self._hook_id:
                UnhookWindowsHookEx(self._hook_id)
                self._hook_id = None
                logger.info("Hook de teclado desinstalado")
        except Exception as exc:
            logger.exception("Error en hilo de hook: %s", exc)
            self._hook_thread_failed = True

    def start(self):
        if self.is_active:
            return
        self._should_stop.clear()
        self._hook_thread_failed = False
        self._hook_thread = threading.Thread(target=self._hook_proc, daemon=True, name="KioskHookThread")
        self._hook_thread.start()
        self.is_active = True
        logger.info("Modo Kiosco: bloqueo de teclas activado")

    def stop(self):
        if not self.is_active:
            return
        self._should_stop.set()
        if self._thread_id:
            try:
                PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
            except Exception:
                pass
        if self._hook_thread and self._hook_thread.is_alive():
            self._hook_thread.join(timeout=2.0)
        self.is_active = False
        logger.info("Modo Kiosco: bloqueo de teclas desactivado")


kiosk = KioskManager()
