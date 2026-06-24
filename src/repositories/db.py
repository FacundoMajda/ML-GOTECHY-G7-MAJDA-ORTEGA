# src/repositories/db.py
import threading
import traceback

import psycopg2
from psycopg2 import extras, pool

from src.config.settings import NEON_DB_URL

_connection_pool: pool.ThreadedConnectionPool | None = None
_pool_init_lock = threading.Lock()


def get_connection():
    global _connection_pool
    if _connection_pool is None:
        with _pool_init_lock:
            if _connection_pool is None:
                print("[DEBUG] db.get_connection: creating connection pool", flush=True)
                _connection_pool = psycopg2.pool.ThreadedConnectionPool(
                    minconn=2,
                    maxconn=20,
                    dsn=NEON_DB_URL,
                )
    conn = _connection_pool.getconn()
    return conn


def release_connection(conn):
    global _connection_pool
    if _connection_pool:
        _connection_pool.putconn(conn)


def execute_query(query: str, params=None, fetch: str = "all"):
    query_preview = query[:80].replace("\n", " ")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()
            has_result_set = cur.description is not None
            if fetch == "one":
                if not has_result_set:
                    return None
                return cur.fetchone()
            elif fetch == "all":
                if not has_result_set:
                    return []
                result = cur.fetchall()
                return result
            return None
    except Exception as exc:
        print(f"[DEBUG] db.execute_query: EXCEPTION {exc}", flush=True)
        try:
            conn.rollback()
        except Exception:
            pass
        traceback.print_exc()
        raise
    finally:
        release_connection(conn)


def execute_batch(query: str, params_list: list[tuple], page_size: int = 500) -> None:
    """Batch INSERT/UPDATE — un solo commit para todas las filas.
    ~10-50x más rápido que N execute_query() individuales.
    """
    if not params_list:
        return
    query_preview = query[:80].replace("\n", " ")
    print(f"[DEBUG] db.execute_batch: rows={len(params_list)} query={query_preview}...", flush=True)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            extras.execute_batch(cur, query, params_list, page_size=page_size)
            conn.commit()
    except Exception as exc:
        print(f"[DEBUG] db.execute_batch: EXCEPTION {exc}", flush=True)
        try:
            conn.rollback()
        except Exception:
            pass
        traceback.print_exc()
        raise
    finally:
        release_connection(conn)
