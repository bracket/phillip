{%- for header in headers %}
#include {{ header }}
{%- endfor %}

{% for structure in structures -%}
{{ structure }}

{% endfor -%}

{% for variable in variable_declarations %}
{{ variable }}
{%- endfor %}

{% for function in functions %}
{{ function }}
{% endfor %}

extern "C" {
{%- for interface in interfaces %}
{{ interface }}
{% endfor %}
}
