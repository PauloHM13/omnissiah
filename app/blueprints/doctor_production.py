# app/blueprints/doctor_production.py
from flask import Blueprint, render_template, request, session, abort, jsonify, flash, redirect, url_for
from ..services.production_service import ProductionService
from ..services.hospital_service import HospitalService

bp = Blueprint("doctor_production", __name__)
svc = ProductionService()
hsvc = HospitalService()

def _doctor_required():
    return bool(session.get("user_id")) and session.get("role") == "doctor"

@bp.before_request
def guard():
    if not _doctor_required():
        abort(403)

@bp.route("/production/new", methods=["GET"])
def production_form():
    uid = session["user_id"]
    allowed_ids = set(svc.allowed_hospitals(uid))
    hospitals = [h for h in hsvc.list("") if h["id"] in allowed_ids]

    # filtros (via GET)
    hid_f = request.args.get("f_hospital_id")
    pid_f = request.args.get("f_procedure_id")
    dfrom = request.args.get("f_date_from")
    dto   = request.args.get("f_date_to")

    hid = int(hid_f) if (hid_f and hid_f.isdigit()) else None
    pid = int(pid_f) if (pid_f and pid_f.isdigit()) else None

    # lista de procedimentos para o combo de filtro (se houver hospital filtrado)
    filter_procedures = svc.procedures_for(hid) if hid else []

    rows = svc.list_my(
        doctor_user_id=uid,
        hospital_id=hid,
        date_from=dfrom,
        date_to=dto,
        procedure_id=pid
    )

    return render_template(
        "doctor/production_form.html",
        hospitals=hospitals,
        rows=rows,
        f_hospital_id=hid,
        f_procedure_id=pid,
        f_date_from=dfrom or "",
        f_date_to=dto or "",
        filter_procedures=filter_procedures
    )

@bp.route("/production/procedures", methods=["GET"])
def ajax_procedures_by_hospital():
    uid = session["user_id"]
    hid = int(request.args.get("hospital_id", "0"))
    if hid not in svc.allowed_hospitals(uid):
        return jsonify({"ok": False, "error": "Hospital não autorizado."}), 403
    try:
        procs = svc.procedures_for(hid)
        data = [{"id": p["procedure_id"], "label": f'{p["tuss_code"]} — {p["name"]}'} for p in procs]
        return jsonify({"ok": True, "procedures": data})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400

@bp.route("/production/new", methods=["POST"])
def production_submit():
    uid = session["user_id"]
    hid = int(request.form.get("hospital_id"))
    dt  = request.form.get("exec_date")

    proc_ids = request.form.getlist("procedure_id")
    qtys     = request.form.getlist("quantity")
    notes    = request.form.getlist("note")

    items = []
    for i in range(len(proc_ids)):
        pid = (proc_ids[i] or "").strip()
        if not pid:
            continue
        items.append({
            "procedure_id": int(pid),
            "quantity": int(qtys[i]),
            "note": notes[i] if i < len(notes) else "",
        })

    if not items:
        flash("Inclua ao menos um procedimento.", "error")
        return redirect(url_for("doctor_production.production_form"))

    try:
        inserted = svc.create_batch(uid, hid, dt, items)
        flash(f"Produção registrada ({inserted} linha(s)).", "ok")
        return redirect(url_for("doctor_production.production_form"))
    except Exception as e:
        flash(f"Erro ao salvar: {e}", "error")
        return redirect(url_for("doctor_production.production_form"))
    
@bp.route("/production/<int:prod_id>/delete", methods=["POST"])
def delete_production(prod_id: int):
    uid = session["user_id"]
    ok = svc.delete_my(uid, prod_id)
    flash("Lançamento removido." if ok else "Registro não encontrado ou sem permissão.", "ok" if ok else "error")

    # preserva filtros ao voltar
    return redirect(url_for(
        "doctor_production.production_form",
        f_hospital_id=request.form.get("f_hospital_id") or None,
        f_procedure_id=request.form.get("f_procedure_id") or None,
        f_date_from=request.form.get("f_date_from") or None,
        f_date_to=request.form.get("f_date_to") or None
    ))