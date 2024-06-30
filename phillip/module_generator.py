from .structure_generator import StructureGenerator
from collections import namedtuple

import io
import itertools
import operator
import os
import re

Variable = namedtuple('Variable', 'name type initializer is_constant')

class Function(object):
    def __init__(self, structure_generator = None, name = '', return_type = None, arguments = None, definition = ''):
        if structure_generator is None:
            self.structure_generator = StructureGenerator()
        else:
            self.structure_generator = structure_generator

        self.name = name
        self.return_type = return_type
        self.arguments = [ ]

        if arguments:
            self.arguments.extend(arguments)

        if isinstance(definition, str):
            self.definition = split_and_dedent_lines(definition)
        else:
            self.definition = definition


    def render_arguments(self, with_names=True, with_types=True):
        templates = [ ]

        if with_types:
            templates.append('{type}')

        if with_names:
            templates.append('{name}')

        template = ' '.join(templates)

        variables = [
            template.format(
                type = self.structure_generator.get_c_name(variable.type),
                name = variable.name
            )
            for variable in self.arguments
        ]

        return ', '.join(variables)


    def render_signature(self, with_names=True, with_types=True):
        templates = [ ]

        if with_types:
            templates.append('{type}')

        if with_names:
            templates.append('{name}')

        template =  ' '.join(templates) + '({arguments})'

        return template.format(
            type = self.structure_generator.get_c_name(self.return_type),
            name = self.name,
            arguments = self.render_arguments(with_names, with_types),
        )


    def render_definition(self):
        fd = io.StringIO()
        render_indents(fd, self.definition, indent='    ')

        return '{signature} {{\n{definition}}}'.format(
            signature = self.render_signature(),
            definition = fd.getvalue()
        )


    def generate_default_interface(self, name=None):
        if name is None:
            name = 'c_' + self.name

        definition = 'return {call};'.format(
            call = self.render_signature(with_names=True, with_types=False)
        )

        return Function(
            structure_generator = self.structure_generator,
            name = name,
            return_type = self.return_type,
            arguments = self.arguments,
            definition = definition
        )


Header = namedtuple('Header', 'name module_only')

class ModuleGenerator(object):
    def __init__(self, header_name = None):
        self.header_name = header_name

        self.headers = { }
        self.structures = [ ]
        self.variables = [ ]
        self.functions = [ ]
        self.interfaces = [ ]


        self.structure_generator = StructureGenerator()


    def add_variable(self, variable):
        self.variables.append(variable)


    def add_structure(self, type_definition, type_name = None):
        self.structures.append(type_definition)

        if type_name is not None:
            self.structure_generator.rename(type_definition, type_name)


    def add_header(self, name, module_only = True):
        header = Header(name, module_only)
        self.headers[header.name] = header


    def make_function(self, name = '', return_type = None, arguments = None, definition = ''):
        if isinstance(name, Function):
            return name

        f = Function(
            self.structure_generator,
            name, return_type, arguments, definition
        )

        return f


    def add_function(self, name = '', return_type = None, arguments = None, definition = ''):
        f = self.make_function(name, return_type, arguments, definition)
        self.functions.append(f)

        return f


    def add_interface(self, interface):
        self.interfaces.append(interface)


    def render_module(self):
        from jinja2 import Environment, PackageLoader

        loader = PackageLoader('phillip', os.path.join('data', 'templates'))
        env = Environment(loader = loader)

        template = env.get_template('module_template.cpp')

        headers = [ header.name for header in self.headers.values() ]

        if self.header_name and self.header_name not in headers:
            headers = [ self.header_name ] + headers

        if self.header_name:
            structures = [ ]
        else:
            structures = self.render_structures()

        variable_declarations = [
            self.render_variable_declaration(variable)
            for variable in self.variables
        ]

        structure_generator = self.structure_generator

        functions = [
            function.render_definition()
            for function in self.functions
        ]

        interfaces = [
            interface.render_definition()
            for interface in self.interfaces
        ]

        return template.render(
            headers               = headers,
            structures            = structures,
            variable_declarations = variable_declarations,
            functions             = functions,
            interfaces            = interfaces,
        )


    def render_header(self):
        from jinja2 import Environment, PackageLoader

        loader = PackageLoader('phillip', os.path.join('data', 'templates'))
        env = Environment(loader = loader)

        template = env.get_template('header_template.hpp')

        headers = [
            header.name
            for header in self.headers.values()
            if not header.module_only
        ]

        structures = self.render_structures()

        interfaces = [
            '{};'.format(interface.render_signature())
            for interface in self.interfaces
        ]

        return template.render(
            headers    = headers,
            structures = structures,
            interfaces = interfaces,
        )


    def render_structures(self):
        structures = { }
        current_structure = 0

        for structure in self.structures:
            if isinstance(structure, str):
                if structure in structures:
                    continue

                structures[structure] = current_structure
                current_structure += 1
            else:
                for s in self.structure_generator.render_structures(structure):
                    if s in structures:
                        continue

                    structures[s] = current_structure
                    current_structure += 1

        return sorted(structures, key = structures.get)


    def render_variable_declaration(self, variable):
        if not isinstance(variable, Variable):
            return variable

        type_name = self.structure_generator.get_c_name(variable.type)

        if variable.is_constant:
            const = ' const '
        else:
            const = ' '

        if variable.initializer is None:
            init = ''
        else:
            init = ' = {}'.format(variable.initializer)

        return '{type_name}{const}{name}{init};'.format(
            type_name = type_name,
            const = const,
            name = variable.name,
            init = init
        )


    def generate(self, lib):
        sg = self.structure_generator

        out = { }

        for interface in self.interfaces:
            f = lib[interface.name]

            restype = sg.get_ctypes_definition(interface.return_type)

            argtypes = [
                sg.get_ctypes_definition(arg.type)
                for arg in interface.arguments
            ]

            f.restype = restype
            f.argtypes = argtypes

            out[interface.name] = f

        return out


space_re = re.compile(r'\s*')

def split_and_dedent_lines(text):
    lines = list(
        itertools.dropwhile(
            operator.not_,
            map(str.rstrip, text.splitlines())
        )
    )

    prefix = os.path.commonprefix([ line for line in lines if line ])
    prefix_length = space_re.match(prefix).end()

    while lines and not lines[-1]:
        lines.pop()

    return [ line[prefix_length:] for line in lines ]

IndentLines = namedtuple('IndentLines', 'indent lines')

def render_indents(fd, lines, indent=None):
    nl = os.linesep

    if indent is None:
        indent = ''

    for line in lines:
        if isinstance(line, str):
            fd.write(indent)
            fd.write(line)
            fd.write(nl)
        elif isinstance(line, IndentLines):
            render_indents(fd, line.lines, indent + line.indent)
        else:
            render_indents(fd, line, indent)
