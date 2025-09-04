# app/services/user_service.py
from ..repositories.users import UserRepository
from ..repositories.doctors import DoctorRepository
from ..repositories.hospitals import HospitalRepository

class UserService:
    def __init__(self):
        self.users = UserRepository()
        self.docs = DoctorRepository()
        self.hosp  = HospitalRepository()   # para listar todos no form

    # ---- Autenticação / Perfil ----
    def authenticate(self, username: str, password: str):
        return self.users.authenticate(username, password)

    def change_password(self, user_id: int, current: str, new_pass: str) -> bool:
        return self.users.change_password(user_id, current, new_pass)

    # ---- Administração de usuários ----
    def list_users(self):
        return self.users.list()

    def create_user(self, payload: dict) -> tuple[int, str]:
        """Cria usuário; se for doctor, cria/atualiza perfil em doctors.
        Retorna (user_id, senha_provisoria)."""
        user_id = self.users.create(payload)

        if payload.get("role") == "doctor":
            self.docs.upsert(user_id, {
                "full_name": payload.get("full_name"),
                "crm": payload.get("crm"),
                "specialty": payload.get("specialty"),
                "rqe": payload.get("rqe"),
                "cpf": payload.get("cpf"),
                "rg": payload.get("rg"),
            })

        # senha provisória veio no payload como "password"
        return user_id, payload.get("password")

    def update_user(self, user_id: int, fields: dict) -> None:
        self.users.update(user_id, fields)
        if fields.get("role") == "doctor":
            self.docs.upsert(user_id, {
                "full_name": fields.get("full_name"),
                "crm": fields.get("crm"),
                "specialty": fields.get("specialty"),
                "rqe": fields.get("rqe"),
                "cpf": fields.get("cpf"),
                "rg": fields.get("rg"),
            })
        else:
            # se deixou de ser médico, remove perfil doctor
            self.docs.delete(user_id)

    def delete_user(self, user_id: int) -> bool:
        return self.users.delete(user_id)

    def reset_password(self, user_id: int, new_pass: str):
        """Retorna o username se encontrou e resetou; senão None."""
        return self.users.reset_password(user_id, new_pass)
    
    def doctor_hospital_ids(self, user_id: int):
        return self.docs.list_hospital_ids(user_id)

    def set_doctor_hospitals(self, user_id: int, hospital_ids: list[int]):
        # filtra só IDs válidos (existentes) por segurança (opcional)
        all_ids = {h["id"] for h in self.hosp.list("")}
        clean = [hid for hid in hospital_ids if hid in all_ids]
        self.docs.set_hospitals(user_id, clean)
