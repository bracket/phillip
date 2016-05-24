import itertools
import operator
import os
import re
from collections import namedtuple

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

def make_replace_grammar():
    g = { }

    g['indent']     = r'(?P<indent>\s*)'
    g['identifier'] = r'(?P<identifier>[a-zA-Z_][a-zA-Z0-9_]*)'
    g['replace']    = r'{g[indent]}{{{g[identifier]}}}'.format(g=g)

    for k, r in g.items():
        g[k] = re.compile(r)

    return g

replace_re = make_replace_grammar()['replace']

def render_indents(lines, indent=None, fd=None):
    nl = os.linesep

    if fd is None:
        import io
        fd = io.StringIO()

    if indent is None:
        indent = ''

    for line in lines:
        if isinstance(line, str):
            fd.write(indent)
            fd.write(line)
            fd.write(nl)
        elif isinstance(line, IndentLines):
            render_indents(line.lines, indent + line.indent, fd)
        else:
            render_indents(line, indent + '    ', fd)

    return fd.getvalue()
