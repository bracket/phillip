{%- for header in headers %}
#include {{ header }}
{%- endfor %}

{%- for structure in structures %}
extern "C" {{ structure }}
{%- endfor %}


extern "C" {
{%- for interface in interfaces %}
{{ interface }}
{%- endfor %}
}
