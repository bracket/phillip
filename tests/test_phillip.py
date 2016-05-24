import os
import phillip

def test_build(tmpdir):
    from phillip.build import build_so
    import ctypes

    source = r'''
        int test_function() {
            return 51;
        }
    '''

    source_path = os.path.join(str(tmpdir), 'main.c')

    with open(source_path, 'w') as out:
        out.write(source)

    so_path = build_so('__test__.build', str(tmpdir), [ source_path ])

    lib = ctypes.cdll.LoadLibrary(so_path)

    test = lib['test_function']
    test.restype = ctypes.c_int

    value = test()

    assert value == 51


def test_clean_lines():
    from phillip.generate import split_and_dedent_lines

    text = r'''
        if (weasel == beaver) {
            /* do stuff */
        }
    '''

    actual = split_and_dedent_lines(text)

    expected = [
        'if (weasel == beaver) {',
        '    /* do stuff */',
        '}'
    ]

    assert actual == expected
