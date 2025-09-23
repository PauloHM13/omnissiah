# app/repositories/doctors.py
from typing import Optional, Dict, Any, List
from ..db import get_conn

class DoctorRepository:
    def upsert(self, user_id: int, doc: Dict[str, Any]) -> None:
        """
        Cria ou atualiza o registro do médico (linha única por user_id).
        Inclui os campos de PJ: company_name, company_cnpj, company_crm.
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO doctors (
                    user_id, full_name, crm, specialty, rqe, cpf, rg,
                    company_name, company_cnpj, company_crm
                )
                VALUES (
                    %s,
                    %s,
                    NULLIF(%s,''),
                    NULLIF(%s,''),
                    NULLIF(%s,''),
                    NULLIF(%s,''),
                    NULLIF(%s,''),
                    NULLIF(%s,''),
                    NULLIF(%s,''),
                    NULLIF(%s,'')
                )
                ON CONFLICT (user_id) DO UPDATE SET
                    full_name     = EXCLUDED.full_name,
                    crm           = EXCLUDED.crm,
                    specialty     = EXCLUDED.specialty,
                    rqe           = EXCLUDED.rqe,
                    cpf           = EXCLUDED.cpf,
                    rg            = EXCLUDED.rg,
                    company_name  = EXCLUDED.company_name,
                    company_cnpj  = EXCLUDED.company_cnpj,
                    company_crm   = EXCLUDED.company_crm;
                """,
                (
                    user_id,
                    doc.get("full_name"),
                    doc.get("crm"),
                    doc.get("specialty"),
                    doc.get("rqe"),
                    doc.get("cpf"),
                    doc.get("rg"),
                    doc.get("company_name"),
                    doc.get("company_cnpj"),
                    doc.get("company_crm"),
                ),
            )

    def delete(self, user_id: int) -> None:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM doctors WHERE user_id=%s;", (user_id,))

    def get(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        Retorna os dados do médico (ou None se não houver),
        incluindo campos de PJ.
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    user_id, full_name, crm, specialty, rqe, cpf, rg,
                    company_name, company_cnpj, company_crm
                FROM doctors
                WHERE user_id=%s;
                """,
                (user_id,),
            )
            return cur.fetchone()

    # ---------------------------
    # Hospitais de atuação
    # ---------------------------
    def list_hospital_ids(self, user_id: int) -> List[int]:
        sql = "SELECT hospital_id FROM doctor_hospitals WHERE user_id=%s ORDER BY hospital_id;"
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, (user_id,))
            rows = cur.fetchall()
            # rows podem ser dicts ou tuplas, dependendo do cursor
            try:
                return [r["hospital_id"] for r in rows]
            except (TypeError, KeyError):
                return [r[0] for r in rows]

    def set_hospitals(self, user_id: int, hospital_ids: List[int]) -> None:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM doctor_hospitals WHERE user_id=%s;", (user_id,))
            if hospital_ids:
                cur.executemany(
                    """
                    INSERT INTO doctor_hospitals (user_id, hospital_id)
                    VALUES (%s, %s)
                    ON CONFLICT DO NOTHING;
                    """,
                    [(user_id, hid) for hid in hospital_ids],
                )
