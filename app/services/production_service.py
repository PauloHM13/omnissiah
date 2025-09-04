# app/services/production_service.py
from typing import List, Dict, Any, Optional
from datetime import datetime
from ..repositories.productions import ProductionRepository
from ..repositories.hospital_prices import HospitalPriceRepository
from ..repositories.doctors import DoctorRepository

class ProductionService:
    def __init__(self):
        self.repo = ProductionRepository()
        self.prices = HospitalPriceRepository()
        self.docs = DoctorRepository()

    @staticmethod
    def _norm_date(s: str) -> str:
        s = (s or "").strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(s, fmt).date().isoformat()
            except ValueError:
                pass
        raise ValueError("Data de execução inválida. Use YYYY-MM-DD ou DD/MM/YYYY.")

    def allowed_hospitals(self, user_id: int) -> list[int]:
        return self.docs.list_hospital_ids(user_id)

    def procedures_for(self, hospital_id: int) -> list[dict]:
        return self.prices.list_procedures_for_hospital(hospital_id)

    def create_batch(self, doctor_user_id: int, hospital_id: int, exec_date: str,
                     items: List[Dict[str, Any]]) -> int:
        if hospital_id not in self.allowed_hospitals(doctor_user_id):
            raise PermissionError("Hospital não vinculado ao seu usuário.")
        dt = self._norm_date(exec_date)

        rows = []
        for it in items:
            pid = int(it["procedure_id"])
            qty = int(it["quantity"])
            if qty <= 0:
                raise ValueError("Quantidade deve ser > 0.")
            price = self.prices.resolve_price(hospital_id, pid)  # usa último preço ativo
            if price is None:
                raise ValueError("Procedimento sem preço ativo no hospital.")
            rows.append({
                "doctor_user_id": doctor_user_id,
                "hospital_id": hospital_id,
                "exec_date": dt,
                "procedure_id": pid,
                "quantity": qty,
                "unit_price": price,
                "note": (it.get("note") or "").strip(),
            })
        return self.repo.insert_many(rows)

    # NOVO: histórico do próprio médico com filtros
    def list_my(
        self,
        doctor_user_id: int,
        hospital_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        procedure_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        return self.repo.list(
            doctor_user_id=doctor_user_id,
            hospital_id=hospital_id or None,
            date_from=date_from or None,
            date_to=date_to or None,
            procedure_id=procedure_id or None,
            limit=1000
        )

    def delete_my(self, doctor_user_id: int, prod_id: int) -> bool:
        return self.repo.delete_own(prod_id, doctor_user_id)
