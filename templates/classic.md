# {{ full_name }}

**{{ headline }}**

{{ email }} | {{ phone }} | {{ location }}
[LinkedIn]({{ linkedin }}) | [GitHub]({{ github }}) | [{{ website }}]({{ website }})

---

{% if summary %}
## Summary

{{ summary }}
{% endif %}

{% if experiences %}
## Experience

{% for exp in experiences %}
### {{ exp.title }} — *{{ exp.company }}*{% if exp.location %}, {{ exp.location }}{% endif %}
*{{ exp.start_date }} – {{ exp.end_date }}*

{% for h in exp.highlights %}
- {{ h }}
{% endfor %}
{% if exp.tech %}
*Tech:* {{ exp.tech | join(', ') }}
{% endif %}

{% endfor %}
{% endif %}

{% if education %}
## Education

{% for ed in education %}
**{{ ed.degree }}** — *{{ ed.institution }}*{% if ed.location %}, {{ ed.location }}{% endif %}
*{{ ed.start_date }} – {{ ed.end_date }}*{% if ed.notes %}
{{ ed.notes }}{% endif %}

{% endfor %}
{% endif %}

{% if skills %}
## Skills

{% for group in skills %}
- **{{ group.category }}:** {{ group['items'] | join(', ') }}
{% endfor %}
{% endif %}

{% if projects %}
## Projects

{% for p in projects %}
- **{{ p.name }}**{% if p.url %} — [link]({{ p.url }}){% endif %}: {{ p.description }}{% if p.tech %} *(Tech: {{ p.tech | join(', ') }})*{% endif %}
{% endfor %}
{% endif %}

{% if certifications %}
## Certifications

{% for c in certifications %}
- **{{ c.name }}** — {{ c.issuer }}{% if c.date %} ({{ c.date }}){% endif %}{% if c.url %} — [credential]({{ c.url }}){% endif %}
{% endfor %}
{% endif %}

{% if languages %}
## Languages

{% for l in languages %}{{ l.name }} ({{ l.level }}){% if not loop.last %} • {% endif %}{% endfor %}
{% endif %}
