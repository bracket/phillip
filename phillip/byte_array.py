import ctypes
from functools import cached_property

c_ubyte_p = ctypes.POINTER(ctypes.c_ubyte)

class CTypesByteArray(ctypes.Structure):
    _fields_ = [
        ("data", c_ubyte_p),
        ("length", ctypes.c_int),
    ]


class ByteArray:
    data: bytearray
    length: int

    def __init__(self, data):
        if not isinstance(data, bytearray):
            data = bytearray(data)

        self.data = data
        self.length = len(data)

        
    @cached_property
    def ctypes_buffer(self):
        ctypes_type = ctypes.c_ubyte * 1
        return ctypes_type.from_buffer(self.data)


    @cached_property
    def ctypes_pointer(self):
        return c_ubyte_p(self.ctypes_buffer)


    @cached_property
    def ctypes_instance(self):
        return CTypesByteArray(
            self.ctypes_pointer,
            len(self.data)
        )
