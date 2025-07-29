{% extends "base_document.md" %}

{% block test_cases -%}
{% for env_name in ['sandbox', 'production'] -%}
{%- set env_test_cases = env_test_cases_data[env_name] -%}
{%- if env_test_cases %}

## {{ env_name.title() }} Environment Test Cases

Test cases specifically for the {{ env_name }} environment.

| `ID` | Provider | Payment Method | Description | Passed | Date | Executer | Evidence |
|----|----------|----------------|-------------|--------|------|----------|----------|
{%- for test_case in env_test_cases %}
| `{{ test_case.id }}` | {{ test_case.provider }} | {{ test_case.payment_method }} | {{ test_case.description }} | {{ test_case.passed }} | {{ test_case.date }} | {{ test_case.executer }} | {{ test_case.evidence }} |
{%- endfor %}

{% endif -%}
{% endfor -%}
{% endblock %}