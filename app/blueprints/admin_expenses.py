# app/blueprints/admin_expenses.py
from flask import Blueprint, render_template, request, session, abort, flash, redirect, url_for, send_from_directory, current_app
import os
from ..services.expenses_service import ExpensesService
from ..db import get_conn

bp = Blueprint("admin_expenses", __name__)
svc = ExpensesService()

def _admin_required() -> bool:
    return bool(session.get("user_id")) and session.get("role") == "admin"

@bp.before_request
def guard():
    if not _admin_required():
        abort(403)

def _list_doctors():
    """
    Retorna [{'id': user_id, 'name': 'Nome do médico ou username'}]
    """
    sql = """
        SELECT u.id,
               COALESCE(NULLIF(TRIM(d.full_name), ''), u.username) AS name
          FROM users u
          LEFT JOIN doctors d ON d.user_id = u.id
         WHERE u.role = 'doctor'
         ORDER BY name;
    """
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(sql)
        return cur.fetchall()

@bp.route("/expenses")
def list_all():
    dfrom = request.args.get("f_date_from", "")
    dto   = request.args.get("f_date_to", "")
    city  = request.args.get("f_city", "")
    f_doc = request.args.get("f_doctor_id", "")  # <-- novo filtro

    doctor_id = int(f_doc) if f_doc.isdigit() else None

    rows = svc.list_all(
        date_from=dfrom or None,
        date_to=dto or None,
        city_like=city or None,
        doctor_user_id=doctor_id,  # <-- aplica filtro
    )

    files_map = { r["id"]: svc.files_for_expense(r["id"]) for r in rows }
    doctors = _list_doctors()

    return render_template(
        "admin/expenses_list.html",
        rows=rows,
        files_map=files_map,
        doctors=doctors,          # <-- lista para o <select>
        f_date_from=dfrom, f_date_to=dto, f_city=city,
        f_doctor_id=f_doc,        # <-- mantém seleção
    )

@bp.route("/expenses/<int:expense_id>/delete", methods=["POST"])
def delete_any(expense_id: int):
    ok = svc.delete_any(expense_id)
    flash("Despesa excluída." if ok else "Despesa não encontrada.", "ok" if ok else "error")

    # preserva filtros
    q = {}
    for k in ("f_date_from", "f_date_to", "f_city", "f_doctor_id"):
        v = request.form.get(k, "")
        if v:
            q[k] = v
    return redirect(url_for("admin_expenses.list_all", **q))

@bp.route("/expenses/<int:expense_id>/file/<int:file_id>")
def download_any(expense_id: int, file_id: int):
    f = svc.file_by_id(file_id)
    if not f or f["expense_id"] != expense_id:
        abort(404)
    base = os.path.join(current_app.config["EXPENSES_UPLOAD_DIR"], str(expense_id))
    return send_from_directory(base, f["stored_name"], as_attachment=True, download_name=f["orig_name"])
