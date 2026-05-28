from pathlib import Path
from string import Template
import html

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_TEMPLATE_CACHE = {}


def escape(value):
    return html.escape(str(value), quote=True)


def render(template_name, **context):
    template = _TEMPLATE_CACHE.get(template_name)
    if template is None:
        template = Template((TEMPLATE_DIR / template_name).read_text(encoding="utf-8"))
        _TEMPLATE_CACHE[template_name] = template
    safe_context = {key: value for key, value in context.items()}
    return template.safe_substitute(safe_context)


def page(title, body, active="home"):
    nav = {
        "home": "",
        "resume": "",
        "admin": "",
    }
    nav[active] = "active"
    return render("layout.html", title=escape(title), body=body, **nav)
