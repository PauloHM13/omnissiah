# app/config.py
import os
from urllib.parse import urlparse, unquote
from dotenv import load_dotenv

load_dotenv()

def _parse_database_url(db_url: str) -> dict:
    """
    Converte DATABASE_URL (postgresql://user:pass@host:port/db?sslmode=require)
    no dict que o psycopg2 espera.
    """
    u = urlparse(db_url)
    return {
        "host": u.hostname,
        "port": u.port or 5432,
        "dbname": u.path.lstrip("/"),
        "user": unquote(u.username) if u.username else None,
        "password": unquote(u.password) if u.password else None,
        # garante TLS no Neon
        "sslmode": "require",
    }

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-change-me")

    # Tente usar DATABASE_URL primeiro
    _db_url = os.getenv("DATABASE_URL")

    if _db_url:
        DB_CFG = _parse_database_url(_db_url)
    else:
        # fallback por variáveis separadas (ou defaults)
        DB_CFG = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "dbname": os.getenv("DB_NAME", "postgres"),
            "user": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", ""),
            "sslmode": os.getenv("DB_SSLMODE", ""),  # vazio em dev; 'require' em prod
        }

    # uploads de despesas
    EXPENSES_UPLOAD_DIR = os.getenv("EXPENSES_UPLOAD_DIR", "./uploads")
    ALLOWED_RECEIPT_EXT = set((os.getenv("ALLOWED_RECEIPT_EXT", "pdf,jpg,jpeg,png")).split(","))
