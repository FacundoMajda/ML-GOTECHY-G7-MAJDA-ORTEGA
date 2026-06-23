# src/repositories/db.py
import traceback

import psycopg2
from psycopg2 import pool

from src.config.settings import NEON_DB_URL

_connection_pool: pool.ThreadedConnectionPool | None = None


def get_connection():
    global _connection_pool
    if _connection_pool is None:
        print(f"[DEBUG] db.get_connection: creating connection pool", flush=True)
        _connection_pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            dsn=NEON_DB_URL,
        )
    conn = _connection_pool.getconn()
    print(f"[DEBUG] db.get_connection: got connection {id(conn)}", flush=True)
    return conn


def release_connection(conn):
    global _connection_pool
    if _connection_pool:
        _connection_pool.putconn(conn)
        print(f"[DEBUG] db.release_connection: released connection {id(conn)}", flush=True)


def execute_query(query: str, params: tuple | None = None, fetch: str = "all"):
    query_preview = query[:80].replace("\n", " ")
    print(f"[DEBUG] db.execute_query: ENTRY fetch={fetch} query={query_preview}... params={params}", flush=True)
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()
            has_result_set = cur.description is not None
            if fetch == "one":
                if not has_result_set:
                    print(f"[DEBUG] db.execute_query: fetch=one but query returned no result set", flush=True)
                    return None
                result = cur.fetchone()
                print(f"[DEBUG] db.execute_query: fetch=one result={result}", flush=True)
                return result
            elif fetch == "all":
                if not has_result_set:
                    print(f"[DEBUG] db.execute_query: fetch=all but query returned no result set", flush=True)
                    return []
                result = cur.fetchall()
                print(f"[DEBUG] db.execute_query: fetch=all rows={len(result) if result else 0}", flush=True)
                return result
            print(f"[DEBUG] db.execute_query: fetch=None, no result", flush=True)
            return None
    except Exception as exc:
        print(f"[DEBUG] db.execute_query: EXCEPTION {exc}", flush=True)
        traceback.print_exc()
        raise
    finally:
        release_connection(conn)
