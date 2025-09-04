from contextlib import contextmanager
from psycopg2.pool import SimpleConnectionPool
import psycopg2.extras

_pool = None

def init_db(db_cfg: dict):
    global _pool
    if _pool is None:
        _pool = SimpleConnectionPool(
            1, 10,
            **db_cfg,
            cursor_factory=psycopg2.extras.DictCursor
        )

@contextmanager
def get_conn():
    conn = _pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)
