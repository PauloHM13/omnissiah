from flask import Blueprint, render_template, request, redirect, url_for, session, abort, flash
from ..services.procedure_service import ProcedureService

def _money(s: str | None) -> str:
    # permite "123,45" ou "123.45"
    s = (s or "").strip().replace(",", ".")
    return s

bp = Blueprint("admin_procedures", __name__)
svc = ProcedureService()


def _admin_required() -> bool:
    return bool(session.get("user_id")) and session.get("role") == "admin"

@bp.before_request
def guard():
    if not _admin_required():
        abort(403)

@bp.route("/procedures")
def list_procedures():
    q = request.args.get('q','')
    procs = svc.list(q)
    return render_template("admin/procedures_list.html", procedures=procs, q=q)

@bp.route("/procedures/new", methods=["GET","POST"])
def new_procedure():
    msg = error = None
    if request.method == 'POST':
        try:
            payload = {
                'tuss_code': (request.form.get('tuss_code') or '').strip(),
                'name': (request.form.get('name') or '').strip(),
                'charge_unit': request.form.get('charge_unit'),
                'grp': (request.form.get('grp') or '').strip(),
                'internal_code': (request.form.get('internal_code') or '').strip(),
                'active': True,
                'valor_sus': _money(request.form.get('valor_sus')),  # <-- NOVO
            }
            pid = svc.create(payload)
            flash("Procedimento criado.", "ok")
            return redirect(url_for('admin_procedures.edit_procedure', procedure_id=pid))
        except Exception as e:
            error = f"Erro: {e}"
    return render_template("admin/procedure_form.html", mode='new', error=error, msg=msg, proc={})

@bp.route("/procedures/<int:procedure_id>/edit", methods=["GET","POST"])
def edit_procedure(procedure_id: int):
    proc = svc.by_id(procedure_id)
    if not proc:
        abort(404)
    msg = error = None
    if request.method == 'POST':
        try:
            payload = {
                'tuss_code': (request.form.get('tuss_code') or '').strip(),
                'name': (request.form.get('name') or '').strip(),
                'charge_unit': request.form.get('charge_unit'),
                'grp': (request.form.get('grp') or '').strip(),
                'internal_code': (request.form.get('internal_code') or '').strip(),
                'active': True if request.form.get('active') == 'on' else False,
                'valor_sus': _money(request.form.get('valor_sus')),  # <-- NOVO
            }
            svc.update(procedure_id, payload)
            msg = "Procedimento atualizado."
            proc = svc.by_id(procedure_id)
        except Exception as e:
            error = f"Erro: {e}"
    return render_template("admin/procedure_form.html", mode='edit', proc=proc, error=error, msg=msg)

@bp.route("/procedures/<int:procedure_id>/delete", methods=["POST"])
def delete_procedure(procedure_id: int):
    ok = svc.delete(procedure_id)
    flash("Procedimento excluído." if ok else "Não encontrado.", "ok" if ok else "error")
    return redirect(url_for('admin_procedures.list_procedures'))
