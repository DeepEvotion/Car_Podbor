"""Local SQLite storage for catalog, photos and shared garages."""

import json
import os
import sqlite3
from contextlib import closing, contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class Database:
    def __init__(self, path=None):
        self.path = path or os.getenv("SQLITE_PATH") or ROOT / "data" / "carmatch.sqlite3"

    @contextmanager
    def connect(self):
        with closing(sqlite3.connect(self.path)) as connection:
            connection.row_factory = sqlite3.Row
            with connection:
                yield connection

    def init(self):
        with self.connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS cars (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS photo_cache (
                    car_id TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS shares (
                    token TEXT PRIMARY KEY, revoke_key TEXT NOT NULL, items TEXT NOT NULL
                );
            """)
            cars = json.loads((ROOT / "data" / "catalog.json").read_text(encoding="utf-8"))
            from .catalog_extra import build_catalog
            cars.extend(build_catalog())
            db.executemany("INSERT OR IGNORE INTO cars VALUES (?, ?)",
                           [(car["id"], json.dumps(car)) for car in cars])

    def catalog(self):
        with self.connect() as db:
            return [json.loads(row["payload"]) for row in db.execute("SELECT payload FROM cars ORDER BY rowid")]

    def photo(self, car_id):
        with self.connect() as db:
            row = db.execute("SELECT payload FROM photo_cache WHERE car_id = ? AND updated_at > datetime('now', '-7 days')",
                             (car_id,)).fetchone()
            if not row:
                return None
            payload = json.loads(row["payload"])
            # Invalidate the previous Wikimedia cache after switching provider.
            return payload if "openverse.org" in payload.get("source", "") or payload.get("source") == "https://openverse.org/" else None

    def save_photo(self, car_id, photo):
        with self.connect() as db:
            db.execute("INSERT OR REPLACE INTO photo_cache VALUES (?, ?, datetime('now'))", (car_id, json.dumps(photo)))

    def create_share(self, token, revoke_key, items):
        with self.connect() as db:
            db.execute("INSERT INTO shares VALUES (?, ?, ?)", (token, revoke_key, json.dumps(items)))

    def share(self, token):
        with self.connect() as db:
            row = db.execute("SELECT items FROM shares WHERE token = ?", (token,)).fetchone()
            return {"items": json.loads(row["items"])} if row else None

    def revoke_share(self, token, revoke_key):
        with self.connect() as db:
            return db.execute("DELETE FROM shares WHERE token = ? AND revoke_key = ?", (token, revoke_key)).rowcount == 1
