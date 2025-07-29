# Test Cases for {{ merchant_name }}

{% if include_metadata -%}
**Generated on:** {{ generation_timestamp }}
**Language:** {{ language.upper() }}
**Environment:** {{ environment.title() }}

---

{% endif -%}
{% if integration_steps -%}
## Integration Steps

Follow these integration steps in sequential order to implement the required features for your payment integration:

{% for step in integration_steps -%}
### Step {{ step.step_number }}: {{ step.feature_name }} Implementation

**Description:** {{ step.comment }}
**Documentation:** [{{ step.documentation_url }}]({{ step.documentation_url }})

{% endfor -%}
---

{% endif -%}
## Test Case Documentation

This document contains test cases for your payment integration implementation.
Each test case should be executed to ensure proper functionality of the implemented features.

{% block test_cases %}{% endblock %}
{% if include_metadata -%}

---

## Summary

- **Total Test Cases:** {{ statistics.total_test_cases }}
- **Document Language:** {{ language.upper() }}
- **Environment Filter:** {{ environment.title() }}
{%- if environment == 'separated' %}
- **Sandbox Test Cases:** {{ statistics.sandbox_test_cases }}
- **Production Test Cases:** {{ statistics.production_test_cases }}
{%- endif %}

### Instructions
- Fill in the 'Passed' column with Yes/No after executing each test case
- Record the execution date in the 'Date' column
- Add the name of the person who executed the test in the 'Executer' column
- Provide evidence (screenshots, logs, etc.) in the 'Evidence' column

---

*This document was automatically generated from your implementation scope.*
{% endif %}