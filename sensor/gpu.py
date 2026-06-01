import ctypes

_lib = None
_handle = None

def _init():
    global _lib, _handle
    lib = ctypes.CDLL("libnvidia-ml.so")
    lib.nvmlInit_v2()
    handle = ctypes.c_void_p()
    lib.nvmlDeviceGetHandleByIndex_v2(0, ctypes.byref(handle))
    _lib = lib
    _handle = handle

def get_gpu_temp():
    global _lib, _handle
    try:
        if _lib is None:
            _init()
        temp = ctypes.c_uint()
        _lib.nvmlDeviceGetTemperature(_handle, 0, ctypes.byref(temp))
        return float(temp.value)
    except Exception:
        _lib = None
        return None
