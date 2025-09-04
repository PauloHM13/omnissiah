# app/blueprints/doctor_expenses.py
from flask import (
    Blueprint, render_template, request, session, abort, flash,
    redirect, url_for, current_app, send_from_directory
)
import os
from ..services.expenses_service import ExpensesService

bp = Blueprint("doctor_expenses", __name__)
svc = ExpensesService()

def _doctor_required() -> bool:
    return bool(session.get("user_id")) and session.get("role") == "doctor"

@bp.before_request
def guard():
    if not _doctor_required():
        abort(403)

@bp.route("/expenses/new", methods=["GET"])
def form():
    uid = session["user_id"]
    dfrom = request.args.get("f_date_from", "")
    dto   = request.args.get("f_date_to", "")
    city  = request.args.get("f_city", "")
    rows  = svc.list_mine(uid, dfrom or None, dto or None, city or None)

    # carrega anexos de cada despesa
    files_map = { r["id"]: svc.files_for_expense(r["id"]) for r in rows }

    return render_template(
        "doctor/expense_form.html",
        rows=rows,
        files_map=files_map,
        f_date_from=dfrom, f_date_to=dto, f_city=city
    )

@bp.route("/expenses/new", methods=["POST"])
def submit():
    uid = session["user_id"]
    dt  = request.form.get("request_date")

    cities  = request.form.getlist("city")
    values  = request.form.getlist("amount")
    descs   = request.form.getlist("description")
    files   = request.files.getlist("receipt")

    items = []
    for i in range(len(cities)):
        if not (cities[i] or "").strip():
            continue
        items.append({
            "city": cities[i],
            "amount": values[i] if i < len(values) else "",
            "description": (descs[i] if i < len(descs) else "")
        })

    if not items:
        flash("Inclua ao menos uma linha de despesa.", "error")
        return redirect(url_for("doctor_expenses.form"))

    ok = 0
    try:
        for i, it in enumerate(items):
            fs = files[i] if i < len(files) else None
            svc.create_one_with_file(
                uid, dt, it, fs,
                upload_dir=current_app.config["EXPENSES_UPLOAD_DIR"],
                allowed_ext=current_app.config["ALLOWED_RECEIPT_EXT"],
                max_bytes=current_app.config["MAX_CONTENT_LENGTH"]
            )
            ok += 1
        flash(f"{ok} despesa(s) registrada(s).", "ok")
    except Exception as e:
        flash(f"Erro ao salvar: {e}", "error")

    return redirect(url_for("doctor_expenses.form"))

# Endpoint de exclusão usado no template: url_for('doctor_expenses.delete', expense_id=...)
@bp.route("/expenses/<int:expense_id>/delete", methods=["POST"], endpoint="delete")
def delete_expense(expense_id: int):
    uid = session["user_id"]
    ok = svc.delete_my(uid, expense_id)
    flash("Despesa excluída." if ok else "Despesa não encontrada ou sem permissão.", "ok" if ok else "error")

    # preserva filtros
    q = {}
    for k in ("f_date_from", "f_date_to", "f_city"):
        v = request.form.get(k, "")
        if v:
            q[k] = v
    return redirect(url_for("doctor_expenses.form", **q))

@bp.route("/expenses/<int:expense_id>/file/<int:file_id>")
def download(expense_id: int, file_id: int):
    uid = session["user_id"]
    # valida se a despesa pertence ao médico (ou 404)
    mine = svc.list_mine(uid)
    if not any(r["id"] == expense_id for r in mine):
        abort(404)

    f = svc.file_by_id(file_id)
    if not f or f["expense_id"] != expense_id:
        abort(404)

    base = os.path.join(current_app.config["EXPENSES_UPLOAD_DIR"], str(expense_id))
    return send_from_directory(base, f["stored_name"], as_attachment=True, download_name=f["orig_name"])
