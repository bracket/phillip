import os
from phillip.build import *


def test_build(tmpdir):
    import ctypes

    source = r'''
        int test_function() {
            return 51;
        }
    '''

    source_path = os.path.join(str(tmpdir), 'main.c')

    with open(source_path, 'w') as out:
        out.write(source)

    extension_args = generate_extension_args([ 'test_function' ])

    so_path = build_so('__test__.build', str(tmpdir), [ source_path ], extension_args)

    lib = load_library(so_path)

    test = lib['test_function']
    test.restype = ctypes.c_int

    value = test()

    assert value == 51


def test_type_info():
    from phillip.typemap import get_c_type_info, get_ctypes_type_info, get_numpy_type_info

    getters = (get_c_type_info, get_ctypes_type_info, get_numpy_type_info)

    for getter in getters:
        type_info = getter()

        assert isinstance(type_info, dict)
        assert len(type_info) > 0
        assert all(i.size > 0 for i in type_info.values())


def test_typemap():
    from phillip.typemap import make_type_map, TypeName

    tm = make_type_map('C')

    assert isinstance(tm, dict)
    assert all(isinstance(t, TypeName) and t.type_system == 'C' for t in tm.values())


def test_render_numpy_structure(tmpdir):
    import numpy as np
    from phillip.structure_generator import StructureGenerator

    inner_type = np.dtype([
            ('weasel', np.int),
            ('beaver', np.int)
        ],
        align=True
    )

    outer_type = np.dtype([
            ('monkey', np.int32),
            ('inner', inner_type),
        ],
        align = True
    )

    generator = StructureGenerator()
    generator.rename(outer_type, 'outer_type')

    source = '\n\n'.join(generator.render_structures(outer_type))
    source_path = os.path.join(str(tmpdir), 'test_render_numpy_structure.cpp')

    with open(source_path, 'w') as out:
        out.write(source)

    extension_args = generate_extension_args()

    so_path = build_so('__test__.build', str(tmpdir), [ source_path ], extension_args)


def test_render_ctypes_structure(tmpdir):
    import ctypes
    from phillip.structure_generator import StructureGenerator

    class InnerType(ctypes.Structure):
        _fields_ = [
            ('weasel', ctypes.c_int64),
            ('beaver', ctypes.c_int64),
        ]


    class OuterType(ctypes.Structure):
        _fields_ = [
            ('monkey', ctypes.c_int64),
            ('inner',  InnerType)
        ]

    generator = StructureGenerator()
    generator.rename(OuterType, 'outer_type')

    type_descriptor = generator.get_ctypes_definition(OuterType)
    assert type_descriptor is not OuterType
    assert generator.get_c_name(type_descriptor) == generator.get_c_name(OuterType)

    source = '\n\n'.join(generator.render_structures(type_descriptor))
    source_path = os.path.join(str(tmpdir), 'test_render_ctypes_structure.cpp')

    with open(source_path, 'w') as fd:
        fd.write(source)

    extension_args = generate_extension_args()

    so_path = build_so('__test__.build', str(tmpdir), [ source_path ], extension_args)
