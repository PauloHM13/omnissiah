# app/services/hospital_service.py
from typing import Optional, Dict, Any, List

from ..repositories.hospitals import HospitalRepository
from ..repositories.hospital_prices import HospitalPriceRepository


def _normalize_money(value: Optional[str]) -> str:
    """
    Normaliza valores em formato brasileiro para ponto flutuante US:
    - "1.234,56" -> "1234.56"
    - "1234,56"  -> "1234.56"
    - "100"      -> "100"
    """
    s = (value or "").strip().replace(" ", "")
    if "," in s and "." in s:
        # assume '.' como separador de milhar e ',' como decimal
        s = s.replace(".", "")
    return s.replace(",", ".")


class HospitalService:
    def __init__(self) -> None:
        self.hosp = HospitalRepository()
        self.prices = HospitalPriceRepository()

    # -----------------
    # CRUD de hospitais
    # -----------------
    def list(self, q: str = "") -> List[Dict[str, Any]]:
        return self.hosp.list(q)

    def by_id(self, hid: int) -> Optional[Dict[str, Any]]:
        return self.hosp.by_id(hid)

    def create(self, payload: Dict[str, Any]) -> int:
        return self.hosp.create(payload)

    def update(self, hid: int, payload: Dict[str, Any]) -> None:
        self.hosp.update(hid, payload)

    def delete(self, hid: int) -> bool:
        return self.hosp.delete(hid)

    # -----------------
    # Preços/procedures
    # -----------------
    def list_prices(self, hospital_id: int) -> List[Dict[str, Any]]:
        return self.prices.list_for_hospital(hospital_id)

    def add_price(self, payload: Dict[str, Any]) -> int:
        """
        Insere um preço (sem vigência). Garante normalização do campo 'price'.
        Espera payload com: hospital_id, procedure_id, price (BR/US), start_date(opc),
        note(opc), active(opc).
        """
        data = dict(payload)
        data["price"] = _normalize_money(data.get("price"))
        return self.prices.add_price(data)

    def update_price(self, price_id: int, price: str, note: str, active: bool) -> None:
        """
        Atualiza o preço existente (sem vigência).
        """
        p = _normalize_money(price)
        self.prices.update_price(price_id, p, note, active)

    def deactivate_price(self, price_id: int) -> None:
        self.prices.deactivate(price_id)

    # Mantido apenas por compatibilidade (não usamos end_date mais).
    def close_price(self, price_id: int, end_date: str) -> None:
        self.prices.close_price(price_id, end_date)

    # Úteis para a tela do médico (lista de procedimentos/preço vigente)
    def procedures_for_hospital(self, hospital_id: int) -> List[Dict[str, Any]]:
        """
        Retorna uma linha por procedimento com o preço ativo mais recente.
        """
        return self.prices.list_procedures_for_hospital(hospital_id)

    def resolve_price(self, hospital_id: int, procedure_id: int) -> Optional[float]:
        """
        Retorna o preço ativo mais recente para um procedimento em um hospital.
        """
        return self.prices.resolve_price(hospital_id, procedure_id)
