# app/blueprints/admin_procedures.py
from flask import Blueprint, render_template, request, redirect, url_for, session, abort, flash
from ..services.procedure_service import ProcedureService

bp = Blueprint("admin_procedures", __name__)
svc = ProcedureService()


# ------- helpers -------
def _admin_required() -> bool:
    return bool(session.get("user_id")) and session.get("role") == "admin"


def _money(s: str | None) -> str | None:
    """Normaliza valor monetário aceitando '123,45' ou '123.45'.
    Retorna None para vazio (o repo faz NULLIF/::numeric)."""
    if s is None:
        return None
    s = s.strip()
    if not s:
        return None
    return s.replace(",", ".")


@bp.before_request
def guard():
    if not _admin_required():
        abort(403)


# ------- rotas -------
@bp.route("/procedures")
def list_procedures():
    q = request.args.get("q", "")
    procs = svc.list(q)
    return render_template("admin/procedures_list.html", procedures=procs, q=q)


@bp.route("/procedures/new", methods=["GET", "POST"])
def new_procedure():
    error = msg = None

    if request.method == "POST":
        try:
            payload = {
                "tuss_code": (request.form.get("tuss_code") or "").strip(),
                "name": (request.form.get("name") or "").strip(),
                "charge_unit": (request.form.get("charge_unit") or "").strip(),
                "grp": (request.form.get("grp") or "").strip(),
                "internal_code": (request.form.get("internal_code") or "").strip(),
                "active": True,
                # Valor SUS (referência) — opcional
                "valor_sus": _money(request.form.get("valor_sus")),
            }
            pid = svc.create(payload)
            flash("Procedimento criado.", "ok")
            return redirect(url_for("admin_procedures.edit_procedure", procedure_id=pid))
        except Exception as e:
            error = f"Erro: {e}"

    # IMPORTANTE: enviar 'procedure' (não 'proc') para o template
    return render_template(
        "admin/procedure_form.html",
        mode="new",
        procedure={},  # estrutura vazia para o form
        error=error,
        msg=msg,
    )


@bp.route("/procedures/<int:procedure_id>/edit", methods=["GET", "POST"])
def edit_procedure(procedure_id: int):
    proc = svc.by_id(procedure_id)
    if not proc:
        abort(404)

    error = msg = None

    if request.method == "POST":
        try:
            payload = {
                "tuss_code": (request.form.get("tuss_code") or "").strip(),
                "name": (request.form.get("name") or "").strip(),
                "charge_unit": (request.form.get("charge_unit") or "").strip(),
                "grp": (request.form.get("grp") or "").strip(),
                "internal_code": (request.form.get("internal_code") or "").strip(),
                "active": True if request.form.get("active") == "on" else False,
                # Valor SUS (referência) — opcional
                "valor_sus": _money(request.form.get("valor_sus")),
            }
            svc.update(procedure_id, payload)
            msg = "Procedimento atualizado."
            proc = svc.by_id(procedure_id)  # recarrega atualizado
        except Exception as e:
            error = f"Erro: {e}"

    return render_template(
        "admin/procedure_form.html",
        mode="edit",
        procedure=proc,  # <- nome alinhado com o template
        error=error,
        msg=msg,
    )


@bp.route("/procedures/<int:procedure_id>/delete", methods=["POST"])
def delete_procedure(procedure_id: int):
    ok = svc.delete(procedure_id)
    flash("Procedimento excluído." if ok else "Não encontrado.", "ok" if ok else "error")
    return redirect(url_for("admin_procedures.list_procedures"))
