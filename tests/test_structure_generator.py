from phillip.structure_generator import StructureGenerator
from phillip.typemap import TypeName

import ctypes

def test_extract_pointee():
    generator = StructureGenerator()

    test_values = [
        (TypeName('C', 'Vertex *'), TypeName('C', 'Vertex')),
        (ctypes.POINTER(ctypes.c_int), ctypes.c_int),
    ]

    for value, expected in test_values:
        assert generator.extract_pointee(value) == expected
