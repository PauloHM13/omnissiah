# app/repositories/hospital_prices.py
from typing import List, Dict, Any, Optional
from ..db import get_conn

class HospitalPriceRepository:
    def list_for_hospital(self, hospital_id: int) -> List[Dict[str, Any]]:
        sql = """
            SELECT p.id, p.hospital_id, p.procedure_id, pr.tuss_code, pr.name,
                   p.price, p.start_date, p.note, p.active
              FROM hospital_procedure_prices p
              JOIN procedures pr ON pr.id = p.procedure_id
             WHERE p.hospital_id=%s
             ORDER BY pr.name, p.start_date DESC, p.id DESC;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, (hospital_id,))
            return cur.fetchall()

    def add_price(self, data: Dict[str, Any]) -> int:
        """
        Insere preço sem colunas de vigência/charge_type/hospital_code.
        Garante start_date (hoje) e converte preço para numeric.
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO hospital_procedure_prices
                (hospital_id, procedure_id, price, start_date, note, active)
                VALUES
                (%(hospital_id)s,
                %(procedure_id)s,
                NULLIF(%(price)s,'')::numeric,
                COALESCE(NULLIF(%(start_date)s,'')::date, CURRENT_DATE),
                NULLIF(%(note)s,''),
                COALESCE(%(active)s, TRUE))
                RETURNING id;
                """,
                data,
            )
            return cur.fetchone()["id"]

    def close_price(self, price_id: int, end_date: str) -> None:
        # Se você não usa mais end_date, pode remover esse método
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE hospital_procedure_prices SET start_date = start_date WHERE id=%s;",
                (price_id,),
            )

    def deactivate(self, price_id: int) -> None:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("UPDATE hospital_procedure_prices SET active=FALSE WHERE id=%s;", (price_id,))

    # ---------------------------
    # Suporte ao formulário médico (SEM vigência)
    # ---------------------------

    def list_procedures_for_hospital(self, hospital_id: int) -> List[Dict[str, Any]]:
        """
        Retorna 1 linha por procedimento cadastrado para o hospital,
        pegando o PREÇO ATIVO mais recente, ignorando datas.
        """
        sql = """
          SELECT DISTINCT ON (hpp.procedure_id)
                 p.id AS procedure_id, p.tuss_code, p.name, p.charge_unit,
                 hpp.price::numeric AS price
            FROM hospital_procedure_prices hpp
            JOIN procedures p ON p.id = hpp.procedure_id
           WHERE hpp.hospital_id = %(hid)s
             AND p.active = TRUE
             AND hpp.active = TRUE
           ORDER BY hpp.procedure_id, hpp.id DESC;   -- pega o último ativo
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {"hid": hospital_id})
            return cur.fetchall()

    def resolve_price(self, hospital_id: int, procedure_id: int) -> Optional[float]:
        """
        Retorna o preço ATIVO mais recente (ignora datas).
        """
        sql = """
          SELECT hpp.price::numeric AS price
            FROM hospital_procedure_prices hpp
           WHERE hpp.hospital_id = %(hid)s
             AND hpp.procedure_id = %(pid)s
             AND hpp.active = TRUE
           ORDER BY hpp.id DESC
           LIMIT 1;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {"hid": hospital_id, "pid": procedure_id})
            row = cur.fetchone()
            return row["price"] if row else None
