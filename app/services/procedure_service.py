from ..repositories.procedures import ProcedureRepository

class ProcedureService:
    def __init__(self):
        self.repo = ProcedureRepository()

    def list(self, q: str = "", active: bool | None = None):
        return self.repo.list(q, active)

    def by_id(self, pid: int):
        return self.repo.by_id(pid)

    def create(self, payload: dict) -> int:
        return self.repo.create(payload)

    def update(self, pid: int, payload: dict) -> None:
        self.repo.update(pid, payload)

    def delete(self, pid: int) -> bool:
        return self.repo.delete(pid)
    
    def delete_my(self, doctor_user_id: int, prod_id: int) -> bool:
        return self.repo.delete_own(prod_id, doctor_user_id)