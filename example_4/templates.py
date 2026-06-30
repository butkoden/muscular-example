from pathlib import Path
from string import Template
import html

TEMPLATE_DIR = Path(__file__).resolve().parent / "templates"
_TEMPLATE_CACHE = {}


def escape(value):
    # RU: Экранируем пользовательские значения перед вставкой в HTML.
    # EN: Escape user-provided values before inserting them into HTML.
    return html.escape(str(value), quote=True)


def render(template_name, **context):
    # RU: string.Template выбран специально: меньше магии для учебного примера.
    # EN: string.Template is intentional here: less magic for a learning example.
    template = _TEMPLATE_CACHE.get(template_name)
    if template is None:
        # RU: Кешируем шаблоны после первого чтения с диска.
        # EN: Cache templates after the first disk read.
        template = Template((TEMPLATE_DIR / template_name).read_text(encoding="utf-8"))
        _TEMPLATE_CACHE[template_name] = template
    safe_context = {key: value for key, value in context.items()}
    return template.safe_substitute(safe_context)


def page(title, body, active="home"):
    # RU: Общая layout-функция держит навигацию в одном месте.
    # EN: A shared layout helper keeps navigation state in one place.
    nav = {
        "home": "",
        "resume": "",
        "admin": "",
    }
    nav[active] = "active"
    return render("layout.html", title=escape(title), body=body, **nav)
