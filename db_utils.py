# db_utils.py
import sqlite3
import hashlib
import datetime
from pathlib import Path

DB_PATH = Path("news_db.sqlite")

def get_conn():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), timeout=30)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    conn = get_conn()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS posted_news (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        hash TEXT UNIQUE,
        title TEXT,
        url TEXT,
        posted_at TEXT
    )
    """)
    conn.commit()
    conn.close()

def make_hash(title: str, url: str) -> str:
    h = hashlib.sha256()
    h.update((title or "").strip().encode("utf-8"))
    h.update(b"||")
    h.update((url or "").strip().encode("utf-8"))
    return h.hexdigest()

def already_posted(title: str, url: str) -> bool:
    init_db()
    h = make_hash(title, url)
    conn = get_conn()
    cur = conn.execute("SELECT 1 FROM posted_news WHERE hash = ? LIMIT 1", (h,))
    found = cur.fetchone() is not None
    conn.close()
    return found

def mark_posted(title: str, url: str):
    init_db()
    h = make_hash(title, url)
    now = datetime.datetime.utcnow().isoformat() + "Z"
    conn = get_conn()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO posted_news (hash, title, url, posted_at) VALUES (?, ?, ?, ?)",
            (h, title, url, now)
        )
        conn.commit()
    finally:
        conn.close()