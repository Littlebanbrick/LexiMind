"""
database.py

SQLite database operations module.

Managing three tables:
- words: Records the query count of words/phrases
- history: Records all user interaction history
- daily_articles: Stores the generated daily articles
"""

import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from config import config

# The path of the database file, defined in config.py
DB_PATH = config.DATABASE_PATH

# Ensuring the directory for the database exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def get_db_connection():
    """
    Create and return a db connection with foreign keys enabled and row factory set.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Enable dict-like access to rows
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Initialize the db by creating necessary tables if they don't exist"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. words table: Records query counts for words/phrases
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT UNIQUE NOT NULL,       -- Word or phrase text
                query_count INTEGER DEFAULT 1,   -- Query count
                last_queried TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. history table: Records all user interactions (input, command type, LLM result, timestamp)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_input TEXT NOT NULL,        -- Original user input
                command_type TEXT NOT NULL,      -- Command type
                result TEXT,                     -- LLM result (may be long)
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 3. daily_articles table: Stores the generated daily articles
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,           -- Article content (with source line)
                generated_at DATE DEFAULT CURRENT_DATE
            )
        """)

        conn.commit()


# ---------- Words table operations ----------
def record_word_query(term: str) -> None:
    """
    Record a word/phrase query. If it exists, increment the count; otherwise, insert a new record.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO words (term, query_count, last_queried)
            VALUES (?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(term) DO UPDATE SET
                query_count = query_count + 1,
                last_queried = CURRENT_TIMESTAMP
        """, (term,))
        conn.commit()


def get_word_stats(term: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """
    Get word statistical information.
    If term is not specified, return the top 'limit' words by query count.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if term:
            cursor.execute("SELECT * FROM words WHERE term = ?", (term,))
        else:
            cursor.execute("""
                SELECT * FROM words
                ORDER BY query_count DESC, last_queried DESC
                LIMIT ?
            """, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# ---------- History table operations ----------
def insert_history(user_input, command_type, result_text, db_path="backend/data/leximind.db"):
    """Insert a history record and prune old ones if exceeding limit."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    timestamp = datetime.now().isoformat()

    cursor.execute(
        "INSERT INTO history (timestamp, user_input, command_type, result) VALUES (?, ?, ?, ?)",
        (timestamp, user_input, command_type, result_text)
    )
    conn.commit()

    # Prune old records if total exceeds MAX_HISTORY_RECORDS
    cursor.execute("SELECT COUNT(*) FROM history")
    total = cursor.fetchone()[0]
    max_records = config.MAX_HISTORY_RECORDS

    if total > max_records:
        # Delete the oldest records: delete rows where id NOT IN (the newest max_records)
        cursor.execute("""
            DELETE FROM history
            WHERE id NOT IN (
                SELECT id FROM history
                ORDER BY timestamp DESC
                LIMIT ?
            )
        """, (max_records,))
        conn.commit()

    conn.close()

def get_recent_history(limit: int = 20) -> List[Dict[str, Any]]:
    """Get the most recent history records (ordered by time)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM history
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# ---------- Daily Articles table operations ----------
def insert_daily_article(content: str) -> int:
    """Save a daily article and return its ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO daily_articles (content)
            VALUES (?)
        """, (content,))
        conn.commit()
        return cursor.lastrowid


def get_today_article() -> Optional[Dict[str, Any]]:
    """Get today article if exists, otherwise return None"""
    today = datetime.now().strftime('%Y-%m-%d')
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM daily_articles
            WHERE DATE(generated_at) = ?
            ORDER BY generated_at DESC
            LIMIT 1
        """, (today,))
        row = cursor.fetchone()
        return dict(row) if row else None


def get_latest_article() -> Optional[Dict[str, Any]]:
    """Get the latest article regardless of date"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM daily_articles
            ORDER BY generated_at DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        return dict(row) if row else None


# When the module is imported, ensure the database is initialized
init_db()