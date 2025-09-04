from flask import Blueprint, render_template, request, redirect, url_for, session, abort, flash
from ..services.hospital_service import HospitalService
from ..services.procedure_service import ProcedureService
from datetime import datetime, date

bp = Blueprint("admin_hospitals", __name__)
svc = HospitalService()
procs = ProcedureService()


def _money(s: str | None) -> str:
    # aceita "150,00" ou "150.00"
    s = (s or "").strip().replace(" ", "")
    return s.replace(",", ".")

def _norm_date(s: str | None) -> str:
    s = (s or "").strip()
    if not s:
        return ""  # vazio vira NULL no DB via NULLIF(...,'')::date
    # aceita ISO (YYYY-MM-DD) ou BR (DD/MM/YYYY)
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date().isoformat()  # YYYY-MM-DD
        except ValueError:
            pass
    # se vier algo inesperado, deixa como está (vai estourar e veremos a msg)
    return s


def _admin_required() -> bool:
    return bool(session.get("user_id")) and session.get("role") == "admin"

@bp.before_request
def guard():
    if not _admin_required():
        abort(403)


@bp.route("/hospitals")
def list_hospitals():
    q = request.args.get("q", "")
    hospitals = svc.list(q)
    return render_template("admin/hospitals_list.html", hospitals=hospitals, q=q)


@bp.route("/hospitals/new", methods=["GET", "POST"])
def new_hospital():
    msg = error = None
    if request.method == "POST":
        try:
            payload = {k: (request.form.get(k) or "").strip() for k in [
                "corporate_name", "trade_name", "nickname", "cnpj", "state_reg", "city_reg",
                "cep", "street", "number", "complement", "district", "city", "state",
                "phone", "email",
                "contract_contact_name", "contract_contact_email", "contract_contact_phone",
                "billing_contact_name", "billing_contact_email", "billing_contact_phone",
                "bank_name", "bank_agency", "bank_account", "bank_type", "bank_holder", "bank_holder_doc",
                "contract_start", "contract_end", "pay_term", "reajuste_rule", "fine_interest",
                "invoice_channel", "send_deadline", "nf_type", "cfop", "cnae", "city_service_code", "notes"
            ]}
            for k in ("contract_start", "contract_end"):
                payload[k] = _norm_date(payload.get(k))
            hid = svc.create(payload)
            flash("Hospital criado.", "ok")
            return redirect(url_for("admin_hospitals.edit_hospital", hospital_id=hid))
        except Exception as e:
            error = f"Erro: {e}"
    return render_template("admin/hospital_form.html", mode="new", error=error, msg=msg, hospital={})


@bp.route("/hospitals/<int:hospital_id>/edit", methods=["GET", "POST"])
def edit_hospital(hospital_id: int):
    hospital = svc.by_id(hospital_id)
    if not hospital:
        abort(404)

    msg = error = None
    if request.method == "POST":
        try:
            payload = {k: (request.form.get(k) or "").strip() for k in [
                "corporate_name", "trade_name", "nickname", "cnpj", "state_reg", "city_reg",
                "cep", "street", "number", "complement", "district", "city", "state",
                "phone", "email",
                "contract_contact_name", "contract_contact_email", "contract_contact_phone",
                "billing_contact_name", "billing_contact_email", "billing_contact_phone",
                "bank_name", "bank_agency", "bank_account", "bank_type", "bank_holder", "bank_holder_doc",
                "contract_start", "contract_end", "pay_term", "reajuste_rule", "fine_interest",
                "invoice_channel", "send_deadline", "nf_type", "cfop", "cnae", "city_service_code", "notes"
            ]}
            for k in ("contract_start", "contract_end"):
                payload[k] = _norm_date(payload.get(k))
            svc.update(hospital_id, payload)
            msg = "Hospital atualizado."
            hospital = svc.by_id(hospital_id)
        except Exception as e:
            error = f"Erro: {e}"

    # preços (aba/tabela)
    price_rows = svc.list_prices(hospital_id)
    all_procs = procs.list(active=True)
    return render_template(
        "admin/hospital_form.html",
        mode="edit",
        hospital=hospital,
        prices=price_rows,
        procedures=all_procs,
        msg=msg,
        error=error
    )


@bp.route("/hospitals/<int:hospital_id>/prices/add", methods=["POST"])
def add_price(hospital_id: int):
    try:
        today = date.today().isoformat()
        payload = {
            "hospital_id": hospital_id,
            "procedure_id": int(request.form["procedure_id"]),
            "price": _money(request.form.get("price")),
            "start_date": today,   # assumimos hoje
            "end_date": None,      # sem data final
            "charge_type": None,   # não usamos mais na UI
            "hospital_code": None, # idem
            "note": request.form.get("note") or None,
            "active": True,
        }
        svc.add_price(payload)  # encerra vigente (se houver) e insere a nova
        flash("Preço definido.", "ok")
    except Exception as e:
        flash(f"Erro ao adicionar preço: {e}", "error")

    return redirect(url_for("admin_hospitals.edit_hospital", hospital_id=hospital_id) + "#prices")


@bp.route("/hospitals/<int:hospital_id>/prices/<int:price_id>/close", methods=["POST"])
def close_price(hospital_id: int, price_id: int):
    try:
        svc.close_price(price_id, request.form.get("end_date"))
        flash("Vigência encerrada.", "ok")
    except Exception as e:
        flash(f"Erro: {e}", "error")
    return redirect(url_for("admin_hospitals.edit_hospital", hospital_id=hospital_id) + "#prices")


@bp.route("/hospitals/<int:hospital_id>/prices/<int:price_id>/deactivate", methods=["POST"])
def deactivate_price(hospital_id: int, price_id: int):
    try:
        svc.deactivate_price(price_id)
        flash("Preço inativado.", "ok")
    except Exception as e:
        flash(f"Erro: {e}", "error")
    return redirect(url_for("admin_hospitals.edit_hospital", hospital_id=hospital_id) + "#prices")
