# app/blueprints/auth.py
from flask import Blueprint, render_template, request, session, redirect, url_for, abort, flash
from ..services.user_service import UserService

bp = Blueprint("auth", __name__)
svc = UserService()

@bp.route("/")
def index():
    return redirect(url_for("auth.dashboard") if session.get("user_id") else url_for("auth.login"))

@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user = svc.authenticate(
            request.form.get("username", ""),
            request.form.get("password", "")
        )
        if not user:
            error = "Usuário ou senha inválidos."
        elif not user["is_active"]:
            error = "Usuário inativo."
        else:
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            session["role"] = user["role"]
            if user["must_change_password"]:
                return redirect(url_for("auth.change_password"))
            return redirect(url_for("auth.dashboard"))
    return render_template("auth/login.html", error=error)

@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

@bp.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))
    role = session.get("role")
    user = session.get("username")
    if role == "admin":
        return render_template("admin/dashboard.html", user=user)
    if role == "doctor":
        return render_template("doctor/dashboard.html", user=user)
    abort(403)

@bp.route("/profile/password", methods=["GET", "POST"])
def change_password():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    error = None
    if request.method == "POST":
        ok = svc.change_password(
            session["user_id"],
            request.form.get("current", ""),
            request.form.get("new1", "")
        )
        if not ok:
            error = "Senha atual incorreta."
        else:
            flash("Senha alterada com sucesso.", "ok")
            return redirect(url_for("auth.dashboard"))

    return render_template("profile/change_password.html", error=error)
