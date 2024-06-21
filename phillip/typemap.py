from collections import namedtuple

import ctypes
import functools
import numpy as np

memoize = functools.lru_cache(None)

TypeName = namedtuple('TypeName', 'type_system type_name')
TypeInfo = namedtuple('TypeInfo', 'signage numeric_type size')

def extract_type_system(type_descriptor):
    if isinstance(type_descriptor, TypeName):
        return type_descriptor.type_system

    module = type(type_descriptor).__module__
    module = module.split('.')[0]

    if module == 'numpy':
        return 'numpy'

    if module in ('ctypes', '_ctypes'):
        return 'ctypes'

    return 'python'


def make_type_map(target_system):
    type_systems = set(t.type_system for (t, _) in parse_raw_type_data())
    inverse_map = make_inverse_map(target_system)

    out = { }

    for source_system in type_systems:
        for t, type_info in get_type_info(source_system).items():
            out[t] = inverse_map[type_info]

    return out


#TODO: Name this better
def make_inverse_map(target_system):
    from groupby import list_groupby

    by_type_info = list_groupby(
        (type_info, t)
        for t, type_info in get_type_info(target_system).items()
        if isinstance(t, TypeName) and t.type_system == target_system
    )

    sort_order = { t : i for i, (t, _) in enumerate(parse_raw_type_data()) }

    return {
        type_info : min(types, key=sort_order.get)
        for type_info, types
        in by_type_info.items()
    }


def get_type_info(system):
    if system == 'C':
        return get_c_type_info()
    elif system == 'numpy':
        return get_numpy_type_info()
    elif system == 'ctypes':
        return get_ctypes_type_info()


@memoize
def get_c_type_info():
    from phillip.build import build_so, generate_extension_args, load_library, unload_library
    import json
    import os
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        source_path = os.path.join(str(tmpdir), 'sizeof.c')

        source = generate_sizeof_program()

        with open(source_path, 'w') as fd:
            fd.write(source)

        extension_args = generate_extension_args([ 'get_sizeofs' ])

        so_path = build_so('__test__.sizeof', str(tmpdir), [ source_path ], extension_args)
        lib = load_library(so_path)

        get_sizeofs = lib['get_sizeofs']
        get_sizeofs.restype = ctypes.c_char_p

        js = json.loads(get_sizeofs().decode('utf-8'))
        unload_library(lib)

        out = { }

        for entry in js:
            t = TypeName._make(entry[:2])
            type_info = TypeInfo._make(entry[2:])
            out[t] = type_info

        return out


@memoize
def get_numpy_type_info():
    dtype = np.dtype

    out = { }

    for t, type_info in parse_raw_type_data():
        if t.type_system != 'numpy':
            continue

        np_type = getattr(np, t.type_name, None)

        if np_type is None:
            continue

        x = np_type()

        type_info = TypeInfo(type_info.signage, type_info.numeric_type, x.itemsize)

        out[t] = type_info
        out[np_type] = type_info
        out[dtype(np_type)] = type_info

    return out


@memoize
def get_ctypes_type_info():
    from ctypes import sizeof

    out = { }

    for t,type_info in parse_raw_type_data():
        if t.type_system != 'ctypes':
            continue

        ctypes_type = getattr(ctypes, t.type_name)
        type_info = TypeInfo(type_info.signage, type_info.numeric_type, sizeof(ctypes_type))

        out[t] = type_info
        out[ctypes_type] = type_info

    return out


def generate_sizeof_program():
    from jinja2 import Environment, PackageLoader
    import os

    loader = PackageLoader('phillip', os.path.join('data', 'templates'))
    env = Environment(loader=loader)

    c_types = [ (t,p) for (t,p) in parse_raw_type_data() if t.type_system == 'C' ]

    template = env.get_template('sizeof_program.cpp')
    source = template.render(c_types=c_types)

    return source


@memoize
def parse_raw_type_data():
    rows = [ row for row in map(str.strip, RAW_TYPE_DATA_CSV.splitlines()) if row ]
    rows = [ [ field.strip() for field in row.split('|') ] for row in rows ]

    return [ (TypeName._make(row[:2]), TypeInfo._make(row[2:])) for row in rows ]


# TODO: We can probably deduce signage and numeric_type as well (for Python based types anyway)

# NOTE: Order reflects preference of type names when types are identical

RAW_TYPE_DATA_CSV = r'''
    C      | char               | signed   | integer |
    C      | float              | signed   | float   |
    C      | double             | signed   | float   |
    C      | int                | signed   | integer |
    C      | long double        | signed   | float   |
    C      | short              | signed   | integer |
    C      | long long          | signed   | integer |
    C      | unsigned char      | unsigned | integer |
    C      | unsigned int       | unsigned | integer |
    C      | unsigned long long | unsigned | integer |
    C      | unsigned short     | unsigned | integer |
    ctypes | c_int8             | signed   | integer |
    ctypes | c_int16            | signed   | integer |
    ctypes | c_int32            | signed   | integer |
    ctypes | c_int64            | signed   | integer |
    ctypes | c_uint8            | unsigned | integer |
    ctypes | c_uint16           | unsigned | integer |
    ctypes | c_uint32           | unsigned | integer |
    ctypes | c_uint64           | unsigned | integer |
    ctypes | c_float            | signed   | float   |
    ctypes | c_double           | signed   | float   |
    ctypes | c_longdouble       | signed   | float   |
    ctypes | c_bool             | unsigned | integer |
    ctypes | c_byte             | signed   | integer |
    ctypes | c_int              | signed   | integer |
    ctypes | c_long             | signed   | integer |
    ctypes | c_longlong         | signed   | integer |
    ctypes | c_short            | signed   | integer |
    ctypes | c_size_t           | unsigned | integer |
    ctypes | c_ssize_t          | signed   | integer |
    ctypes | c_ubyte            | unsigned | integer |
    ctypes | c_uint             | unsigned | integer |
    ctypes | c_ulong            | unsigned | integer |
    ctypes | c_ulonglong        | unsigned | integer |
    ctypes | c_ushort           | unsigned | integer |
    numpy  | int8               | signed   | integer |
    numpy  | int16              | signed   | integer |
    numpy  | int32              | signed   | integer |
    numpy  | int64              | signed   | integer |
    numpy  | float32            | signed   | float   |
    numpy  | float64            | signed   | float   |
    numpy  | float128           | signed   | float   |
    numpy  | uint8              | unsigned | integer |
    numpy  | uint16             | unsigned | integer |
    numpy  | uint32             | unsigned | integer |
    numpy  | uint64             | unsigned | integer |
    numpy  | bool_              | unsigned | integer |
    numpy  | byte               | signed   | integer |
    numpy  | double             | signed   | float   |
    numpy  | float_             | signed   | float   |
    numpy  | int_               | signed   | integer |
    numpy  | intc               | signed   | integer |
    numpy  | longfloat          | signed   | float   |
    numpy  | longlong           | signed   | integer |
    numpy  | short              | signed   | integer |
    numpy  | single             | signed   | float   |
    numpy  | ubyte              | unsigned | integer |
    numpy  | uint               | unsigned | integer |
    numpy  | uintc              | unsigned | integer |
    numpy  | ulonglong          | unsigned | integer |
    numpy  | ushort             | unsigned | integer |
'''

#    C  | void * | unsigned | pointer |
# numpy | intp   | unsigned | pointer |
# numpy | uintp  | unsigned | pointer |
