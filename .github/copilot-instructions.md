# Copilot Instructions for Phillip

## Project Overview

**Phillip** is a Python module that generates C/C++ shared libraries on the fly and compiles them for use in Python using ctypes. It serves primarily as an interop layer for the `handsome` project but has broader applicability for any Python project requiring efficient C/C++ integration.

### Key Characteristics
- **Language**: Python 3.x (with Python 2.6+ legacy support)
- **Type**: Library/Module for dynamic C/C++ code generation and compilation
- **Dependencies**: numpy, ctypes, Jinja2 (for templating), groupby, setuptools/distutils
- **Test Framework**: pytest with tmpdir fixture

---

## Architecture Overview

### Core Modules

#### 1. `phillip/typemap.py`
**Purpose**: Provides type interoperability between C/C++, numpy dtypes, and ctypes structures.

**Key Features**:
- Maps types across three type systems: C, numpy, and ctypes
- Generates sizeof determination programs on the fly to get accurate C type sizes
- Uses `RAW_TYPE_DATA_CSV` as a reference table for type information (signage, numeric_type)
- Compiles and executes temporary C programs to determine platform-specific type sizes

**Important Functions**:
- `make_type_map(target_system)`: Creates a type mapping to a target system
- `get_c_type_info()`: Dynamically determines C type sizes by compiling and running a sizeof program
- `get_numpy_type_info()`: Extracts numpy type information from dtype objects
- `get_ctypes_type_info()`: Extracts ctypes type information
- `generate_sizeof_program()`: Uses Jinja2 template to create a C program that reports type sizes

#### 2. `phillip/structure_generator.py`
**Purpose**: Generates compatible C/numpy/ctypes structures dynamically with automatic naming.

**Key Features**:
- Maintains three parallel definitions: C, numpy, and ctypes for each structure
- Auto-generates C structure names using SHA1 hashing (e.g., `struct_<hash>`)
- Supports custom naming via `rename()` method
- Handles nested structures and pointers
- Uses Jinja2 templates to render C structure definitions

**Important Classes/Methods**:
- `StructureGenerator`: Main class for structure generation
- `get_c_name(type_descriptor)`: Returns C-compatible name for a type
- `get_c_definition(type_descriptor)`: Returns C structure definition
- `get_numpy_definition(type_descriptor)`: Returns numpy dtype
- `get_ctypes_definition(type_descriptor)`: Returns ctypes.Structure subclass
- `render_structures(type_descriptor)`: Generates C code for all nested structures

#### 3. `phillip/module_generator.py`
**Purpose**: Handles C++ to Python interfacing by automatically generating extern "C" wrappers.

**Key Features**:
- Wraps C++ code with `extern "C"` blocks for ctypes compatibility
- Manages headers, structures, functions, and interfaces
- Supports both module generation (`.cpp` files) and header generation (`.hpp` files)
- Uses Jinja2 templates for code generation

**Important Classes**:
- `Function`: Represents a C++ function with signature and definition
- `ModuleGenerator`: Main class for generating complete modules
- `Variable`: Represents a variable with type and initializer

**Key Methods**:
- `add_function()`: Adds a C++ function to the module
- `add_interface()`: Adds an extern "C" interface function
- `render_module()`: Generates the complete C++ module source
- `render_header()`: Generates the corresponding header file
- `generate(lib)`: Sets up ctypes function signatures for loaded library

#### 4. `phillip/byte_array.py`
**Purpose**: Facilitates passing raw data buffers between Python and C/C++ (particularly numpy arrays).

**Key Features**:
- Provides `ByteArray` class for Python-side buffer management
- Provides `CTypesByteArray` ctypes.Structure for C-side representation
- Includes module generator for byte array allocation/deallocation functions
- Uses ctypes pointers to share memory between Python and C

**Important Classes**:
- `ByteArray`: Python wrapper with ctypes conversion properties
- `CTypesByteArray`: C-compatible structure (data pointer + size)

#### 5. `phillip/build.py`
**Purpose**: Compiles C/C++ code into shared libraries using distutils/setuptools.

**Key Features**:
- Adapted from setuptools build system
- Handles cross-platform compilation (Linux, macOS, Windows)
- Uses `LyingList` class to trick setuptools into accepting custom export symbols
- Manages library loading/unloading with platform-specific code

**Important Functions**:
- `build_so(module_name, target_dir, sources, extension_args)`: Compiles sources to shared library
- `generate_extension_args(export_symbols)`: Creates extension arguments for build
- `load_library(path)`: Loads compiled library with ctypes
- `unload_library(lib)`: Unloads library (platform-specific)

#### 6. `phillip/util.py`
**Purpose**: Utility functions, primarily caching.

**Contents**:
- `cache`: Alias for `functools.lru_cache(None)` for unlimited memoization

---

## Templates

Located in `phillip/data/templates/`, these Jinja2 templates are used for code generation:

1. **`sizeof_program.cpp`**: Template for generating C programs that report type sizes as JSON
2. **`render_structure.cpp`**: Template for rendering C struct definitions
3. **`module_template.cpp`**: Template for complete C++ modules with extern "C" interfaces
4. **`header_template.hpp`**: Template for C++ header files

---

## Build and Test Instructions

### Dependencies Installation
```bash
# Core dependencies (usually available)
pip install numpy jinja2 groupby
```

### Running Tests
The project uses **pytest** for testing:

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_phillip.py

# Run with verbose output
pytest -v tests/
```

**Test Files**:
- `tests/test_phillip.py`: Tests for build system, typemap, and structure generation
- `tests/test_module_generator.py`: Tests for module generation functionality
- `tests/test_structure_generator.py`: Tests for structure generation
- `tests/test_byte_array.py`: Tests for byte array functionality

**Note**: Tests use `tmpdir` fixture from pytest to create temporary directories for compilation artifacts.

### Building from Source
```bash
# Install in development mode
pip install -e .

# Or install normally
python setup.py install
```

### Testing Compilation
Phillip dynamically compiles C/C++ code, so you need:
- A working C/C++ compiler (gcc, clang, or MSVC)
- C++ standard library development files

**Platform-specific requirements**:
- **Linux**: `build-essential` package
- **macOS**: Xcode Command Line Tools
- **Windows**: Microsoft Visual C++ Build Tools

---

## Code Patterns and Conventions

### Type System Integration
- Always use `StructureGenerator` to manage type conversions between C/numpy/ctypes
- Use `typemap` functions to convert between type systems
- When creating new structures, use `rename()` to provide human-readable C names

### Memory Management
- Phillip uses `ctypes` for memory sharing between Python and C
- `ByteArray` handles buffer allocation and lifetime management
- Generated C code uses `malloc`/`free` - ensure proper cleanup

### Code Generation Flow
1. Create a `ModuleGenerator` instance
2. Define structures using numpy dtypes or ctypes.Structure
3. Add functions with C++ implementations
4. Generate extern "C" interfaces for Python access
5. Render module source code using templates
6. Compile to shared library using `build_so()`
7. Load library and set up ctypes signatures

### Template Usage
- All templates are Jinja2 based
- Templates are loaded using `PackageLoader('phillip', os.path.join('data', 'templates'))`
- Keep template logic minimal - complex logic belongs in Python code

---

## Common Patterns

### Creating a New Module
```python
from phillip.module_generator import ModuleGenerator, Function, Variable

mg = ModuleGenerator()
mg.add_header('<math.h>')

# Add a function
f = mg.add_function(
    name='my_function',
    return_type=float,
    arguments=[Variable('x', float, None, False)],
    definition='return sqrt(x);'
)

# Create extern "C" interface
interface = f.generate_default_interface()
mg.add_interface(interface)

# Render and compile
source = mg.render_module()
```

### Working with Structures
```python
import numpy as np
from phillip.structure_generator import StructureGenerator

sg = StructureGenerator()

# Define a numpy structure
point_type = np.dtype([
    ('x', np.float32),
    ('y', np.float32),
], align=True)

# Give it a name
sg.rename(point_type, 'Point')

# Get C name
c_name = sg.get_c_name(point_type)  # 'Point'

# Render structure definitions
structures = sg.render_structures(point_type)
```

---

## Important Notes

### File Locations
- **Source code**: `phillip/*.py`
- **Templates**: `phillip/data/templates/*.cpp` and `*.hpp`
- **Tests**: `tests/test_*.py`
- **Package metadata**: `setup.py`, `setup.cfg`, `phillip/__init__.py`

### Generated Files
- Phillip generates C/C++ source files and compiled shared libraries at runtime
- Generated files are typically placed in temporary directories or `phillip/generated/`
- The `byte_array` module is pre-generated on first import

### Platform Considerations
- Library loading differs between Linux/macOS (`ctypes.cdll`) and Windows (`ctypes.windll`)
- Library unloading is platform-specific and may not be fully implemented on all platforms
- C++ compiler flags and options are managed by distutils/setuptools

---

## Validation Steps

Before submitting changes:
1. Run the full test suite: `pytest tests/`
2. Verify that compilation works on your platform
3. Check that generated C code compiles without warnings
4. Ensure type mappings are correct across C/numpy/ctypes
5. Test with both simple and nested structure definitions

---

## Related Projects

**handsome**: The primary consumer of phillip. Handsome uses phillip for efficient C/C++ interop in its computational tasks. When making changes to phillip, consider the impact on handsome's usage patterns.
