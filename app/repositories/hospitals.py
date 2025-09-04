# app/repositories/hospitals.py
from typing import List, Dict, Any, Optional
from ..db import get_conn

class HospitalRepository:
    def list(self, q: str = "") -> List[Dict[str, Any]]:
        where = ""
        params: list[Any] = []
        if q:
            where = (
                "WHERE corporate_name ILIKE %s OR trade_name ILIKE %s "
                "OR nickname ILIKE %s OR cnpj ILIKE %s"
            )
            like = f"%{q}%"
            params = [like, like, like, like]
        sql = f"""
            SELECT * FROM hospitals
            {where}
            ORDER BY id DESC;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def by_id(self, hid: int) -> Optional[Dict[str, Any]]:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM hospitals WHERE id=%s;", (hid,))
            return cur.fetchone()

    def create(self, data: Dict[str, Any]) -> int:
        cols = [
            'corporate_name','trade_name','nickname','cnpj','state_reg','city_reg',
            'cep','street','number','complement','district','city','state',
            'phone','email',
            'contract_contact_name','contract_contact_email','contract_contact_phone',
            'billing_contact_name','billing_contact_email','billing_contact_phone',
            'bank_name','bank_agency','bank_account','bank_type','bank_holder','bank_holder_doc',
            'contract_start','contract_end','pay_term','reajuste_rule','fine_interest',
            'invoice_channel','send_deadline','nf_type','cfop','cnae','city_service_code','notes'
        ]
        date_cols = {'contract_start', 'contract_end'}
        placeholders = ",".join(
            [f"NULLIF(%({c})s,'')::date" if c in date_cols else f"NULLIF(%({c})s,'')" for c in cols]
        )
        sql = f"INSERT INTO hospitals ({','.join(cols)}) VALUES ({placeholders}) RETURNING id;"
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            return cur.fetchone()["id"]

    def update(self, hid: int, data: Dict[str, Any]) -> None:
        cols = [
            'corporate_name','trade_name','nickname','cnpj','state_reg','city_reg',
            'cep','street','number','complement','district','city','state',
            'phone','email',
            'contract_contact_name','contract_contact_email','contract_contact_phone',
            'billing_contact_name','billing_contact_email','billing_contact_phone',
            'bank_name','bank_agency','bank_account','bank_type','bank_holder','bank_holder_doc',
            'contract_start','contract_end','pay_term','reajuste_rule','fine_interest',
            'invoice_channel','send_deadline','nf_type','cfop','cnae','city_service_code','notes'
        ]
        date_cols = {'contract_start', 'contract_end'}
        set_clause = ",".join(
            [f"{c}=NULLIF(%({c})s,'')::date" if c in date_cols else f"{c}=NULLIF(%({c})s,'')" for c in cols]
        )
        sql = f"UPDATE hospitals SET {set_clause} WHERE id=%(id)s;"
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {**data, "id": hid})

    def delete(self, hid: int) -> bool:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM hospitals WHERE id=%s RETURNING id;", (hid,))
            return bool(cur.fetchone())
