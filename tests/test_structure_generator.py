from pprint import pprint
from phillip.structure_generator import StructureGenerator
from phillip.typemap import TypeName

import ctypes

def test_extract_pointee():
    generator = StructureGenerator()

    test_values = [
        (TypeName('C', 'Vertex *'),    TypeName('C', 'Vertex')),
        (ctypes.POINTER(ctypes.c_int), ctypes.c_int),
    ]

    for value, expected in test_values:
        assert generator.extract_pointee(value) == expected


def test_annotations():
    class User:
        user_id: int
        name:    str

    generator = StructureGenerator()

    generator.rename(User, 'User')

    assert generator.get_c_name(User) == 'User'

    expected = { 'user_id' : 'long long', 'name' : 'ByteArray' }
    assert dict(generator.get_c_definition(User)) == expected
