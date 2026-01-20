# Phillip

**Phillip** is a Python library for generating and compiling C/C++ shared libraries on-the-fly for seamless integration with Python via ctypes. It provides a powerful interoperability layer between Python, C/C++, NumPy, and ctypes, enabling high-performance computing directly from Python.

## Overview

Phillip dynamically generates C/C++ code, compiles it into shared libraries, and loads them for use in Python—all at runtime. Originally developed as an interop layer for the [handsome](https://github.com/bracket/handsome) project, Phillip has broader applicability for any Python project requiring efficient C/C++ integration.

### Key Features

- **🔄 Cross-Type System Mapping**: Automatic type conversion between C, NumPy dtypes, and ctypes
- **🏗️ Dynamic Structure Generation**: Create compatible C/NumPy/ctypes structures with automatic C naming
- **🔌 Automatic Interface Generation**: Wrap C++ code with `extern "C"` interfaces for Python accessibility
- **📦 On-the-Fly Compilation**: Generate, compile, and load C/C++ libraries without manual build steps
- **💾 Zero-Copy Buffer Sharing**: Efficiently pass NumPy arrays and raw data between Python and C/C++
- **🎯 Platform-Aware Type Sizing**: Determine actual C type sizes dynamically for your platform

## Installation

### Requirements

- Python 3.3+ (Python 2.6+ legacy support available)
- NumPy
- Jinja2 (for code generation templates)
- groupby
- A C/C++ compiler:
  - **Linux**: gcc/g++ (install via `build-essential`)
  - **macOS**: clang/clang++ (install via Xcode Command Line Tools)
  - **Windows**: Microsoft Visual C++ Build Tools

### Install from Source

```bash
git clone https://github.com/bracket/phillip.git
cd phillip
pip install -e .
```

Or install dependencies manually:

```bash
pip install numpy jinja2 groupby
```

## Quick Start

Here's a simple example of generating a C function and calling it from Python:

```python
import numpy as np
from phillip.module_generator import ModuleGenerator, Function, Variable
from phillip.build import build_so, generate_extension_args
import ctypes

# Create a module generator
mg = ModuleGenerator()
mg.add_header('<math.h>')

# Define a C++ function
x = Variable('x', float, None, False)
sqrt_func = mg.add_function(
    name='my_sqrt',
    return_type=float,
    arguments=[x],
    definition='return sqrt(x);'
)

# Create an extern "C" interface for Python
interface = sqrt_func.generate_default_interface('c_my_sqrt')
mg.add_interface(interface)

# Generate and compile the module
import tempfile
import os

with tempfile.TemporaryDirectory() as tmpdir:
    source_path = os.path.join(tmpdir, 'module.cpp')
    with open(source_path, 'w') as f:
        f.write(mg.render_module())
    
    extension_args = generate_extension_args()
    extension_args['export_symbols'].extend([iface.name for iface in mg.interfaces])
    
    so_path = build_so('my_module', tmpdir, [source_path], extension_args)
    
    # Load and use the library
    lib = ctypes.cdll.LoadLibrary(so_path)
    c_my_sqrt = lib.c_my_sqrt
    c_my_sqrt.restype = ctypes.c_double
    c_my_sqrt.argtypes = [ctypes.c_double]
    
    result = c_my_sqrt(16.0)
    print(f"Square root of 16: {result}")  # Output: 4.0
```

## Architecture

Phillip consists of several integrated modules that work together to provide seamless C/C++ interop:

### Core Components

#### 1. Type Mapping (`typemap.py`)

The type mapping system provides automatic conversion between three type systems:

- **C types** (`int`, `float`, `double`, etc.)
- **NumPy dtypes** (`np.int32`, `np.float64`, etc.)
- **ctypes types** (`c_int`, `c_float`, etc.)

Phillip determines actual C type sizes by generating and compiling small C programs on-the-fly, ensuring correct type mapping for your specific platform.

**Example:**

```python
from phillip.typemap import make_type_map

# Get mappings from any type system to C
type_map = make_type_map('C')
print(type_map[np.int32])  # TypeName(type_system='C', type_name='int')
```

#### 2. Structure Generator (`structure_generator.py`)

Generates compatible structure definitions across C, NumPy, and ctypes simultaneously. Handles nested structures, pointers, and provides automatic C-compatible naming.

**Example:**

```python
import numpy as np
from phillip.structure_generator import StructureGenerator

sg = StructureGenerator()

# Define a NumPy structure
vec3_type = np.dtype([
    ('x', np.float32),
    ('y', np.float32),
    ('z', np.float32),
], align=True)

# Name it for C compatibility
sg.rename(vec3_type, 'Vec3')

# Get corresponding definitions
c_name = sg.get_c_name(vec3_type)           # 'Vec3'
numpy_def = sg.get_numpy_definition(vec3_type)  # numpy.dtype
ctypes_def = sg.get_ctypes_definition(vec3_type)  # ctypes.Structure subclass

# Generate C code
c_code = '\n\n'.join(sg.render_structures(vec3_type))
print(c_code)
# Output:
# struct Vec3 {
#     float x;
#     float y;
#     float z;
# };
```

#### 3. Module Generator (`module_generator.py`)

Creates complete C++ modules with automatic `extern "C"` wrapper generation for Python interoperability.

**Example:**

```python
from phillip.module_generator import ModuleGenerator, Function, Variable

mg = ModuleGenerator()
mg.add_header('<stdio.h>')

# Define a structure
point_type = np.dtype([('x', np.float32), ('y', np.float32)], align=True)
mg.add_structure(point_type, 'Point')

# Add a function
p = Variable('p', point_type, None, False)
print_point = mg.add_function(
    name='print_point',
    return_type=None,
    arguments=[p],
    definition='printf("Point(%f, %f)\\n", p.x, p.y);'
)

# Create interface
interface = print_point.generate_default_interface()
mg.add_interface(interface)

# Render complete module
print(mg.render_module())
```

#### 4. Byte Array (`byte_array.py`)

Facilitates zero-copy data exchange between Python and C/C++, particularly useful for NumPy arrays.

**Example:**

```python
from phillip.byte_array import ByteArray

# Create a buffer
data = bytearray(b"Hello, C!")
ba = ByteArray(data)

# Get ctypes representation for passing to C
ctypes_obj = ba.ctypes_instance
# ctypes_obj.data is a pointer, ctypes_obj.size is the length
```

#### 5. Build System (`build.py`)

Compiles C/C++ source files into shared libraries using Python's distutils/setuptools infrastructure.

**Example:**

```python
from phillip.build import build_so, generate_extension_args

sources = ['my_module.cpp']
extension_args = generate_extension_args(['my_function'])

so_path = build_so(
    module_name='my_module',
    target_dir='/tmp',
    sources=sources,
    extension_args=extension_args
)

# so_path now points to the compiled shared library
```

## Usage Examples

### Example 1: Working with NumPy Structures

```python
import numpy as np
from phillip.structure_generator import StructureGenerator
from phillip.module_generator import ModuleGenerator, Variable
from phillip.build import build_so, generate_extension_args
import tempfile
import ctypes

# Define a color structure
color_type = np.dtype([
    ('r', np.uint8),
    ('g', np.uint8),
    ('b', np.uint8),
    ('a', np.uint8),
], align=True)

# Create module generator
mg = ModuleGenerator()
mg.add_structure(color_type, 'Color')

# Add a function to manipulate colors
c = Variable('c', color_type, None, False)
invert_color = mg.add_function(
    name='invert_color',
    return_type=color_type,
    arguments=[c],
    definition='''
        Color result;
        result.r = 255 - c.r;
        result.g = 255 - c.g;
        result.b = 255 - c.b;
        result.a = c.a;
        return result;
    '''
)

interface = invert_color.generate_default_interface()
mg.add_interface(interface)

# Compile and load
with tempfile.TemporaryDirectory() as tmpdir:
    # ... (compilation code as in Quick Start)
    pass
```

### Example 2: Type Mapping Between Systems

```python
import numpy as np
import ctypes
from phillip.typemap import make_type_map

# Create a mapping from any type to ctypes
ctypes_map = make_type_map('ctypes')

# Convert NumPy type to ctypes
print(ctypes_map[np.int32])      # TypeName for c_int32
print(ctypes_map[np.float64])    # TypeName for c_double

# Works with actual type objects too
c_map = make_type_map('C')
print(c_map[ctypes.c_int])       # TypeName for 'int' in C
```

### Example 3: Nested Structures

```python
import numpy as np
from phillip.structure_generator import StructureGenerator

sg = StructureGenerator()

# Define nested structures
vec2_type = np.dtype([('x', np.float32), ('y', np.float32)], align=True)
rect_type = np.dtype([
    ('position', vec2_type),
    ('size', vec2_type),
], align=True)

sg.rename(vec2_type, 'Vec2')
sg.rename(rect_type, 'Rect')

# Generate C code for all nested structures
structures = sg.render_structures(rect_type)
for struct_code in structures:
    print(struct_code)
# Output:
# struct Vec2 {
#     float x;
#     float y;
# };
#
# struct Rect {
#     Vec2 position;
#     Vec2 size;
# };
```

## How It Works

1. **Type Discovery**: Phillip compiles and runs small C programs to determine actual type sizes on your platform
2. **Code Generation**: Using Jinja2 templates, it generates C/C++ source code with proper structure definitions and extern "C" interfaces
3. **Compilation**: The build system uses Python's distutils to compile the generated code into a shared library
4. **Loading**: The library is loaded using ctypes, and function signatures are automatically configured
5. **Invocation**: Python code can now call the C/C++ functions directly with automatic type marshaling

## Relationship to Handsome

Phillip was originally developed as an interoperability layer for the **handsome** project, which requires high-performance C/C++ code generation and execution. While Phillip can be used standalone, it was designed with handsome's needs in mind:

- **Performance**: Zero-copy data transfer for large NumPy arrays
- **Flexibility**: Dynamic code generation allows handsome to adapt to different computational requirements
- **Type Safety**: Automatic type mapping ensures correct data representation across language boundaries

## Testing

Phillip uses pytest for testing:

```bash
# Run all tests
pytest tests/

# Run specific test
pytest tests/test_phillip.py -v

# Run tests with compilation output
pytest tests/ -s
```

Tests include:
- Type mapping verification
- Structure generation and compilation
- Module generation
- Cross-platform build testing
- ByteArray functionality

## Contributing

Contributions are welcome! When contributing:

1. Ensure all tests pass: `pytest tests/`
2. Verify cross-platform compatibility when possible
3. Add tests for new functionality
4. Follow existing code style and patterns

## License

[Check the LICENSE file in the repository]

## Author

Stephen [Bracket] McCray (mcbracket@gmail.com)

## Version

Current version: 0.1.0 (Beta)

---

**Note**: This project is in beta. APIs may change between versions.
