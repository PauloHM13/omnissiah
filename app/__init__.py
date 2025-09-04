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

def create_app():
    app = Flask(__name__, template_folder="templates")
    app.config.from_object(Config())
    os.makedirs(app.config["EXPENSES_UPLOAD_DIR"], exist_ok=True)  # <- garante pasta
    init_db(app.config["DB_CFG"])

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_users_bp, url_prefix="/admin")
    app.register_blueprint(admin_hospitals_bp, url_prefix="/admin")
    app.register_blueprint(admin_procedures_bp, url_prefix="/admin")
    app.register_blueprint(doctor_production_bp, url_prefix="/doctor")
    app.register_blueprint(admin_productions_bp, url_prefix="/admin")
    app.register_blueprint(doctor_expenses_bp, url_prefix="/doctor")
    app.register_blueprint(admin_expenses_bp,  url_prefix="/admin")

    return app
