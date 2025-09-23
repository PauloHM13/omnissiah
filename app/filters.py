# app/filters.py
from datetime import date, datetime

def brdate(value):
    """Formata datas no padrão dd/mm/aaaa.
    Aceita date/datetime ou string 'YYYY-MM-DD'."""
    if not value:
        return ""
    if isinstance(value, (date, datetime)):
        return value.strftime("%d/%m/%Y")
    s = str(value)[:10]  # protege contra 'YYYY-MM-DD...' ou None
    try:
        y, m, d = s.split("-")
        return f"{d}/{m}/{y}"
    except ValueError:
        return s

def register_filters(app):
    app.jinja_env.filters["brdate"] = brdate
