# app/repositories/users.py
from typing import Optional, List, Dict, Any
from ..db import get_conn

class UserRepository:
    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        sql = """
            SELECT id, username, role, is_active, must_change_password
              FROM users
             WHERE LOWER(username) = LOWER(%s)
               AND password_hash = crypt(%s, password_hash)
             LIMIT 1;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, (username, password))
            return cur.fetchone()

    def by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE id=%s;", (user_id,))
            return cur.fetchone()

    def list(self) -> List[Dict[str, Any]]:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, username, email, role, is_active, created_at,
                       must_change_password,
                       phone, cep, street, number, complement, district, city, state
                  FROM users
                 ORDER BY id DESC;
                """
            )
            return cur.fetchall()

    def create(self, data: Dict[str, Any]) -> int:
        sql = """
            INSERT INTO users (
              username, email, password_hash, role, is_active, must_change_password,
              phone, cep, street, number, complement, district, city, state
            )
            VALUES (
              LOWER(%(username)s), LOWER(%(email)s),
              crypt(%(password)s, gen_salt('bf', 12)),
              %(role)s, TRUE, TRUE,
              NULLIF(%(phone)s,''), NULLIF(%(cep)s,''), NULLIF(%(street)s,''),
              NULLIF(%(number)s,''), NULLIF(%(complement)s,''), NULLIF(%(district)s,''),
              NULLIF(%(city)s,''), NULLIF(%(state)s,'')
            )
            RETURNING id;
        """
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, data)
            return cur.fetchone()["id"]

    def update(self, user_id: int, fields: Dict[str, Any]) -> None:
        sql = """
            UPDATE users
               SET username=LOWER(%(username)s),
                   email=LOWER(%(email)s),
                   role=%(role)s,
                   is_active=%(is_active)s,
                   phone=NULLIF(%(phone)s,''),
                   cep=NULLIF(%(cep)s,''),
                   street=NULLIF(%(street)s,''),
                   number=NULLIF(%(number)s,''),
                   complement=NULLIF(%(complement)s,''),
                   district=NULLIF(%(district)s,''),
                   city=NULLIF(%(city)s,''),
                   state=NULLIF(%(state)s,'')
             WHERE id=%(id)s;
        """
        payload = {**fields, "id": user_id}
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(sql, payload)

    def delete(self, user_id: int) -> bool:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM users WHERE id=%s RETURNING id;", (user_id,))
            return bool(cur.fetchone())

    def reset_password(self, user_id: int, new_password: str) -> Optional[str]:
        with get_conn() as conn, conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                   SET password_hash = crypt(%s, gen_salt('bf', 12)),
                       must_change_password = TRUE
                 WHERE id = %s
             RETURNING username;
                """,
                (new_password, user_id),
            )
            row = cur.fetchone()
            return row["username"] if row else None

    def change_password(self, user_id: int, current: str, new_password: str) -> bool:
        with get_conn() as conn, conn.cursor() as cur:
            # valida senha atual
            cur.execute(
                """
                SELECT 1 FROM users
                 WHERE id=%s AND password_hash = crypt(%s, password_hash);
                """,
                (user_id, current),
            )
            if not cur.fetchone():
                return False
            # aplica nova senha e libera flag
            cur.execute(
                """
                UPDATE users
                   SET password_hash = crypt(%s, gen_salt('bf', 12)),
                       must_change_password = FALSE
                 WHERE id = %s;
                """,
                (new_password, user_id),
            )
            return True
