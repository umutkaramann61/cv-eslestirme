"""Veritabanı katmanı.

- DATABASE_URL ortam değişkeni varsa PostgreSQL (ör. Neon ücretsiz) kullanılır.
- Yoksa yerel SQLite dosyası (data/ilanlar.db) kullanılır.

İlan durumu (durum): 'bekliyor' (işletme gönderdi, onay bekliyor), 'yayinda', 'pasif'.
"""
import json
import os
import sqlite3
from datetime import date

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
DATA_DIR = os.environ.get("DATA_DIR", os.path.join(BASE_DIR, "data"))
SQLITE_PATH = os.path.join(DATA_DIR, "ilanlar.db")
TABLE = "isletme_ilanlari"

# (alan adı, liste mi?)
FIELDS = [
    ("firma", False), ("iletisim", False), ("baslik", False), ("calisma_turu", False),
    ("il", False), ("ilce", False), ("sektor", False), ("mezuniyet_alanlari", True),
    ("uzmanliklar", True), ("robot_markalari", True), ("min_deneyim", False),
    ("surucu_belgesi", False), ("ilan_detayi", False), ("basvuru", False), ("son_tarih", False),
    ("durum", False), ("instagram", False),
]
NAMES = [f for f, _ in FIELDS]
DURUMLAR = ("bekliyor", "yayinda", "pasif")


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
    cols = ",\n".join(
        f"{n} INTEGER DEFAULT 0" if n in ("min_deneyim", "surucu_belgesi") else f"{n} TEXT DEFAULT ''"
        for n in NAMES
    )
    _run(f"CREATE TABLE IF NOT EXISTS {TABLE} (id {id_col}, {cols}, olusturma TEXT DEFAULT '')")
    # Sonradan eklenen sütunları mevcut tabloya ekle (veri kaybı olmadan)
    if _is_pg():
        mevcut = {r["column_name"] for r in _run(
            "SELECT column_name FROM information_schema.columns WHERE table_name = ?", (TABLE,), fetch="all")}
    else:
        mevcut = {r["name"] for r in _run(f"PRAGMA table_info({TABLE})", fetch="all")}
    for n in NAMES:
        if n not in mevcut:
            tip = "INTEGER DEFAULT 0" if n in ("min_deneyim", "surucu_belgesi") else "TEXT DEFAULT ''"
            _run(f"ALTER TABLE {TABLE} ADD COLUMN {n} {tip}")
    if seed_file and os.path.exists(seed_file):
        row = _run(f"SELECT COUNT(*) AS n FROM {TABLE}", fetch="one")
        if row and int(row["n"]) == 0:
            with open(seed_file, encoding="utf-8") as f:
                for ilan in json.load(f):
                    add_job(ilan)


def _to_list(v):
    if isinstance(v, (list, tuple)):
        return [str(x).strip() for x in v if str(x).strip()]
    return [s.strip() for s in str(v or "").split("|") if s.strip()]


def _clean(data):
    """Form (MultiDict) veya dict'ten veritabanı satırı üret."""
    getlist = getattr(data, "getlist", None)
    out = {}
    for name, is_list in FIELDS:
        if is_list:
            vals = getlist(name) if getlist else data.get(name, [])
            out[name] = "|".join(_to_list(vals))
        elif name in ("min_deneyim",):
            try:
                out[name] = max(0, int(data.get(name) or 0))
            except ValueError:
                out[name] = 0
        elif name == "surucu_belgesi":
            out[name] = 1 if data.get(name) in (1, True, "1", "on", "evet") else 0
        else:
            out[name] = str(data.get(name) or "").strip()
    if out["durum"] not in DURUMLAR:
        out["durum"] = "bekliyor"
    return out


def _decode(row):
    if not row:
        return row
    for name, is_list in FIELDS:
        if is_list:
            row[name] = _to_list(row.get(name))
    return row


def add_job(data, durum=None):
    d = _clean(data)
    if durum:
        d["durum"] = durum
    cols = ", ".join(NAMES + ["olusturma"])
    marks = ", ".join(["?"] * (len(NAMES) + 1))
    _run(f"INSERT INTO {TABLE} ({cols}) VALUES ({marks})",
         [d[n] for n in NAMES] + [date.today().isoformat()])


def update_job(job_id, data):
    d = _clean(data)
    sets = ", ".join(f"{n} = ?" for n in NAMES)
    _run(f"UPDATE {TABLE} SET {sets} WHERE id = ?", [d[n] for n in NAMES] + [job_id])


def set_status(job_id, durum):
    if durum in DURUMLAR:
        _run(f"UPDATE {TABLE} SET durum = ? WHERE id = ?", (durum, job_id))


def delete_job(job_id):
    _run(f"DELETE FROM {TABLE} WHERE id = ?", (job_id,))


def get_job(job_id):
    return _decode(_run(f"SELECT * FROM {TABLE} WHERE id = ?", (job_id,), fetch="one"))


def list_jobs(only_published=True):
    sql = f"SELECT * FROM {TABLE}"
    if only_published:
        sql += " WHERE durum = 'yayinda'"
    sql += " ORDER BY id DESC"
    jobs = [_decode(j) for j in _run(sql, fetch="all")]
    if only_published:
        today = date.today().isoformat()
        jobs = [j for j in jobs if not j.get("son_tarih") or j["son_tarih"] >= today]
    return jobs


def export_jobs():
    return [{n: j.get(n) for n in NAMES} for j in list_jobs(only_published=False)]
