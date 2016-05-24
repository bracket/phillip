import os

def build_so(module_name, target_dir, sources, extension_args={ }, setup_args=None):
    from distutils.dist import Distribution
    from distutils.errors import DistutilsArgError
    from distutils.extension import Extension
    from shutil import copy2

    setup_args = generate_setup_args(setup_args)

    dist = Distribution(setup_args)

    ext = Extension(
        name = module_name,
        sources = sources,
        **extension_args
    )

    if dist.ext_modules is None:
        dist.ext_modules = [ ext ]
    else:
        dist.ext_modules.append(ext)

    build = dist.get_command_obj('build')
    build.build_base = os.path.join(target_dir, 'build')

    cfgfiles = dist.find_config_files()
    dist.parse_config_files(cfgfiles)

    try:
        ok = dist.parse_command_line()
    except DistutilsArgError:
        raise

    if not ok:
        raise RuntimeError('Build cannot continue')

    command = dist.get_command_obj("build_ext")
    dist.run_commands()

    so_path = os.path.abspath(command.get_outputs()[0])
    _, so_name = os.path.split(so_path)

    target_path = os.path.join(target_dir, so_name)

    if os.path.isfile(target_path):
        os.unlink(target_path)
    
    copy2(so_path, target_path)

    return target_path


def generate_setup_args(setup_args=None):
    setup_args = { } if setup_args is None else dict(setup_args)

    script_args = setup_args.get('script_args')

    if script_args is None:
        script_args = [ ]

    args = [ "--quiet", "build_ext" ]

    setup_args['script_name'] = None
    setup_args['script_args'] = args + script_args

    return setup_args
