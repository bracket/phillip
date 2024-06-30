from pprint import pprint
import ctypes

from phillip.byte_array import *
from phillip.structure_generator import *
from phillip.build import *


def test_pass_byte_array(tmpdir):
    source = r'''
        #include <stdio.h>

        typedef struct {
            unsigned char * data;
            int size;
        } ByteArray;

        int test_function(ByteArray s) {
            char const * expected = "weasel";
            int matching = 0;

            for (; matching < s.size; ++matching) {
                if (s.data[matching] != expected[matching])
                    { break; }
            }

            return matching;
        }
    '''


    source_path = tmpdir / 'main.c'
    source_path.write_text(source, 'utf-8')

    extension_args = generate_extension_args([ 'test_function' ])

    so_path = build_so('__test__.build', str(tmpdir), [ str(source_path) ], extension_args)

    lib = load_library(so_path)

    array = ByteArray(b'weasel')

    test = lib['test_function']
    test.argtypes = [ CTypesByteArray ]
    test.restype = ctypes.c_int

    value = test(array.ctypes_instance)

    assert value == 6


def test_byte_array_module(tmpdir):
    from phillip.byte_array import byte_array_module

    module = byte_array_module()

    array = module['byte_array_alloc'](7)
    module['byte_array_free'](array)
