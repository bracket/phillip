struct {{ c_name }} {
{%- for name, type  in fields %}
    {{ type }} {{ name }};
{%- endfor %}
};
