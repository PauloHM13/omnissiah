from ..repositories.hospitals import HospitalRepository
from ..repositories.hospital_prices import HospitalPriceRepository

class HospitalService:
    def __init__(self):
        self.hosp = HospitalRepository()
        self.prices = HospitalPriceRepository()

    # CRUD hospital
    def list(self, q: str = ""):
        return self.hosp.list(q)

    def by_id(self, hid: int):
        return self.hosp.by_id(hid)

    def create(self, payload: dict) -> int:
        return self.hosp.create(payload)

    def update(self, hid: int, payload: dict) -> None:
        self.hosp.update(hid, payload)

    def delete(self, hid: int) -> bool:
        return self.hosp.delete(hid)

    # preços
    def list_prices(self, hospital_id: int):
        return self.prices.list_for_hospital(hospital_id)

    def add_price(self, payload: dict) -> int:
        # Opcional: validar end_date >= start_date, etc.
        return self.prices.add_price(payload)

    def close_price(self, price_id: int, end_date: str) -> None:
        self.prices.close_price(price_id, end_date)

    def deactivate_price(self, price_id: int) -> None:
        self.prices.deactivate(price_id)