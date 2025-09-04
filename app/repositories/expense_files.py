# app/repositories/expense_files.py
from typing import List, Dict, Any, Optional
from ..db import get_conn

class ExpenseFilesRepository:
    def insert(self, expense_id: int, orig_name: str, stored_name: str,
               mime_type: Optional[str], size_bytes: Optional[int]) -> int:
        sql = """
          INSERT INTO expense_files (expense_id, orig_name, stored_name, mime_type, size_bytes)
          VALUES (%s, %s, %s, %s, %s) RETURNING id;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, (expense_id, orig_name, stored_name, mime_type, size_bytes))
            return cur.fetchone()["id"]

    def list_for_expense(self, expense_id: int) -> List[Dict[str, Any]]:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM expense_files WHERE expense_id=%s ORDER BY id;", (expense_id,))
            return cur.fetchall()

    def by_id(self, file_id: int) -> Optional[Dict[str, Any]]:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM expense_files WHERE id=%s;", (file_id,))
            return cur.fetchone()
