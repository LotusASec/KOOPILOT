import os
import psycopg2
import psycopg2.extras


def get_connection():
    url = os.environ.get("DATABASE_URL", "").strip()

    if not url:
        raise RuntimeError("DATABASE_URL env değişkeni tanımlı değil.")

    return psycopg2.connect(url, cursor_factory=psycopg2.extras.RealDictCursor)


def query(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            return cur.fetchall()
    finally:
        conn.close()


def execute(sql, params=None):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, params)
        conn.commit()
    finally:
        conn.close()
