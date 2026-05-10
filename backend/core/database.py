import sqlite3
import json
import os
from datetime import datetime
from core.config import settings

DB_PATH = os.path.join(os.path.dirname(settings.DATA_DIR), "osint_hunter.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS search_queries (
            id TEXT PRIMARY KEY,
            phone_number TEXT NOT NULL,
            normalized_phone TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT,
            updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS search_results (
            id TEXT PRIMARY KEY,
            query_id TEXT NOT NULL,
            source TEXT NOT NULL,
            raw_data TEXT,
            processed_data TEXT,
            confidence REAL DEFAULT 0.5,
            created_at TEXT,
            FOREIGN KEY(query_id) REFERENCES search_queries(id)
        );
        CREATE INDEX IF NOT EXISTS idx_phone ON search_queries(phone_number);
        CREATE INDEX IF NOT EXISTS idx_query_id ON search_results(query_id);
    """)
    conn.commit()
    conn.close()

init_db()
print("[DB] SQLite база инициализирована")
