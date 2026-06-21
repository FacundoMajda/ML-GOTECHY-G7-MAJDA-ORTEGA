# src/repositories/db.py
import psycopg2
from psycopg2 import pool

from src.config.settings import NEON_DB_URL

_connection_pool: pool.SimpleConnectionPool | None = None


def get_connection():
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = psycopg2.pool.SimpleConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=NEON_DB_URL,
        )
    return _connection_pool.getconn()


def release_connection(conn):
    global _connection_pool
    if _connection_pool:
        _connection_pool.putconn(conn)


def execute_query(query: str, params: tuple | None = None, fetch: str = "all"):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()
            if fetch == "one":
                return cur.fetchone()
            elif fetch == "all":
                return cur.fetchall()
            return None
    finally:
        release_connection(conn)
