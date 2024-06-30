import ctypes
from functools import cached_property

from .util import cache

from pathlib import Path

FILE = Path(__file__).resolve().absolute()
HERE = FILE.parent


c_ubyte_p = ctypes.POINTER(ctypes.c_ubyte)

class CTypesByteArray(ctypes.Structure):
    _fields_ = [
        ("data", c_ubyte_p),
        ("size", ctypes.c_int),
    ]


class ByteArray:
    data: bytearray
    size: int

    def __init__(self, data):
        if not isinstance(data, bytearray):
            data = bytearray(data)

        self.data = data
        self.size = len(data)


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


@cache
def byte_array_module_generator():
    from .module_generator import Function, Variable,  ModuleGenerator

    mg = ModuleGenerator('"byte_array.hpp"')

    mg.add_structure(CTypesByteArray, 'ByteArray')
    mg.add_header('<stdlib.h>')

    size = Variable('size', int, None, False)

    alloc = mg.add_function(
        'byte_array_alloc_', bytearray, [ size ],
        r'''
            ByteArray out;

            out.data = (unsigned char*)malloc(size);
            out.size = size;

            return out;
        '''
    )

    alloc_interface = alloc.generate_default_interface('byte_array_alloc')

    mg.add_interface(alloc_interface)

    byte_array = Variable('byte_array', bytearray, None, False)

    free = mg.add_function(
        'byte_array_free_', None, [byte_array],
        r'''
            free(byte_array.data);
        '''
    )

    free_interface = free.generate_default_interface('byte_array_free')

    mg.add_interface(free_interface)

    return mg


@cache
def byte_array_lib():
    import ctypes
    from .build import build_so, generate_extension_args

    directory = HERE / 'generated/byte_array'
    directory.mkdir(parents=True, exist_ok=True)

    mg = byte_array_module_generator()

    header_path = directory / 'byte_array.hpp'

    if not header_path.exists() or True:
        header_path.write_text(mg.render_header(), 'utf-8')

    source_path = directory / 'byte_array.cpp'

    if not source_path.exists() or True:
        source_path.write_text(mg.render_module(), 'utf-8')

    extension_arguments = generate_extension_args()
    extension_arguments['export_symbols'].extend(f.name for f in mg.interfaces)

    sources = [ source_path ]

    so_path = build_so(
        'phillip.c_byte_array',
        str(directory), [ str(p) for p in sources ],
        extension_arguments
    )

    lib = ctypes.cdll.LoadLibrary(so_path)

    return lib


@cache
def byte_array_module():
    import ctypes

    mg = byte_array_module_generator()
    lib = byte_array_lib()

    return mg.generate(lib)
