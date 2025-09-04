# app/services/expenses_service.py
from typing import List, Dict, Any, Optional
from datetime import datetime
import os, time, secrets, mimetypes
from werkzeug.utils import secure_filename

from ..repositories.expenses import ExpensesRepository
from ..repositories.expense_files import ExpenseFilesRepository

class ExpensesService:
    def __init__(self) -> None:
        self.repo = ExpensesRepository()
        self.files_repo = ExpenseFilesRepository()

    @staticmethod
    def _norm_date(s: str) -> str:
        s = (s or "").strip()
        for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
            try:
                return datetime.strptime(s, fmt).date().isoformat()
            except ValueError:
                pass
        raise ValueError("Data inválida. Use YYYY-MM-DD ou DD/MM/YYYY.")

    @staticmethod
    def _money(s: Optional[str]) -> str:
        s = (s or "").strip().replace(" ", "")
        return s.replace(",", ".")

    # Continua disponível para uso sem arquivos (lote)
    def create_batch(self, doctor_user_id: int, request_date: str, items: List[Dict[str, Any]]) -> int:
        dt = self._norm_date(request_date)
        rows: List[Dict[str, Any]] = []
        for it in items:
            city = (it.get("city") or "").strip()
            amount = self._money(it.get("amount"))
            if not city:
                raise ValueError("Cidade destino é obrigatória.")
            if not amount:
                raise ValueError("Valor é obrigatório.")
            rows.append({
                "doctor_user_id": doctor_user_id,
                "request_date": dt,
                "city": city,
                "amount": amount,
                "description": (it.get("description") or "").strip()
            })
        return self.repo.insert_many(rows)

    # Cria 1 linha e anexa arquivo opcional
    def create_one_with_file(
        self,
        doctor_user_id: int,
        request_date: str,
        item: Dict[str, Any],
        file_storage,
        upload_dir: str,
        allowed_ext: set,
        max_bytes: int
    ) -> int:
        dt = self._norm_date(request_date)
        city = (item.get("city") or "").strip()
        amount = self._money(item.get("amount"))
        if not city:
            raise ValueError("Cidade destino é obrigatória.")
        if not amount:
            raise ValueError("Valor é obrigatório.")

        expense_id = self.repo.insert_one({
            "doctor_user_id": doctor_user_id,
            "request_date": dt,
            "city": city,
            "amount": amount,
            "description": (item.get("description") or "").strip()
        })

        # anexa se veio arquivo
        if file_storage and getattr(file_storage, "filename", ""):
            self._attach_file(expense_id, file_storage, upload_dir, allowed_ext, max_bytes)
        return expense_id

    def _attach_file(self, expense_id: int, fs, upload_dir: str, allowed_ext: set, max_bytes: int) -> int:
        filename = (fs.filename or "").strip()
        if not filename:
            return 0

        orig = secure_filename(filename)
        ext = orig.rsplit(".", 1)[-1].lower() if "." in orig else ""
        if ext not in allowed_ext:
            raise ValueError("Extensão não permitida. Use PDF ou imagem.")

        # checa tamanho
        fs.stream.seek(0, os.SEEK_END)
        size = fs.stream.tell()
        fs.stream.seek(0)
        if size > max_bytes:
            raise ValueError("Arquivo excede o tamanho máximo permitido.")

        # pasta por despesa
        dst_dir = os.path.join(upload_dir, str(expense_id))
        os.makedirs(dst_dir, exist_ok=True)

        rand = secrets.token_hex(4)
        stored = f"{int(time.time())}_{rand}.{ext}"
        path = os.path.join(dst_dir, stored)
        fs.save(path)

        mime = fs.mimetype or mimetypes.guess_type(orig)[0]
        return self.files_repo.insert(expense_id, orig, stored, mime, size)

    # Listagens
    def list_mine(
        self,
        doctor_user_id: int,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        city_like: Optional[str] = None
    ):
        return self.repo.list(
            doctor_user_id=doctor_user_id,
            date_from=date_from or None,
            date_to=date_to or None,
            city_like=city_like or None,
            limit=1000,
        )

    def list_all(
        self,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        city_like: Optional[str] = None,
        doctor_user_id: Optional[int] = None,   # <- filtro por médico (admin)
    ):
        return self.repo.list(
            doctor_user_id=doctor_user_id,
            date_from=date_from or None,
            date_to=date_to or None,
            city_like=city_like or None,
            limit=2000,
        )

    # Exclusões
    def delete_my(self, doctor_user_id: int, expense_id: int) -> bool:
        return self.repo.delete_own(expense_id, doctor_user_id)

    def delete_any(self, expense_id: int) -> bool:
        return self.repo.delete_any(expense_id)

    # Arquivos
    def files_for_expense(self, expense_id: int):
        return self.files_repo.list_for_expense(expense_id)

    def file_by_id(self, file_id: int):
        return self.files_repo.by_id(file_id)
