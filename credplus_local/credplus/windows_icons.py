"""Native Windows taskbar/window icon setup, with pointer-sized icon handles."""
import ctypes
from ctypes import wintypes
import os


def application_id(version):
    return 'PropostaSeguroAuto.Segurado.v'+version.replace('.','_')


def set_application_id(version):
    if os.name!='nt':return False
    api=ctypes.WinDLL('shell32',use_last_error=True)
    fn=api.SetCurrentProcessExplicitAppUserModelID
    fn.argtypes=[wintypes.LPCWSTR];fn.restype=ctypes.c_long
    return fn(application_id(version))==0


def set_window_icons(root,icon_path,api=None):
    if os.name!='nt' and api is None:return []
    if api is None:api=ctypes.WinDLL('user32',use_last_error=True)
    ancestor=api.GetAncestor;ancestor.argtypes=[wintypes.HWND,wintypes.UINT];ancestor.restype=wintypes.HWND
    load=api.LoadImageW;load.argtypes=[wintypes.HINSTANCE,wintypes.LPCWSTR,wintypes.UINT,ctypes.c_int,ctypes.c_int,wintypes.UINT];load.restype=wintypes.HANDLE
    send=api.SendMessageW;send.argtypes=[wintypes.HWND,wintypes.UINT,wintypes.WPARAM,wintypes.LPARAM];send.restype=ctypes.c_ssize_t
    metrics=api.GetSystemMetrics;metrics.argtypes=[ctypes.c_int];metrics.restype=ctypes.c_int
    destroy=api.DestroyIcon;destroy.argtypes=[wintypes.HANDLE];destroy.restype=wintypes.BOOL
    root.update_idletasks()
    hwnd=ancestor(root.winfo_id(),2) or root.winfo_id() # GA_ROOT: Tk's native wrapper, not just its client child.
    handles=[]
    try:
        for which,xmetric,ymetric in [(0,49,50),(1,11,12)]: # ICON_SMALL/ICON_BIG and system metrics.
            handle=load(None,str(icon_path),1,metrics(xmetric),metrics(ymetric),0x10) # IMAGE_ICON, LR_LOADFROMFILE.
            if not handle:raise OSError('Não foi possível carregar o ícone da proposta no Windows.')
            handles.append(handle)
            send(hwnd,0x80,which,handle) # WM_SETICON; never destroy the borrowed previous icon returned by Windows.
    except Exception:
        for handle in handles:destroy(handle)
        raise
    return handles


def release_window_icons(handles,api=None):
    if not handles:return
    if api is None:
        if os.name!='nt':return
        api=ctypes.WinDLL('user32',use_last_error=True)
    fn=api.DestroyIcon;fn.argtypes=[wintypes.HANDLE];fn.restype=wintypes.BOOL
    for handle in handles:fn(handle)
    handles.clear()
