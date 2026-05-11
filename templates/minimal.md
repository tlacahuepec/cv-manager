{{ full_name }}
{{ headline }}

{{ email }} | {{ phone }} | {{ location }}
{{ linkedin }}
{{ github }}
{{ website }}

{% if summary %}
SUMMARY

{{ summary }}
{% endif %}

{% if experiences %}
EXPERIENCE

{% for exp in experiences %}
{{ exp.title }}
{{ exp.company }}{% if exp.location %}, {{ exp.location }}{% endif %}
{{ exp.start_date }} - {{ exp.end_date }}

{% for h in exp.highlights %}
- {{ h }}
{% endfor %}
{% if exp.tech %}
Technologies: {{ exp.tech | join(', ') }}
{% endif %}

{% endfor %}
{% endif %}

{% if education %}
EDUCATION

{% for ed in education %}
{{ ed.degree }}
{{ ed.institution }}{% if ed.location %}, {{ ed.location }}{% endif %}
{{ ed.start_date }} - {{ ed.end_date }}
{% if ed.notes %}
{{ ed.notes }}
{% endif %}

{% endfor %}
{% endif %}

{% if skills %}
SKILLS

{% for group in skills %}
{{ group.category }}: {{ group['items'] | join(', ') }}
{% endfor %}
{% endif %}

{% if projects %}
PROJECTS

{% for p in projects %}
{{ p.name }}{% if p.url %} ({{ p.url }}){% endif %}
{{ p.description }}
{% if p.tech %}
Technologies: {{ p.tech | join(', ') }}
{% endif %}

{% endfor %}
{% endif %}

{% if certifications %}
CERTIFICATIONS

{% for c in certifications %}
- {{ c.name }} - {{ c.issuer }}{% if c.date %} ({{ c.date }}){% endif %}
{% endfor %}
{% endif %}

{% if languages %}
LANGUAGES

{% for l in languages %}
{{ l.name }}: {{ l.level }}
{% endfor %}
{% endif %}
