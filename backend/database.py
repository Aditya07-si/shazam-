import sqlite3
import os
from typing import List, Dict, Any, Optional

class Database:
    def __init__(self, db_path: str = "app/data/db/shazam.db"):
        self.db_path = db_path
        # Ensure directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self.create_tables()
    
    def get_connection(self):
        return self.conn
    
    def create_tables(self):
        with self.conn:
            # Tracks table
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                artist TEXT,
                duration INT
            )
            """)

            # Fingerprints table
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS fingerprints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                track_id INT,
                fp TEXT
            )
            """)

            # Index for faster lookup by track_id
            self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_track_id
            ON fingerprints(track_id)
            """)

    def get_song_count(self):
        """Return how many songs are stored in the DB"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tracks")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def insert_song(self, title, artist, duration):
        """Insert a new song into the tracks table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tracks (title, artist, duration) VALUES (?, ?, ?)",
            (title, artist, duration),
        )
        song_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return song_id

    def fetch_tracks(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id, title, artist, duration FROM tracks")
            return cur.fetchall()

    def fetch_fingerprints(self):
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            cur.execute("SELECT track_id, fp FROM fingerprints")
            return cur.fetchall()
