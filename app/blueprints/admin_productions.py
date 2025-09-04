# app/blueprints/admin_productions.py
from flask import Blueprint, render_template, request, session, abort
from ..repositories.productions import ProductionRepository
from ..services.hospital_service import HospitalService
from ..services.user_service import UserService

bp = Blueprint("admin_productions", __name__)
repo = ProductionRepository()
hsvc = HospitalService()
usvc = UserService()

def _admin_required():
    return bool(session.get("user_id")) and session.get("role") == "admin"

@bp.before_request
def guard():
    if not _admin_required():
        abort(403)

@bp.route("/productions", methods=["GET"])
def list_all():
    # filtros
    doctor_id = request.args.get("doctor_id")
    hospital_id = request.args.get("hospital_id")
    date_from = request.args.get("date_from")
    date_to   = request.args.get("date_to")

    did = int(doctor_id) if doctor_id and doctor_id.isdigit() else None
    hid = int(hospital_id) if hospital_id and hospital_id.isdigit() else None

    rows = repo.list(
        doctor_user_id=did,
        hospital_id=hid,
        date_from=date_from or None,
        date_to=date_to or None,
        limit=1000
    )

    # combos
    hospitals = hsvc.list("")  # todos
    # busca usuários e filtra médicos
    users = usvc.list_users()
    doctors = [u for u in users if u.get("role") == "doctor"]

    return render_template(
        "admin/productions_list.html",
        rows=rows,
        hospitals=hospitals,
        doctors=doctors,
        # manter filtros na UI
        sel_doctor=did, sel_hospital=hid,
        date_from=date_from or "", date_to=date_to or ""
    )
