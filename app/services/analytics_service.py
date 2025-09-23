# app/services/analytics_service.py
from typing import Any, Dict, Optional, List
from datetime import date

from ..repositories.analytics import AnalyticsRepository
from ..repositories.productions import ProductionRepository
from ..repositories.hospitals import HospitalRepository
from ..repositories.procedures import ProcedureRepository


class AnalyticsService:
    def __init__(self):
        self.repo = AnalyticsRepository()
        self.prods = ProductionRepository()
        self.hosp = HospitalRepository()
        self.procs = ProcedureRepository()

    # -----------------------------
    # ADMIN DASHBOARD (com filtros)
    # -----------------------------
    def dashboard_data(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        hospital_id: Optional[int] = None,
        doctor_user_id: Optional[int] = None,
        procedure_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        # KPIs "de cadastro" (sempre não filtrados)
        t = self.repo.totals()

        # KPI filtrado: soma das quantidades lançadas
        total_proc = self.repo.total_procedures(
            date_from, date_to, hospital_id, doctor_user_id, procedure_id
        ) or 0

        # Série mensal filtrada (ou ano corrente se sem período)
        monthly_rows = self.repo.monthly_production(
            date_from, date_to, hospital_id, doctor_user_id, procedure_id
        ) or []
        monthly: List[float] = [0.0] * 12
        for r in monthly_rows:
            m = int(r["m"])
            monthly[m - 1] = float(r["qty"])

        # Rótulo do gráfico
        year_label = "período" if (date_from or date_to) else str(date.today().year)

        # Rankings (filtrados)
        top_doctors = self.repo.top_doctors(
            limit=8,
            date_from=date_from,
            date_to=date_to,
            hospital_id=hospital_id,
            doctor_user_id=doctor_user_id,
            procedure_id=procedure_id,
        ) or []
        top_hospitals = self.repo.top_hospitals(
            limit=8,
            date_from=date_from,
            date_to=date_to,
            hospital_id=hospital_id,
            doctor_user_id=doctor_user_id,
            procedure_id=procedure_id,
        ) or []

        return {
            "year": year_label,
            "totals": {
                "hospitals": int(t["hospitals"]),
                "doctors": int(t["doctors"]),
                "procedures": float(total_proc),
            },
            "monthly": monthly,
            "top_doctors": [
                {"name": r["name"], "qty": float(r["qty"])} for r in top_doctors
            ],
            "top_hospitals": [
                {"name": r["name"], "qty": float(r["qty"])} for r in top_hospitals
            ],
        }

    # -----------------------------
    # MÉDICO – dados do dashboard
    # -----------------------------
    def doctor_dashboard_data(self, user_id: int) -> Dict[str, Any]:
        """Agrega tudo que o dashboard do médico precisa."""
        yr = date.today().year

        # Hospitais vinculados (apelido/nome)
        hospitals = self.repo.hospitals_for_doctor(user_id) or []
        hospitals_count = len(hospitals)

        # Total de procedimentos (soma de quantities)
        procedures_total = int(self.repo.doctor_procedures_total(user_id) or 0)

        # Quebra por procedimento (nome + qty) — útil para listas/tabelas
        procedures_breakdown = (
            self.repo.doctor_procedures_breakdown(user_id, limit=30) or []
        )

        # Série mensal (quantidade por mês do ano atual)
        monthly_rows = self.repo.doctor_monthly_production(user_id, yr) or []
        monthly: List[int] = [0] * 12
        for r in monthly_rows:
            m = int(r["m"])
            q = int(r["qty"])
            if 1 <= m <= 12:
                monthly[m - 1] = q

        # Produção recente (últimos 5 lançamentos)
        recent = self.repo.recent_productions_for_doctor(user_id, limit=5) or []

        return {
            "year": yr,
            "hospitals": hospitals,
            "hospitals_count": hospitals_count,
            "procedures_total": procedures_total,
            "procedures_breakdown": procedures_breakdown,
            "monthly": monthly,
            "recent": recent,
        }

    # ------------------------------------------------------------------
    # (opcionais) Pass-throughs, caso você já use em outros lugares
    # ------------------------------------------------------------------
    def monthly_for_doctor(self, doctor_user_id: int, year: int) -> List[int]:
        rows = (
            self.prods.monthly_for_doctor(doctor_user_id, year)
            if hasattr(self.prods, "monthly_for_doctor")
            else []
        )
        series = [0] * 12
        for r in rows:
            m = r.get("m") or r.get("month")
            q = r.get("qty") or r.get("quantity") or 0
            if m and 1 <= int(m) <= 12:
                series[int(m) - 1] = int(q)
        return series

    def procedures_breakdown_for_doctor(self, doctor_user_id: int) -> List[Dict[str, Any]]:
        if hasattr(self.prods, "breakdown_for_doctor"):
            return self.prods.breakdown_for_doctor(doctor_user_id)
        return []

    def hospitals_for_doctor(self, doctor_user_id: int) -> List[Dict[str, Any]]:
        if hasattr(self.hosp, "list_for_doctor"):
            return self.hosp.list_for_doctor(doctor_user_id)
        return []
