# app/repositories/productions.py
from typing import List, Dict, Any, Optional
from ..db import get_conn

class ProductionRepository:
    def insert_many(self, rows: List[Dict[str, Any]]) -> int:
        """
        Insere múltiplos lançamentos de produção.
        Espera cada linha com:
          doctor_user_id, hospital_id, exec_date (YYYY-MM-DD),
          procedure_id, quantity, unit_price, note
        """
        if not rows:
            return 0
        sql = """
            INSERT INTO productions
              (doctor_user_id, hospital_id, exec_date, procedure_id, quantity, unit_price, note)
            VALUES
              (%(doctor_user_id)s, %(hospital_id)s, %(exec_date)s::date,
               %(procedure_id)s, %(quantity)s, %(unit_price)s, NULLIF(%(note)s,''))
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.executemany(sql, rows)
            return cur.rowcount

    def list(
        self,
        doctor_user_id: Optional[int] = None,
        hospital_id: Optional[int] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        procedure_id: Optional[int] = None,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Lista lançamentos de produção com filtros opcionais.
        """
        wh: list[str] = []
        params: dict[str, Any] = {}
        if doctor_user_id:
            wh.append("pr.doctor_user_id = %(doctor_user_id)s")
            params["doctor_user_id"] = doctor_user_id
        if hospital_id:
            wh.append("pr.hospital_id = %(hospital_id)s")
            params["hospital_id"] = hospital_id
        if date_from:
            wh.append("pr.exec_date >= %(date_from)s::date")
            params["date_from"] = date_from
        if date_to:
            wh.append("pr.exec_date <= %(date_to)s::date")
            params["date_to"] = date_to
        if procedure_id:
            wh.append("pr.procedure_id = %(procedure_id)s")
            params["procedure_id"] = procedure_id

        where = ("WHERE " + " AND ".join(wh)) if wh else ""
        sql = f"""
            SELECT pr.id, pr.exec_date, pr.quantity, pr.unit_price,
                   (pr.quantity * COALESCE(pr.unit_price,0))::numeric AS total,
                   pr.note,
                   u.id AS doctor_id, u.username, COALESCE(d.full_name,'') AS doctor_name,
                   h.id AS hospital_id, COALESCE(h.nickname, h.trade_name, h.corporate_name) AS hospital_name,
                   p.id AS procedure_id, p.tuss_code, p.name AS procedure_name
              FROM productions pr
              JOIN users u        ON u.id = pr.doctor_user_id
              LEFT JOIN doctors d ON d.user_id = pr.doctor_user_id
              JOIN hospitals h    ON h.id = pr.hospital_id
              JOIN procedures p   ON p.id = pr.procedure_id
              {where}
             ORDER BY pr.exec_date DESC, pr.id DESC
             LIMIT %(limit)s;
        """
        params["limit"] = max(1, min(limit, 5000))
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def delete_own(self, prod_id: int, doctor_user_id: int) -> bool:
        """
        Exclui um lançamento se pertencer ao médico informado.
        Retorna True se apagou, False caso não exista/permissão negada.
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                "DELETE FROM productions WHERE id=%s AND doctor_user_id=%s RETURNING id;",
                (prod_id, doctor_user_id),
            )
            return cur.fetchone() is not None
