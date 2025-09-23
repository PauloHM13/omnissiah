# app/blueprints/auth.py
from flask import Blueprint, render_template, request, session, redirect, url_for, abort, flash

from ..services.user_service import UserService
from ..services.analytics_service import AnalyticsService
from ..services.hospital_service import HospitalService
from ..services.procedure_service import ProcedureService

from datetime import datetime
from datetime import timezone

bp = Blueprint("auth", __name__)

# Serviços
svc = UserService()
analytics = AnalyticsService()
hsvc = HospitalService()
usvc = UserService()
psvc = ProcedureService()


@bp.route("/")
def index():
    return redirect(
        url_for("auth.dashboard") if session.get("user_id") else url_for("auth.login")
    )


@bp.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        user = svc.authenticate(
            request.form.get("username", ""),
            request.form.get("password", ""),
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
            if user.get("must_change_password"):
                # força a tela de troca de senha no primeiro acesso
                return redirect(url_for("auth.change_password", force=1))
            return redirect(url_for("auth.dashboard"))
    return render_template("auth/login.html", error=error)


@bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))

@bp.route("/privacy")
def privacy():
    return render_template("legal/privacy.html")

@bp.route("/privacy/internal")
def privacy_internal():
    return render_template("legal/internal_notice.html")


@bp.route("/dashboard")
def dashboard():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    role = session.get("role")
    user = session.get("username")

    if role == "admin":
        # ---- Filtros vindos por GET (opcionais) ----
        date_from = request.args.get("date_from") or ""
        date_to = request.args.get("date_to") or ""

        def _to_int(v: str | None):
            return int(v) if v and v.isdigit() else None

        sel_hospital = _to_int(request.args.get("hospital_id"))
        sel_doctor = _to_int(request.args.get("doctor_id"))
        sel_procedure = _to_int(request.args.get("procedure_id"))

        # ---- Listas para os selects (preenchimento dos filtros) ----
        hospitals = hsvc.list("")                      # todos os hospitais
        users = usvc.list_users()                      # todos os usuários
        doctors = [u for u in users if u.get("role") == "doctor"]
        procedures = psvc.list(active=True)            # procedimentos ativos

        # ---- Dados de analytics (com suporte a filtros, fallback se necessário) ----
        try:
            data = analytics.dashboard_data(
                date_from=date_from or None,
                date_to=date_to or None,
                hospital_id=sel_hospital,
                doctor_user_id=sel_doctor,
                procedure_id=sel_procedure,
            )
        except TypeError:
            # Caso sua AnalyticsService ainda não aceite filtros, usa sem argumentos
            data = analytics.dashboard_data()

        return render_template(
            "admin/dashboard.html",
            user=user,
            **data,
            # contexto para os filtros
            hospitals=hospitals,
            doctors=doctors,
            procedures=procedures,
            sel_hospital=sel_hospital,
            sel_doctor=sel_doctor,
            sel_procedure=sel_procedure,
            date_from=date_from,
            date_to=date_to,
        )

    if role == "doctor":
        # Dashboard específico do médico (somente quantidades)
        doc = svc.docs.get(session["user_id"])  # usa o mesmo repo já usado no admin_users
        doctor_name = (doc.get("full_name") if doc else None) or user

        data = analytics.doctor_dashboard_data(session["user_id"])
        return render_template("doctor/dashboard.html", user=user, doctor_name=doctor_name, **data)

    abort(403)


@bp.route("/profile/password", methods=["GET", "POST"])
def change_password():
    if not session.get("user_id"):
        return redirect(url_for("auth.login"))

    user_id = session["user_id"]
    must = svc.user_must_change(user_id)  # flag de primeiro acesso
    user = svc.users.by_id(user_id)  # pegue o registro p/ saber se já aceitou
    privacy_accepted_at = user.get("privacy_accepted_at") if user else None

    error = None

    if request.method == "POST":
        new1 = request.form.get("new1", "").strip()

        # checkbox veio?
        require_accept = must or (privacy_accepted_at is None)
        accepted = (request.form.get("accept_privacy") == "on")

        # fluxo primeiro acesso (não exige senha atual)
        if must:
            if require_accept and not accepted:
                error = "Você precisa aceitar a Política de Privacidade e o Aviso de Privacidade Interno."
            else:
                ok = svc.set_password(user_id, new1, clear_flag=True)
                if not ok:
                    error = "Não foi possível definir a nova senha."
                else:
                    if require_accept and accepted:
                        svc.set_privacy_accepted(user_id)
                    flash("Senha definida. Bem-vindo(a)!", "ok")
                    return redirect(url_for("auth.dashboard"))

        # fluxo normal (exige senha atual)
        else:
            if require_accept and not accepted:
                error = "Você precisa aceitar a Política de Privacidade e o Aviso de Privacidade Interno."
            else:
                cur = request.form.get("current", "").strip()
                ok = svc.change_password(user_id, cur, new1)
                if not ok:
                    error = "Senha atual incorreta."
                else:
                    if require_accept and accepted:
                        svc.set_privacy_accepted(user_id)
                    flash("Senha alterada com sucesso.", "ok")
                    return redirect(url_for("auth.dashboard"))

    return render_template(
        "profile/change_password.html",
        error=error,
        must_change=must,
        privacy_accepted_at=privacy_accepted_at,
    )
