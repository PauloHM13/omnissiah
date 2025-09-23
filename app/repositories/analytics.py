# app/repositories/analytics.py
from typing import Dict, Any, List, Optional, Tuple
from datetime import date
from ..db import get_conn


class AnalyticsRepository:
    # ---- helpers ------------------------------------------------------------
    def _where(
        self,
        date_from: Optional[str],
        date_to: Optional[str],
        hospital_id: Optional[int],
        doctor_user_id: Optional[int],
        procedure_id: Optional[int],
    ) -> Tuple[str, list]:
        clauses: List[str] = []
        params: List[Any] = []

        if date_from:
            clauses.append("p.exec_date >= %s")
            params.append(date_from)
        if date_to:
            clauses.append("p.exec_date <= %s")
            params.append(date_to)
        if hospital_id:
            clauses.append("p.hospital_id = %s")
            params.append(hospital_id)
        if doctor_user_id:
            clauses.append("p.doctor_user_id = %s")
            params.append(doctor_user_id)
        if procedure_id:
            clauses.append("p.procedure_id = %s")
            params.append(procedure_id)

        where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
        return where, params

    # ---- contagens "de cadastro" (não filtradas) ----------------------------
    def totals(self) -> Dict[str, Any]:
        sql = """
        SELECT
          (SELECT COUNT(*) FROM hospitals) AS hospitals,
          (SELECT COUNT(*) FROM users WHERE role='doctor') AS doctors
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql)
            return cur.fetchone()

    # ---- total de procedimentos (FILTRADO) ---------------------------------
    def total_procedures(
        self,
        date_from: Optional[str],
        date_to: Optional[str],
        hospital_id: Optional[int],
        doctor_user_id: Optional[int],
        procedure_id: Optional[int],
    ) -> int:
        where, params = self._where(date_from, date_to, hospital_id, doctor_user_id, procedure_id)
        sql = f"SELECT COALESCE(SUM(p.quantity), 0)::int AS qty FROM productions p {where};"
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            row = cur.fetchone()
            return int(row["qty"]) if row else 0

    # ---- série mensal (FILTRADA) -------------------------------------------
    def monthly_production(
        self,
        date_from: Optional[str],
        date_to: Optional[str],
        hospital_id: Optional[int],
        doctor_user_id: Optional[int],
        procedure_id: Optional[int],
    ) -> List[Dict[str, Any]]:
        where, params = self._where(date_from, date_to, hospital_id, doctor_user_id, procedure_id)

        # Se não veio período, restringe ao ano corrente
        if not date_from and not date_to:
            if where:
                where += " AND EXTRACT(YEAR FROM p.exec_date) = %s"
            else:
                where = "WHERE EXTRACT(YEAR FROM p.exec_date) = %s"
            params.append(date.today().year)

        sql = f"""
            SELECT EXTRACT(MONTH FROM p.exec_date)::int AS m,
                   COALESCE(SUM(p.quantity),0)::int AS qty
              FROM productions p
              {where}
          GROUP BY 1
          ORDER BY 1;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    # ---- ranking por médico (FILTRADO) -------------------------------------
    def top_doctors(
        self,
        limit: int = 8,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        hospital_id: Optional[int] = None,
        doctor_user_id: Optional[int] = None,
        procedure_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        where, params = self._where(date_from, date_to, hospital_id, doctor_user_id, procedure_id)
        params.append(limit)
        sql = f"""
            SELECT COALESCE(d.full_name, u.username) AS name,
                   COALESCE(SUM(p.quantity),0)::int AS qty
              FROM productions p
              JOIN users u        ON u.id = p.doctor_user_id
         LEFT JOIN doctors d      ON d.user_id = u.id
              {where}
          GROUP BY 1
          ORDER BY qty DESC
          LIMIT %s;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    # ---- ranking por hospital (FILTRADO) -----------------------------------
    def top_hospitals(
        self,
        limit: int = 8,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
        hospital_id: Optional[int] = None,
        doctor_user_id: Optional[int] = None,
        procedure_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        where, params = self._where(date_from, date_to, hospital_id, doctor_user_id, procedure_id)
        params.append(limit)
        sql = f"""
            SELECT COALESCE(h.nickname, h.trade_name, h.corporate_name) AS name,
                   COALESCE(SUM(p.quantity),0)::int AS qty
              FROM productions p
              JOIN hospitals h ON h.id = p.hospital_id
              {where}
          GROUP BY 1
          ORDER BY qty DESC
          LIMIT %s;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def hospitals_for_doctor(self, user_id: int) -> List[Dict[str, Any]]:
        sql = """
        SELECT h.id,
               COALESCE(h.nickname, h.trade_name, h.corporate_name) AS name
          FROM doctor_hospitals dh
          JOIN hospitals h ON h.id = dh.hospital_id
         WHERE dh.user_id = %s
         ORDER BY name;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, (user_id,))
            return cur.fetchall()

    def doctor_procedures_total(self, user_id: int) -> int:
        sql = """
        SELECT COALESCE(SUM(quantity),0)::int AS qty
          FROM productions
         WHERE doctor_user_id = %s;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, (user_id,))
            row = cur.fetchone()
            return row["qty"] if row else 0

    def doctor_procedures_breakdown(self, user_id: int, limit: int = 30) -> List[Dict[str, Any]]:
        sql = """
        SELECT COALESCE(p.name, '(sem nome)') AS name,
               p.tuss_code,
               SUM(pr.quantity)::int AS qty
          FROM productions pr
          LEFT JOIN procedures p ON p.id = pr.procedure_id
         WHERE pr.doctor_user_id = %s
         GROUP BY 1,2
         ORDER BY qty DESC
         LIMIT %s;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, (user_id, limit))
            return cur.fetchall()

    def doctor_monthly_production(self, user_id: int, year: int) -> List[Dict[str, Any]]:
        sql = """
        SELECT EXTRACT(MONTH FROM exec_date)::int AS m,
               SUM(quantity)::int AS qty
          FROM productions
         WHERE doctor_user_id = %s
           AND EXTRACT(YEAR FROM exec_date) = %s
         GROUP BY 1
         ORDER BY 1;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, (user_id, year))
            return cur.fetchall()

    def recent_productions_for_doctor(self, doctor_user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Últimos lançamentos do médico (ordenado por data de execução, depois id).
        Ajuste o ORDER BY para created_at DESC se sua tabela tiver essa coluna.
        """
        sql = """
          SELECT p.id,
                 p.exec_date::date AS exec_date,
                 p.quantity::int   AS quantity,
                 COALESCE(h.nickname, h.trade_name, h.corporate_name) AS hospital_name,
                 pr.name AS procedure_name
            FROM productions p
            JOIN hospitals  h ON h.id = p.hospital_id
            JOIN procedures pr ON pr.id = p.procedure_id
           WHERE p.doctor_user_id = %(uid)s
           ORDER BY p.exec_date DESC, p.id DESC
           LIMIT %(limit)s;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {"uid": doctor_user_id, "limit": limit})
            return cur.fetchall()