# app/db.py
from contextlib import contextmanager
from psycopg2.pool import SimpleConnectionPool
import psycopg2
import psycopg2.extras

_pool: SimpleConnectionPool | None = None

def init_db(db_cfg: dict) -> None:
    """
    Inicializa o pool de conexões. Deve ser chamado uma vez no startup
    (já é feito em create_app()).

    db_cfg vem do Config.DB_CFG e pode conter:
      host, port, dbname, user, password, sslmode, connect_timeout...
    """
    global _pool
    if _pool is not None:
        return  # já inicializado

    # Pool com 1..10 conexões (ajuste se necessário)
    _pool = SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        cursor_factory=psycopg2.extras.DictCursor,  # rows acessíveis por nome
        **db_cfg,
    )

def _ensure_pool() -> None:
    if _pool is None:
        raise RuntimeError(
            "DB pool ainda não inicializado. "
            "Garanta que init_db(app.config['DB_CFG']) foi chamado no create_app()."
        )

@contextmanager
def get_conn():
    """
    Uso:
      with get_conn() as conn, conn.cursor() as cur:
          cur.execute("SELECT 1")
          ...
    Faz commit no sucesso e rollback em caso de exceção.
    """
    _ensure_pool()
    conn = _pool.getconn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        _pool.putconn(conn)

@contextmanager
def get_cursor():
    """
    Atalho opcional se preferir:
      with get_cursor() as cur:
          cur.execute("SELECT 1")
          row = cur.fetchone()
    """
    with get_conn() as conn:
        with conn.cursor() as cur:
            yield cur

def close_pool() -> None:
    """
    Fecha todas as conexões do pool (útil em scripts/CLI/tests).
    No Render normalmente não é necessário chamar manualmente.
    """
    global _pool
    if _pool is not None:
        _pool.closeall()
        _pool = None
