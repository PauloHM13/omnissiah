from typing import List, Dict, Any, Optional
from ..db import get_conn

class ProcedureRepository:
    def list(self, q: str = "", active: Optional[bool] = None) -> List[Dict[str, Any]]:
        where = []
        params: list[Any] = []
        if q:
            where.append("(tuss_code ILIKE %s OR name ILIKE %s)")
            like = f"%{q}%"; params += [like, like]
        if active is not None:
            where.append("active=%s"); params.append(active)
        where_sql = ("WHERE "+" AND ".join(where)) if where else ""
        sql = f"SELECT * FROM procedures {where_sql} ORDER BY id DESC;"
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()

    def by_id(self, pid: int) -> Optional[Dict[str, Any]]:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM procedures WHERE id=%s;", (pid,))
            return cur.fetchone()

    def create(self, data: Dict[str, Any]) -> int:
        sql = """
            INSERT INTO procedures (tuss_code, name, charge_unit, grp, internal_code, active, valor_sus)
            VALUES (LOWER(%(tuss_code)s), %(name)s, %(charge_unit)s,
                    NULLIF(%(grp)s,''), NULLIF(%(internal_code)s,''),
                    COALESCE(%(active)s, TRUE),
                    NULLIF(%(valor_sus)s,'')::numeric)
            RETURNING id;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            return cur.fetchone()[0]

    def update(self, pid: int, data: Dict[str, Any]) -> None:
        sql = """
            UPDATE procedures SET
                tuss_code=LOWER(%(tuss_code)s),
                name=%(name)s,
                charge_unit=%(charge_unit)s,
                grp=NULLIF(%(grp)s,''),
                internal_code=NULLIF(%(internal_code)s,''),
                active=COALESCE(%(active)s, TRUE),
                valor_sus=NULLIF(%(valor_sus)s,'')::numeric
            WHERE id=%(id)s;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, {**data, 'id': pid})

    def delete(self, pid: int) -> bool:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM procedures WHERE id=%s RETURNING id;", (pid,))
            return bool(cur.fetchone())
