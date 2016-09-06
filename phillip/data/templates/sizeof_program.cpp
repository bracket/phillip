#include <stdio.h>
#include <string.h>

char const * get_sizeofs() {
    char buffer[16384];
    char * out = buffer;


    out += sprintf(out, "[\n");

    {% for t, i in c_types -%}
    out += sprintf(out,
        "[ \"{{t.type_system}}\", \"{{t.type_name}}\", \"{{i.signage}}\", \"{{i.numeric_type}}\", %lu ]{{ '' if loop.last else ',' }}",
        sizeof({{t.type_name}})
    );

    {% endfor -%}
    out += sprintf(out, "]\n");

    return strdup(buffer);
}
