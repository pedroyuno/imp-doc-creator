{% extends "base_document.md" %}

{% block test_cases -%}

| `ID` | Provider | Payment Method | Description | Passed | Date | Executer | Evidence |
|----|----------|----------------|-------------|--------|------|----------|----------|
{%- for test_case in test_cases_data %}
| `{{ test_case.id }}` | {{ test_case.provider }} | {{ test_case.payment_method }} | {{ test_case.description }} | {{ test_case.passed }} | {{ test_case.date }} | {{ test_case.executer }} | {{ test_case.evidence }} |
{%- endfor %}

{% endblock %}