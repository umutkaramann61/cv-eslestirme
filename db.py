"""Veritabanı katmanı.

- DATABASE_URL ortam değişkeni varsa PostgreSQL (ör. Neon ücretsiz) kullanılır.
- Yoksa yerel SQLite dosyası (data/ilanlar.db) kullanılır.
"""
import json
import os
import sqlite3
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE_DIR, "data"))
SQLITE_PATH = os.path.join(DATA_DIR, "ilanlar.db")

FIELDS = [
    "baslik", "firma", "konum", "calisma_turu", "alan",
    "gerekli_beceriler", "tercih_beceriler", "aciklama",
    "basvuru", "son_tarih", "aktif",
]


def _is_pg():
    return DATABASE_URL.startswith(("postgres://", "postgresql://"))


def _connect():
    if _is_pg():
        import psycopg
        from psycopg.rows import dict_row
        return psycopg.connect(DATABASE_URL, row_factory=dict_row)
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _q(sql):
    """SQLite '?' yer tutucularını PostgreSQL için '%s' yap."""
    return sql.replace("?", "%s") if _is_pg() else sql


def _run(sql, params=(), fetch=None):
    conn = _connect()
    try:
        cur = conn.cursor()
        cur.execute(_q(sql), params)
        result = None
        if fetch == "all":
            result = [dict(r) for r in cur.fetchall()]
        elif fetch == "one":
            row = cur.fetchone()
            result = dict(row) if row else None
        conn.commit()
        return result
    finally:
        conn.close()


def init_db(seed_file=None):
    id_col = "SERIAL PRIMARY KEY" if _is_pg() else "INTEGER PRIMARY KEY AUTOINCREMENT"
    _run(f"""
        CREATE TABLE IF NOT EXISTS ilanlar (
            id {id_col},
            baslik TEXT NOT NULL,
            firma TEXT NOT NULL,
            konum TEXT DEFAULT '',
            calisma_turu TEXT DEFAULT '',
            alan TEXT DEFAULT '',
            gerekli_beceriler TEXT DEFAULT '',
            tercih_beceriler TEXT DEFAULT '',
            aciklama TEXT DEFAULT '',
            basvuru TEXT DEFAULT '',
            son_tarih TEXT DEFAULT '',
            aktif INTEGER DEFAULT 1,
            olusturma TEXT DEFAULT ''
        )
    """)
    if seed_file and os.path.exists(seed_file):
        row = _run("SELECT COUNT(*) AS n FROM ilanlar", fetch="one")
        if row and int(row["n"]) == 0:
            with open(seed_file, encoding="utf-8") as f:
                for ilan in json.load(f):
                    add_job(ilan)


def _clean(data):
    out = {}
    for k in FIELDS:
        v = data.get(k, "")
        if k == "aktif":
            out[k] = 1 if v in (1, True, "1", "on", "true", "evet") else 0
        else:
            out[k] = str(v or "").strip()
    return out


def add_job(data):
    d = _clean(data)
    if "aktif" not in data:
        d["aktif"] = 1
    cols = ", ".join(FIELDS + ["olusturma"])
    marks = ", ".join(["?"] * (len(FIELDS) + 1))
    _run(f"INSERT INTO ilanlar ({cols}) VALUES ({marks})",
         [d[k] for k in FIELDS] + [date.today().isoformat()])


def update_job(job_id, data):
    d = _clean(data)
    sets = ", ".join(f"{k} = ?" for k in FIELDS)
    _run(f"UPDATE ilanlar SET {sets} WHERE id = ?", [d[k] for k in FIELDS] + [job_id])


def delete_job(job_id):
    _run("DELETE FROM ilanlar WHERE id = ?", (job_id,))


def get_job(job_id):
    return _run("SELECT * FROM ilanlar WHERE id = ?", (job_id,), fetch="one")


def list_jobs(only_active=True):
    sql = "SELECT * FROM ilanlar"
    if only_active:
        sql += " WHERE aktif = 1"
    sql += " ORDER BY id DESC"
    jobs = _run(sql, fetch="all")
    if only_active:
        today = date.today().isoformat()
        jobs = [j for j in jobs if not j.get("son_tarih") or j["son_tarih"] >= today]
    return jobs


def export_jobs():
    jobs = list_jobs(only_active=False)
    return [{k: j.get(k) for k in FIELDS} for j in jobs]
