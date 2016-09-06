from hashlib  import sha1
from .typemap import TypeName, extract_type_system, make_type_map

import ctypes
import numpy as np
import os


class StructureGenerator(object):
    def __init__(self):
        self.c_names = initial_c_names()

        self.c_definitions = dict(self.c_names)
        self.numpy_definitions = initial_numpy_definitions()
        self.ctypes_definitions = initial_ctypes_definitions()

        self.pending_renames = set()
        self.heights = { }


    def rename(self, type_descriptor, name):
        self.pending_renames.add((type_descriptor, name))


    def get_c_name(self, type_descriptor):
        if isinstance(type_descriptor, str):
            return type_descriptor

        if self.pending_renames:
            self.execute_pending_renames()

        c_name = self.c_names.get(type_descriptor)

        if c_name is not None:
            return c_name

        hash = sha1()

        for name, field in self.extract_subfields(type_descriptor):
            hash.update(name.encode('utf-8'))
            hash.update(b'\0')
            hash.update(self.get_c_name(field).encode('utf-8'))
            hash.update(b'\0')

        c_name = 'struct_{}'.format(hash.hexdigest())
        self.c_names[type_descriptor] = c_name

        return c_name


    def get_c_definition(self, type_descriptor):
        c_definition = self.c_definitions.get(type_descriptor)

        if c_definition is not None:
            return c_definition

        c_definition = tuple(
            (name, self.get_c_name(field))
            for name, field in self.extract_subfields(type_descriptor)
        )

        self.c_definitions[type_descriptor] = c_definition

        return c_definition


    def get_numpy_definition(self, type_descriptor):
        numpy_definition = self.numpy_definitions.get(type_descriptor)

        if numpy_definition is not None:
            return numpy_definition

        if isinstance(type_descriptor, np.dtype):
            self.numpy_definitions[type_descriptor] = type_descriptor
            return type_descriptor

        numpy_definition = np.dtype(
            [
                (name, self.get_numpy_definition(field))
                for name, field in self.extract_subfields(type_descriptor)
            ],
            align = True
        )

        self.numpy_definitions[type_descriptor] = numpy_definition

        return numpy_definition


    def get_ctypes_definition(self, type_descriptor):
        ctypes_definition = self.ctypes_definitions.get(type_descriptor)

        if ctypes_definition is not None:
            return ctypes_definition

        ctypes_definition = type(
            '',
            ( ctypes.Structure, ),
            {
                'type_descriptor' : type_descriptor,
                '_fields_' :  [
                    (name, self.get_ctypes_definition(field))
                    for name, field in self.extract_subfields(type_descriptor)
                ]
            }
        )

        self.ctypes_definitions[type_descriptor] = ctypes_definition

        return ctypes_definition


    def extract_subfields(self, type_descriptor):
        type_system = extract_type_system(type_descriptor)

        if type_system == 'numpy':
            if not isinstance(type_descriptor, np.dtype):
                type_descriptor = self.numpy_definitions.get(type_descriptor)

            names = getattr(type_descriptor, 'names', None)

            if names:
                fields = type_descriptor.fields
                return ((name, fields[name][0]) for name in names)

        elif type_system == 'ctypes':
            try:
                if not issubclass(type_descriptor, ctypes.Structure):
                    type_descriptor = self.ctypes_definitions.get(type_descriptor)
            except TypeError:
                pass

            try:
                if issubclass(type_descriptor, ctypes.Structure):
                    return type_descriptor._fields_
            except TypeError:
                pass

        elif type_system == 'C':
            fields = self.c_definitions[type_descriptor]

            if isinstance(fields, tuple):
                return fields


    def render_structures(self, type_descriptor):
        from jinja2 import Environment, PackageLoader

        loader = PackageLoader('phillip', os.path.join('data', 'templates'))
        env = Environment(loader=loader)

        template = env.get_template('render_structure.cpp')

        subtypes = [ ]
        self.visit_subtypes(type_descriptor, subtypes.append)

        subtypes = [ t for t in reversed(subtypes) if self.extract_subfields(t) ] 

        return [
            template.render(c_name = self.get_c_name(t), fields = self.get_c_definition(t))
            for t in subtypes
        ]

    def visit_subtypes(self, type_descriptor, f):
        f(type_descriptor)

        fields = self.extract_subfields(type_descriptor)

        if fields is None:
            return

        for name, field in fields:
            self.visit_subtypes(field, f)


    def execute_pending_renames(self):
        renames = sorted(self.pending_renames, key = lambda p: self.get_height(p[0]))
        self.pending_renames.clear()

        for type_descriptor, name in renames:
            if type_descriptor in self.c_names:
                raise RuntimeError('Trying to rename already named type', { 'name' : name, 'type_descriptor' : type_descriptor })

            numpy_td = self.get_numpy_definition(type_descriptor)
            ctypes_td = self.get_ctypes_definition(type_descriptor)

            if numpy_td in self.c_names:
                raise RuntimeError('Trying to rename already named type', { 'name' : name, 'type_system' : 'numpy' })

            if ctypes_td in self.c_names:
                raise RuntimeError('Trying to rename already named type', { 'name' : name, 'type_system' : 'ctypes' })

            self.c_names[type_descriptor] = name
            self.c_names[numpy_td] = name
            self.c_names[ctypes_td] = name


    def get_height(self, type_descriptor):
        height = self.heights.get(type_descriptor)

        if height is not None:
            return height
        
        fields = self.extract_subfields(type_descriptor)

        if fields is None:
            height = 0
        else:
            height = max(self.get_height(field) for field in fields) + 1

        self.heights[type_descriptor] = height

        return height


def initial_c_names():
    out = {
        s : t.type_name
        for s, t in make_type_map('C').items()
    }

    out[None]  = 'void'
    out[bool]  = out[np.bool_]
    out[int]   = out[np.int_]
    out[float] = out[np.float_]

    return out


def initial_numpy_definitions():
    out = {
        s : np.dtype(getattr(np, t.type_name))
        for s, t in make_type_map('numpy').items()
    }

    out[bool]  = out[np.bool_]
    out[int]   = out[np.int_]
    out[float] = out[np.float_]

    return out


def initial_ctypes_definitions():
    out = {
        s : getattr(ctypes, t.type_name)
        for s, t in make_type_map('ctypes').items()
    }

    out[bool]  = out[np.bool_]
    out[int]   = out[np.int_]
    out[float] = out[np.float_]

    return out
