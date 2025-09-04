# app/blueprints/admin_users.py
from flask import Blueprint, render_template, request, redirect, url_for, session, abort, flash
import secrets, string
from ..services.user_service import UserService
from ..services.hospital_service import HospitalService

bp = Blueprint("admin_users", __name__)
svc = UserService()
hsvc = HospitalService()  # listar hospitais no formulário

def _admin_required() -> bool:
    return bool(session.get("user_id")) and session.get("role") == "admin"

@bp.before_request
def guard():
    # Protege tudo que estiver nesse blueprint
    if not _admin_required():
        abort(403)

@bp.route("/users")
def list_users():
    users = svc.list_users()
    return render_template("admin/users_list.html", users=users)

@bp.route("/users/new", methods=["GET", "POST"])
def new_user():
    msg = None
    error = None
    hospitals = hsvc.list("")  # lista completa para checkboxes
    doc_hospital_ids = []      # novo usuário ainda não tem vínculos

    if request.method == "POST":
        role = request.form.get("role")
        username = (request.form.get("username") or "").strip().lower()
        email = (request.form.get("email") or "").strip().lower()

        if role not in ("admin", "doctor") or not username or "@" not in email:
            error = "Preencha papel, usuário e e-mail válido."
        else:
            temp_password = _gen_password()
            payload = {
                "role": role,
                "username": username,
                "email": email,
                "password": temp_password,
                # contato/endereço
                "phone": (request.form.get("phone") or "").strip(),
                "cep": (request.form.get("cep") or "").strip(),
                "street": (request.form.get("street") or "").strip(),
                "number": (request.form.get("number") or "").strip(),
                "complement": (request.form.get("complement") or "").strip(),
                "district": (request.form.get("district") or "").strip(),
                "city": (request.form.get("city") or "").strip(),
                "state": (request.form.get("state") or "").strip().upper(),
                # médico
                "full_name": (request.form.get("full_name") or "").strip(),
                "crm": (request.form.get("crm") or "").strip(),
                "rqe": (request.form.get("rqe") or "").strip(),
                "cpf": (request.form.get("cpf") or "").strip(),
                "rg":  (request.form.get("rg")  or "").strip(),
                "specialty": (request.form.get("specialty") or "").strip(),
            }
            try:
                uid, tmp = svc.create_user(payload)
                # vínculos hospitalares (somente se for médico)
                if role == "doctor":
                    ids = request.form.getlist("hospital_ids")  # ["1","3",...]
                    sel_ids = [int(x) for x in ids if x.isdigit()]
                    svc.set_doctor_hospitals(uid, sel_ids)
                    doc_hospital_ids = sel_ids  # para refletir na tela após criação
                msg = f"Usuário criado: {username} | Senha provisória: {tmp}"
            except Exception as e:
                error = f"Erro: {e}"

    return render_template(
        "admin/user_form.html",
        mode="new",
        msg=msg,
        error=error,
        user={},                # garante que 'user' existe no template
        doc={},                 # idem para 'doc'
        hospitals=hospitals,    # lista para checkboxes
        doc_hospital_ids=doc_hospital_ids,
    )

@bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
def edit_user(user_id: int):
    # carrega usuário e (se for médico) dados do médico
    user = svc.users.by_id(user_id)
    if not user:
        abort(404)
    doc = svc.docs.get(user_id) if user["role"] == "doctor" else None

    hospitals = hsvc.list("")  # para montar os checkboxes
    selected_ids = svc.doctor_hospital_ids(user_id) if user["role"] == "doctor" else []

    msg = None
    error = None
    if request.method == "POST":
        role = request.form.get("role")
        username = (request.form.get("username") or "").strip().lower()
        email = (request.form.get("email") or "").strip().lower()
        is_active = True if request.form.get("is_active") == "on" else False

        fields = {
            "role": role,
            "username": username,
            "email": email,
            "is_active": is_active,
            # contato/endereço
            "phone": (request.form.get("phone") or "").strip(),
            "cep": (request.form.get("cep") or "").strip(),
            "street": (request.form.get("street") or "").strip(),
            "number": (request.form.get("number") or "").strip(),
            "complement": (request.form.get("complement") or "").strip(),
            "district": (request.form.get("district") or "").strip(),
            "city": (request.form.get("city") or "").strip(),
            "state": (request.form.get("state") or "").strip().upper(),
            # médico
            "full_name": (request.form.get("full_name") or "").strip(),
            "crm": (request.form.get("crm") or "").strip(),
            "rqe": (request.form.get("rqe") or "").strip(),
            "cpf": (request.form.get("cpf") or "").strip(),
            "rg":  (request.form.get("rg")  or "").strip(),
            "specialty": (request.form.get("specialty") or "").strip(),
        }

        if role not in ("admin", "doctor") or not username or "@" not in email:
            error = "Preencha papel, usuário e e-mail válido."
        else:
            try:
                svc.update_user(user_id, fields)

                # atualizar vínculos conforme papel atual
                if role == "doctor":
                    ids = request.form.getlist("hospital_ids")
                    sel_ids = [int(x) for x in ids if x.isdigit()]
                    svc.set_doctor_hospitals(user_id, sel_ids)
                    selected_ids = sel_ids
                else:
                    # se deixou de ser médico, limpa vínculos
                    svc.set_doctor_hospitals(user_id, [])
                    selected_ids = []

                msg = "Usuário atualizado."
                user = svc.users.by_id(user_id)
                doc = svc.docs.get(user_id) if user["role"] == "doctor" else None
            except Exception as e:
                error = f"Erro: {e}"

    return render_template(
        "admin/user_form.html",
        mode="edit",
        user=user,
        doc=doc,
        msg=msg,
        error=error,
        hospitals=hospitals,
        doc_hospital_ids=selected_ids,
    )

@bp.route("/users/<int:user_id>/delete", methods=["POST"])
def delete_user(user_id: int):
    ok = svc.delete_user(user_id)
    flash("Usuário excluído." if ok else "Usuário não encontrado.", "ok" if ok else "error")
    return redirect(url_for("admin_users.list_users"))

@bp.route("/users/<int:user_id>/reset", methods=["POST"])
def reset_user(user_id: int):
    new_pass = _gen_password()
    username = svc.reset_password(user_id, new_pass)
    if not username:
        flash("Usuário não encontrado.", "error")
    else:
        flash(f"Senha provisória de {username}: {new_pass}", "ok")
    return redirect(url_for("admin_users.list_users"))

def _gen_password(n: int = 10) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(n))
