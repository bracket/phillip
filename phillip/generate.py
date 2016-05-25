from collections import namedtuple
import itertools
import operator
import os
import re

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

def make_replace_grammar():
    g = { }

    g['indent']      = r'(?P<indent>\s*)'
    g['replace_key'] = r'(?P<replace_key>[a-zA-Z_][a-zA-Z0-9_]*)'
    g['replace']     = r'{g[indent]}{{{g[replace_key]}}}'.format(g=g)

    for k, r in g.items():
        g[k] = re.compile(r)

    return g

replace_re = make_replace_grammar()['replace']

def transform_lines(lines, replacement_map, replace_re=replace_re):
    def replace_line(line):
        m = replace_re.match(line)

        if not m:
            return line
        else:
            groups = m.groupdict()

            indent = groups.get('indent', '')
            replace_key = groups['replace_key']

            return IndentLines(indent, replacement_map[replace_key])

    return map(replace_line, lines)

