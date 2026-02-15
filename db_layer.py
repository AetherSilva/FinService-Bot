import sqlite3
import hashlib
import time
from typing import Optional, Dict, List, Tuple
from config_schema import ServiceType, config_manager
from templates import OfferData

DB_PATH = "fin_referrals.db"

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self.init_db()

    def connect(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def init_db(self):
        con = self.connect()
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS offers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                fingerprint TEXT UNIQUE NOT NULL,
                service_type TEXT NOT NULL,
                provider TEXT NOT NULL,
                title_en TEXT NOT NULL,
                title_hi TEXT,
                title_gu TEXT,
                description_en TEXT,
                description_hi TEXT,
                description_gu TEXT,
                referral_link TEXT NOT NULL,
                validity TEXT,
                terms TEXT,
                status TEXT NOT NULL,
                channel_id TEXT NOT NULL,
                created_at INTEGER NOT NULL,
                posted_at INTEGER,
                rotation_index INTEGER DEFAULT 0,
                metadata TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                blocked BOOLEAN DEFAULT 0,
                joined_at INTEGER NOT NULL
            )
        """)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_service_status ON offers(service_type, status, created_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_fingerprint ON offers(fingerprint)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_channel_status ON offers(channel_id, status)")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS posting_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                offer_id INTEGER NOT NULL,
                channel_id TEXT NOT NULL,
                posted_at INTEGER NOT NULL,
                success BOOLEAN NOT NULL,
                error_message TEXT,
                FOREIGN KEY (offer_id) REFERENCES offers(id)
            )
        """)
        con.commit()
        con.close()

    def register_user(self, user_id: int, username: str):
        con = self.connect()
        cur = con.cursor()
        cur.execute("INSERT OR IGNORE INTO users (user_id, username, joined_at) VALUES (?, ?, ?)", (user_id, username, int(time.time())))
        con.commit()
        con.close()

    def is_user_blocked(self, user_id: int) -> bool:
        con = self.connect()
        cur = con.cursor()
        cur.execute("SELECT blocked FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        con.close()
        return bool(row[0]) if row else False

    def set_user_block_status(self, user_id: int, blocked: bool):
        con = self.connect()
        cur = con.cursor()
        cur.execute("UPDATE users SET blocked = ? WHERE user_id = ?", (int(blocked), user_id))
        con.commit()
        con.close()

    def _normalize_url(self, url: str) -> str:
        return url.split("?")[0].split("#")[0].lower().strip()

    def _make_fingerprint(self, service_type: str, provider: str, url: str) -> str:
        normalized_url = self._normalize_url(url)
        raw = f"{service_type.lower()}|{provider.lower()}|{normalized_url}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def insert_offer(self, offer: OfferData) -> Tuple[bool, Optional[str]]:
        try:
            service_type = ServiceType(offer.service_type)
            channel_id = config_manager.get_channel_for_service(service_type)
        except ValueError as e:
            return False, str(e)
        fingerprint = self._make_fingerprint(offer.service_type, offer.provider, offer.referral_link)
        con = self.connect()
        cur = con.cursor()
        try:
            cur.execute("""
                INSERT INTO offers (
                    fingerprint, service_type, provider, title_en, title_hi, title_gu,
                    description_en, description_hi, description_gu, referral_link, validity, terms,
                    status, channel_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'queued', ?, ?)
            """, (fingerprint, offer.service_type, offer.provider, offer.title_en, offer.title_hi, offer.title_gu,
                offer.description_en, offer.description_hi, offer.description_gu, offer.referral_link,
                offer.validity, offer.terms, channel_id, int(time.time())))
            con.commit()
            return True, f"Queued for {channel_id}"
        except sqlite3.IntegrityError:
            return False, "Duplicate offer"
        finally:
            con.close()

    def next_queued_by_service(self, service_type: ServiceType) -> Optional[Tuple]:
        con = self.connect()
        cur = con.cursor()
        cur.execute("SELECT id, service_type, provider, title_en, title_hi, title_gu, description_en, description_hi, description_gu, referral_link, validity, terms, channel_id, rotation_index FROM offers WHERE service_type = ? AND status = 'queued' ORDER BY created_at ASC LIMIT 1", (service_type.value,))
        row = cur.fetchone()
        con.close()
        return row

    def next_queued_by_channel(self, channel_id: str) -> Optional[Tuple]:
        con = self.connect()
        cur = con.cursor()
        cur.execute("SELECT id, service_type, provider, title_en, title_hi, title_gu, description_en, description_hi, description_gu, referral_link, validity, terms, channel_id, rotation_index FROM offers WHERE channel_id = ? AND status = 'queued' ORDER BY created_at ASC LIMIT 1", (channel_id,))
        row = cur.fetchone()
        con.close()
        return row

    def mark_posted(self, offer_id: int, success: bool = True, error_message: Optional[str] = None):
        con = self.connect()
        cur = con.cursor()
        cur.execute("UPDATE offers SET status = ?, posted_at = ? WHERE id = ?", ("posted" if success else "failed", int(time.time()), offer_id))
        cur.execute("SELECT channel_id FROM offers WHERE id = ?", (offer_id,))
        channel_id = cur.fetchone()[0]
        cur.execute("INSERT INTO posting_history (offer_id, channel_id, posted_at, success, error_message) VALUES (?, ?, ?, ?, ?)", (offer_id, channel_id, int(time.time()), success, error_message))
        if success:
            cur.execute("UPDATE offers SET rotation_index = rotation_index + 1 WHERE id = ?", (offer_id,))
        con.commit()
        con.close()

    def get_stats(self) -> Dict[str, Dict[str, int]]:
        con = self.connect()
        cur = con.cursor()
        stats = {}
        for service_type in ServiceType:
            cur.execute("SELECT COUNT(CASE WHEN status = 'queued' THEN 1 END), COUNT(CASE WHEN status = 'posted' THEN 1 END), COUNT(CASE WHEN status = 'failed' THEN 1 END) FROM offers WHERE service_type = ?", (service_type.value,))
            row = cur.fetchone()
            stats[service_type.value] = {"queued": row[0] or 0, "posted": row[1] or 0, "failed": row[2] or 0}
        con.close()
        return stats

db_manager = DatabaseManager()
