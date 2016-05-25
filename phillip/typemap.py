from collections import namedtuple
import functools

memoize = functools.lru_cache()

CType = namedtuple('CType', 'c_type signage numeric_type size')
NumpyType = namedtuple('NumpyType', 'numpy_type signage numeric_type size')

canonical_numpy_type_names = {
    'float32', 'float64', 'float128',
    'int8', 'int16', 'int32', 'int64',
    'intp',
    'uint8', 'uint16', 'uint32', 'uint64',
}

@memoize
def get_c_type_info():
    from phillip.build import build_so
    import ctypes
    import json
    import os
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        source = generate_sizeof_program()
        source_path = os.path.join(str(tmpdir), 'sizeof.c')

        with open(source_path, 'w') as out:
            out.write(source)

        so_path = build_so('__test__.sizeof', str(tmpdir), [ source_path ])
        lib = ctypes.cdll.LoadLibrary(so_path)

        get_sizeofs = lib['get_sizeofs']
        get_sizeofs.restype = ctypes.c_char_p

        js = json.loads(get_sizeofs().decode('utf-8'))

        return { t.c_type : t for t in map(CType._make, js) }


@memoize
def get_numpy_type_info():
    import numpy as np

    numpy_types = get_raw_numpy_types()

    known_sizes = {
        getattr(np, t.numpy_type) : t.size 
        for t in numpy_types
        if t.size is not None
    }

    def get_size(np_type):
        size = known_sizes.get(np_type, None)

        if size is not None:
            return size

        x = np_type()
        return x.itemsize

    return {
        r.numpy_type
            : NumpyType(
                r.numpy_type, r.signage, r.numeric_type,
                get_size(getattr(np, r.numpy_type))
            )
        for r in numpy_types
    }


def numpy_to_ctype():
    c_type_map = {
        (t.signage, t.numeric_type, t.size) : t.c_type
        for t in get_c_type_info().values()
    }

    return {
        t.numpy_type : c_type_map[(t.signage, t.numeric_type, t.size)]
        for t in get_numpy_type_info().values()
    }


def ctype_to_numpy():
    numpy_map = {
        (t.signage, t.numeric_type, t.size) : t.numpy_type
        for t in get_numpy_type_info().values()
        if t.numpy_type in canonical_numpy_type_names
    }

    return {
        t.c_type : numpy_map[(t.signage, t.numeric_type, t.size)]
        for t in get_c_type_info().values()
    }


def generate_sizeof_program():
    from phillip.generate import split_and_dedent_lines, render_indents, IndentLines, replace_re

    c_types = get_raw_c_types()

    source = split_and_dedent_lines(r'''
        #include <stdio.h>
        #include <string.h>

        char const * get_sizeofs() {
            char buffer[8192];
            char * out = buffer;

            out += sprintf(out, "[\n");

            {SIZEOF_STATEMENTS}

            out += sprintf(out, "]\n");

            return strdup(buffer);
        }
    ''')

    sizeof_template = (
        r'out += sprintf(out, "'
        + r'    [ \"{type_name}\", \"{signage}\", \"{numeric_type}\", %lu ]{comma}'
        + r'\n", sizeof({type_name}));'
    )

    last_index = len(c_types) - 1

    def format_sizeof(p):
        i, c_type = p
        comma = ',' if i < last_index else ''

        return sizeof_template.format(
            type_name=c_type.c_type, signage=c_type.signage,
            numeric_type=c_type.numeric_type, comma=comma
        )

    replace_map = {
        'SIZEOF_STATEMENTS' : 
            [ format_sizeof(p) for p in enumerate(sorted(c_types)) ]
    }

    def replace_line(line):
        m = replace_re.match(line)
        if not m:
            return line
        else:
            indent, identifier = map(m.group, ('indent', 'identifier'))
            return IndentLines(indent, replace_map[identifier])

    return render_indents(map(replace_line, source))


@memoize
def get_raw_c_types():
    c_types_csv = r'''
        char               | signed   | integer |
        double             | signed   | float   |
        float              | signed   | float   |
        int                | signed   | integer |
        long double        | signed   | float   |
        long long          | signed   | integer |
        short              | signed   | integer |
        unsigned char      | unsigned | integer |
        unsigned int       | unsigned | integer |
        unsigned long long | unsigned | integer |
        unsigned short     | unsigned | integer |
        void *             | unsigned | pointer |
    '''

    rows = [ row for row in map(str.strip, c_types_csv.splitlines()) if row ]
    rows = [ CType._make(map(str.strip, row.split('|'))) for row in rows ]

    return rows


@memoize
def get_raw_numpy_types():
    numpy_types_csv = r'''
        bool_     | unsigned | integer | 
        bool8     | unsigned | integer | 1
        byte      | signed   | integer | 
        short     | signed   | integer | 
        intc      | signed   | integer | 
        int_      | signed   | integer | 
        longlong  | signed   | integer | 
        intp      | unsigned | pointer | 
        int8      | signed   | integer | 1
        int16     | signed   | integer | 2
        int32     | signed   | integer | 4
        int64     | signed   | integer | 8
        ubyte     | unsigned | integer | 
        ushort    | unsigned | integer | 
        uintc     | unsigned | integer | 
        uint      | unsigned | integer | 
        ulonglong | unsigned | integer | 
        uintp     | unsigned | pointer | 
        uint8     | unsigned | integer | 1
        uint16    | unsigned | integer | 2
        uint32    | unsigned | integer | 4
        uint64    | unsigned | integer | 8
        single    | signed   | float   | 
        double    | signed   | float   | 
        float_    | signed   | float   | 
        longfloat | signed   | float   | 
        float32   | signed   | float   | 4
        float64   | signed   | float   | 8
        float128  | signed   | float   | 16
    '''

    def make_numpy_type(row):
        numpy_type, signage, numeric_type, size = map(str.strip, row.split('|'))

        return NumpyType(
            numpy_type, signage,
            numeric_type, int(size) if size else None
        )

    rows = [ row for row in map(str.strip, numpy_types_csv.splitlines()) if row ]
    rows = [ make_numpy_type(row) for row in rows ]

    return rows


# ctypes       | c_type             | python
# c_bool       | bool               | bool
# c_char       | char               | str
# c_wchar      | wchar_t            | str
# c_byte       | char               | int
# c_ubyte      | unsigned char      | int
# c_short      | short              | int
# c_ushort     | unsigned short     | int
# c_int        | int                | int
# c_uint       | unsigned int       | int
# c_long       | long               | int
# c_ulong      | unsigned long      | int
# c_longlong   | long long          | int
# c_ulonglong  | unsigned long long | int
# c_float      | float              | float
# c_double     | double             | float
# c_longdouble | long double        | float
# c_char_p     | char *             | bytes
# c_wchar_p    | wchar_t *          | str
# c_void_p     | void *             | int or None
