
import ctypes
import os
from ctypes import wintypes

if os.name != "nt":
    raise OSError("Vingo currently supports Windows only.")

user32 = ctypes.WinDLL("user32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

WNDPROC = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [
        ("style", wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HANDLE),
        ("hCursor", wintypes.HANDLE),
        ("hbrBackground", wintypes.HANDLE),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR),
    ]


class POINT(ctypes.Structure):
    _fields_ = [
        ("x", wintypes.LONG),
        ("y", wintypes.LONG),
    ]


class MSG(ctypes.Structure):
    _fields_ = [
        ("hwnd", wintypes.HWND),
        ("message", wintypes.UINT),
        ("wParam", wintypes.WPARAM),
        ("lParam", wintypes.LPARAM),
        ("time", wintypes.DWORD),
        ("pt", POINT),
        ("lPrivate", wintypes.DWORD),
    ]


user32.DefWindowProcW.restype = ctypes.c_ssize_t
user32.DefWindowProcW.argtypes = [
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
]

user32.CreateWindowExW.restype = wintypes.HWND
user32.CreateWindowExW.argtypes = [
    wintypes.DWORD,
    wintypes.LPCWSTR,
    wintypes.LPCWSTR,
    wintypes.DWORD,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    ctypes.c_int,
    wintypes.HWND,
    wintypes.HMENU,
    wintypes.HINSTANCE,
    wintypes.LPVOID,
]

user32.RegisterClassW.restype = wintypes.ATOM
user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]

user32.GetMessageW.restype = ctypes.c_int
user32.GetMessageW.argtypes = [
    ctypes.POINTER(MSG),
    wintypes.HWND,
    wintypes.UINT,
    wintypes.UINT,
]

user32.TranslateMessage.argtypes = [ctypes.POINTER(MSG)]
user32.DispatchMessageW.argtypes = [ctypes.POINTER(MSG)]
user32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
user32.UpdateWindow.argtypes = [wintypes.HWND]
user32.SetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPCWSTR]

kernel32.GetModuleHandleW.restype = wintypes.HMODULE
kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]

gdi32.CreateSolidBrush.restype = wintypes.HANDLE
gdi32.CreateSolidBrush.argtypes = [wintypes.DWORD]
gdi32.DeleteObject.argtypes = [wintypes.HANDLE]

WM_DESTROY = 0x0002
CS_HREDRAW = 0x0002
CS_VREDRAW = 0x0001
WS_OVERLAPPEDWINDOW = 0x00CF0000
SW_SHOW = 5

_COLORS = {
    "blue": (0, 0, 255),
    "red": (255, 0, 0),
    "green": (0, 128, 0),
    "white": (255, 255, 255),
    "black": (0, 0, 0),
    "yellow": (255, 255, 0),
    "purple": (128, 0, 128),
    "orange": (255, 165, 0),
    "gray": (128, 128, 128),
    "grey": (128, 128, 128),
}

_width = 600
_height = 500
_color = "white"
_title = "Vingo"
_hwnd = None
_brush = None
_class_name = "VingoNativeWindowClass"


def windowmake(width, height, color="white"):
    """Configure the native Windows window."""
    global _width, _height, _color

    if _hwnd:
        raise RuntimeError("The window has already been created.")

    if not isinstance(width, int) or not isinstance(height, int):
        raise TypeError("Width and height must be integers.")

    if width <= 0 or height <= 0:
        raise ValueError("Width and height must be positive.")

    if not isinstance(color, str):
        raise TypeError("Color must be a string.")

    color = color.lower()

    if color not in _COLORS:
        if len(color) == 7 and color.startswith("#"):
            try:
                rgb = tuple(
                    int(color[i:i + 2], 16)
                    for i in (1, 3, 5)
                )
            except ValueError as exc:
                raise ValueError("Invalid hex color.") from exc
        else:
            raise ValueError(f"Unsupported color: {color}")
    else:
        rgb = _COLORS[color]

    _width = width
    _height = height
    _color = color


def windowsetname(name):
    """Set the window title."""
    global _title

    if not isinstance(name, str):
        raise TypeError("Window name must be a string.")

    _title = name

    if _hwnd:
        if not user32.SetWindowTextW(_hwnd, _title):
            raise ctypes.WinError(ctypes.get_last_error())


def _window_proc(hwnd, msg, wparam, lparam):
    if msg == WM_DESTROY:
        user32.PostQuitMessage(0)
        return 0

    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)


def run():
    """Create and display the native window."""
    global _hwnd, _brush

    if _hwnd:
        raise RuntimeError("Vingo is already running.")

    if not _width or not _height:
        raise RuntimeError("Invalid window dimensions.")

    rgb = (
        tuple(
            int(_color[i:i + 2], 16)
            for i in (1, 3, 5)
        )
        if _color.startswith("#")
        else _COLORS[_color]
    )

    # Windows COLORREF uses the order 0x00BBGGRR.
    colorref = rgb[0] | (rgb[1] << 8) | (rgb[2] << 16)
    _brush = gdi32.CreateSolidBrush(colorref)

    if not _brush:
        raise ctypes.WinError(ctypes.get_last_error())

    instance = kernel32.GetModuleHandleW(None)

    # Keep the callback alive while Windows uses it.
    wndproc = WNDPROC(_window_proc)

    wc = WNDCLASSW()
    wc.style = CS_HREDRAW | CS_VREDRAW
    wc.lpfnWndProc = wndproc
    wc.hInstance = instance
    wc.hCursor = user32.LoadCursorW(None, ctypes.c_void_p(32512))
    wc.hbrBackground = _brush
    wc.lpszClassName = _class_name

    if not user32.RegisterClassW(ctypes.byref(wc)):
        gdi32.DeleteObject(_brush)
        _brush = None
        raise ctypes.WinError(ctypes.get_last_error())

    _hwnd = user32.CreateWindowExW(
        0,
        _class_name,
        _title,
        WS_OVERLAPPEDWINDOW,
        100,
        100,
        _width,
        _height,
        None,
        None,
        instance,
        None,
    )

    if not _hwnd:
        error = ctypes.get_last_error()
        gdi32.DeleteObject(_brush)
        _brush = None
        raise ctypes.WinError(error)

    user32.ShowWindow(_hwnd, SW_SHOW)
    user32.UpdateWindow(_hwnd)

    msg = MSG()

    try:
        while True:
            result = user32.GetMessageW(
                ctypes.byref(msg), None, 0, 0
            )

            if result == 0:
                break

            if result == -1:
                raise ctypes.WinError(ctypes.get_last_error())

            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
    finally:
        gdi32.DeleteObject(_brush)
        _brush = None
        _hwnd = None
