# app/repositories/expenses.py
from typing import List, Dict, Any, Optional
from ..db import get_conn

class ExpensesRepository:
    def insert_many(self, rows: List[Dict[str, Any]]) -> int:
        if not rows:
            return 0
        sql = """
            INSERT INTO expenses
              (doctor_user_id, request_date, city, amount, description)
            VALUES
              (%(doctor_user_id)s, %(request_date)s::date,
               NULLIF(%(city)s,''), NULLIF(%(amount)s,'')::numeric,
               NULLIF(%(description)s,''))
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.executemany(sql, rows)
            return cur.rowcount

    def list(
        self,
        doctor_user_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        city_like: Optional[str] = None,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        wh: List[str] = []
        params: Dict[str, Any] = {}

        if doctor_user_id:
            wh.append("e.doctor_user_id = %(doctor_user_id)s")
            params["doctor_user_id"] = doctor_user_id
        if date_from:
            wh.append("e.request_date >= %(date_from)s::date")
            params["date_from"] = date_from
        if date_to:
            wh.append("e.request_date <= %(date_to)s::date")
            params["date_to"] = date_to
        if city_like:
            wh.append("unaccent(lower(e.city)) LIKE unaccent(lower(%(city_like)s))")
            params["city_like"] = f"%{city_like}%"

        where = f"WHERE {' AND '.join(wh)}" if wh else ""
        sql = f"""
            SELECT e.id, e.request_date, e.city, e.amount, e.description,
                   u.id AS doctor_id, u.username, COALESCE(d.full_name,'') AS doctor_name
              FROM expenses e
              JOIN users u        ON u.id = e.doctor_user_id
              LEFT JOIN doctors d ON d.user_id = e.doctor_user_id
              {where}
             ORDER BY e.request_date DESC, e.id DESC
             LIMIT %(limit)s;
        """
        params["limit"] = max(1, min(limit, 5000))
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def delete_own(self, expense_id: int, doctor_user_id: int) -> bool:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM expenses WHERE id=%s AND doctor_user_id=%s RETURNING id;",
                (expense_id, doctor_user_id),
            )
            return cur.fetchone() is not None

    # opcional: exclusão sem dono (para admin)
    def delete_any(self, expense_id: int) -> bool:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM expenses WHERE id=%s RETURNING id;", (expense_id,))
            return cur.fetchone() is not None
        
    def insert_one(self, row: Dict[str, Any]) -> int:
        sql = """
          INSERT INTO expenses
            (doctor_user_id, request_date, city, amount, description)
          VALUES
            (%(doctor_user_id)s, %(request_date)s::date,
             NULLIF(%(city)s,''), NULLIF(%(amount)s,'')::numeric, NULLIF(%(description)s,''))
          RETURNING id;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, row)
            return cur.fetchone()["id"]
