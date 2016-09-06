import numpy as np
import os

def test_generate_module(tmpdir):
    from phillip.module_generator import Function, ModuleGenerator, Variable
    from phillip.build import build_so

    position_type = np.dtype([
        ('x', np.float32),
        ('y', np.float32),
        ('z', np.float32),
        ('w', np.float32),
    ], align = True)

    color_type = np.dtype([
        ('R', np.float32),
        ('G', np.float32),
        ('B', np.float32),
        ('A', np.float32),
    ], align = True)

    vertex_type = np.dtype([
        ('position', position_type),
        ('color', color_type)
    ], align = True)

    generator = ModuleGenerator()

    headers = [ '<vector>', '<cmath>' ]
    generator.headers.extend(headers)

    generator.add_structure(position_type, 'Position')
    generator.add_structure(color_type, 'Color')
    generator.add_structure(vertex_type, 'Vertex')


    variables = [
        Variable('black', color_type, '{ 0., 0., 0., 1. }', True),
        Variable('white', 'Color', '{ 1., 1., 1., 1. }', True),
        Variable('shader_time', 'float', 0., False),
    ]

    generator.variables.extend(variables)

    generator.functions.append(
        Function(
            generator.structure_generator,
            'sample_texture',
            color_type,
            [
                Variable('mesh', vertex_type, None, None),
                Variable('s', 'float', None, None),
                Variable('t', 'float', None, None),
            ],
            'return black;'
        )
    )

    generator.interfaces.extend(
        function.generate_default_interface()
        for function in generator.functions
    )

    source = generator.render_module()
    source_path = os.path.join(str(tmpdir), 'test_module.cpp')

    with open(source_path, 'w') as fd:
        fd.write(source)

    so_path = build_so('__test__.build', str(tmpdir), [ source_path ])
