# app/__init__.py
from flask import Flask
from .config import Config
from .db import init_db
from .blueprints.auth import bp as auth_bp
from .blueprints.admin_users import bp as admin_users_bp
from .blueprints.admin_hospitals import bp as admin_hospitals_bp
from .blueprints.admin_procedures import bp as admin_procedures_bp
from .blueprints.doctor_production import bp as doctor_production_bp
from .blueprints.admin_productions import bp as admin_productions_bp
from .blueprints.doctor_expenses import bp as doctor_expenses_bp
from .blueprints.admin_expenses  import bp as admin_expenses_bp
import os
from datetime import datetime, date

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config())
    os.makedirs(app.config["EXPENSES_UPLOAD_DIR"], exist_ok=True)
    init_db(app.config["DB_CFG"])

    @app.context_processor
    def inject_globals():
        return {"current_year": datetime.now().year}

    # --------- Filtros Jinja: datas em dd/mm/aaaa ---------
    def _br_date(value):
        """Aceita date/datetime ou string 'YYYY-MM-DD' e devolve 'dd/mm/aaaa'."""
        if value is None:
            return ""
        try:
            if isinstance(value, (datetime, date)):
                d = value.date() if isinstance(value, datetime) else value
            else:
                # tenta ISO 'YYYY-MM-DD' ou 'YYYY-MM-DD HH:MM:SS'
                s = str(value)
                try:
                    d = datetime.fromisoformat(s).date()
                except Exception:
                    y, m, d_ = s[:10].split("-")
                    return f"{d_}/{m}/{y}"
            return f"{d.day:02d}/{d.month:02d}/{d.year}"
        except Exception:
            return str(value)

    def _br_datetime(value):
        """Aceita datetime/string ISO e devolve 'dd/mm/aaaa HH:MM'."""
        if value is None:
            return ""
        try:
            if isinstance(value, datetime):
                dt = value
            else:
                dt = datetime.fromisoformat(str(value))
            return f"{dt.day:02d}/{dt.month:02d}/{dt.year} {dt.hour:02d}:{dt.minute:02d}"
        except Exception:
            return str(value)

    app.jinja_env.filters["br_date"] = _br_date
    app.jinja_env.filters["br_datetime"] = _br_datetime
    # ------------------------------------------------------

    # Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_users_bp, url_prefix="/admin")
    app.register_blueprint(admin_hospitals_bp, url_prefix="/admin")
    app.register_blueprint(admin_procedures_bp, url_prefix="/admin")
    app.register_blueprint(doctor_production_bp, url_prefix="/doctor")
    app.register_blueprint(admin_productions_bp, url_prefix="/admin")
    app.register_blueprint(doctor_expenses_bp, url_prefix="/doctor")
    app.register_blueprint(admin_expenses_bp,  url_prefix="/admin")
    return app
