"""
Neon PostgreSQL Database Layer for FinService-Bot
Provides PostgreSQL support via Neon serverless database
Falls back to SQLite if Postgres connection fails
"""

import sqlite3
import hashlib
import time
import asyncio
import logging
from typing import Optional, Dict, List, Tuple
from enum import Enum
from pathlib import Path
import os

logger = logging.getLogger(__name__)

class DatabaseType(Enum):
    SQLITE = "sqlite"
    POSTGRESQL = "postgresql"

class DatabaseManager:
    """Universal database manager supporting SQLite and PostgreSQL"""
    
    def __init__(self, db_type: DatabaseType = DatabaseType.SQLITE, db_path: str = "fin_referrals.db"):
        self.db_type = db_type
        self.db_path = db_path
        self.db_url = os.environ.get("DATABASE_URL")
        
        if db_type == DatabaseType.POSTGRESQL and self.db_url:
            self._init_postgres()
        else:
            self._init_sqlite()
    
    def _init_postgres(self):
        """Initialize PostgreSQL connection"""
        try:
            import psycopg2
            from psycopg2.extras import DictCursor
            self.db_type = DatabaseType.POSTGRESQL
            self.psycopg2 = psycopg2
            logger.info("✓ PostgreSQL database layer initialized")
            self._create_postgres_tables()
        except ImportError:
            logger.warning("⚠ psycopg2 not available, falling back to SQLite")
            self._init_sqlite()
        except Exception as e:
            logger.warning(f"⚠ PostgreSQL connection failed: {e}, using SQLite")
            self._init_sqlite()
    
    def _init_sqlite(self):
        """Initialize SQLite connection"""
        self.db_type = DatabaseType.SQLITE
        self.db_path = os.environ.get("SQLITE_PATH", "fin_referrals.db")
        logger.info(f"✓ SQLite database layer initialized at {self.db_path}")
        self.init_db()
    
    def _get_postgres_connection(self):
        """Get PostgreSQL connection"""
        try:
            import psycopg2
            return psycopg2.connect(self.db_url)
        except Exception as e:
            logger.error(f"❌ PostgreSQL connection error: {e}")
            return None
    
    def _create_postgres_tables(self):
        """Create PostgreSQL tables"""
        try:
            con = self._get_postgres_connection()
            if not con:
                return
            
            cur = con.cursor()
            
            # Drop existing tables if they exist (for fresh setup)
            cur.execute("DROP TABLE IF EXISTS posting_history CASCADE")
            cur.execute("DROP TABLE IF EXISTS offers CASCADE")
            cur.execute("DROP TABLE IF EXISTS users CASCADE")
            
            # Create users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username VARCHAR(255),
                    blocked BOOLEAN DEFAULT FALSE,
                    joined_at BIGINT NOT NULL
                )
            """)
            
            # Create offers table with all fields
            cur.execute("""
                CREATE TABLE IF NOT EXISTS offers (
                    id SERIAL PRIMARY KEY,
                    fingerprint VARCHAR(64) UNIQUE NOT NULL,
                    service_type VARCHAR(50) NOT NULL,
                    provider VARCHAR(255) NOT NULL,
                    title_en TEXT NOT NULL,
                    title_hi TEXT,
                    title_gu TEXT,
                    description_en TEXT,
                    description_hi TEXT,
                    description_gu TEXT,
                    referral_link VARCHAR(500) NOT NULL,
                    validity VARCHAR(100),
                    terms TEXT,
                    status VARCHAR(20) NOT NULL,
                    channel_id VARCHAR(100) NOT NULL,
                    created_at BIGINT NOT NULL,
                    posted_at BIGINT,
                    rotation_index INTEGER DEFAULT 0,
                    metadata TEXT,
                    created_idx BIGINT NOT NULL DEFAULT 0
                )
            """)
            
            # Create indexes
            cur.execute("CREATE INDEX IF NOT EXISTS idx_service_status ON offers(service_type, status, created_at)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_fingerprint ON offers(fingerprint)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_channel_status ON offers(channel_id, status)")
            
            # Create posting_history table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS posting_history (
                    id SERIAL PRIMARY KEY,
                    offer_id INTEGER NOT NULL,
                    channel_id VARCHAR(100) NOT NULL,
                    posted_at BIGINT NOT NULL,
                    success BOOLEAN NOT NULL,
                    error_message TEXT,
                    FOREIGN KEY (offer_id) REFERENCES offers(id)
                )
            """)
            
            con.commit()
            con.close()
            logger.info("✓ PostgreSQL tables created successfully")
        except Exception as e:
            logger.error(f"❌ Failed to create PostgreSQL tables: {e}")
    
    def connect(self):
        """Get database connection"""
        if self.db_type == DatabaseType.POSTGRESQL:
            return self._get_postgres_connection()
        else:
            return sqlite3.connect(self.db_path, check_same_thread=False)
    
    def init_db(self):
        """Initialize SQLite database"""
        if self.db_type != DatabaseType.SQLITE:
            return
        
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
        
        # Create indexes
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
        """Register a new user"""
        try:
            con = self.connect()
            cur = con.cursor()
            
            if self.db_type == DatabaseType.POSTGRESQL:
                cur.execute(
                    "INSERT INTO users (user_id, username, joined_at) VALUES (%s, %s, %s) ON CONFLICT DO NOTHING",
                    (user_id, username, int(time.time()))
                )
            else:
                cur.execute(
                    "INSERT OR IGNORE INTO users (user_id, username, joined_at) VALUES (?, ?, ?)",
                    (user_id, username, int(time.time()))
                )
            
            con.commit()
            con.close()
        except Exception as e:
            logger.error(f"❌ Failed to register user: {e}")
    
    def is_user_blocked(self, user_id: int) -> bool:
        """Check if user is blocked"""
        try:
            con = self.connect()
            cur = con.cursor()
            
            if self.db_type == DatabaseType.POSTGRESQL:
                cur.execute("SELECT blocked FROM users WHERE user_id = %s", (user_id,))
            else:
                cur.execute("SELECT blocked FROM users WHERE user_id = ?", (user_id,))
            
            row = cur.fetchone()
            con.close()
            return bool(row[0]) if row else False
        except Exception as e:
            logger.error(f"❌ Failed to check user block status: {e}")
            return False
    
    def set_user_block_status(self, user_id: int, blocked: bool):
        """Set user block status"""
        try:
            con = self.connect()
            cur = con.cursor()
            
            if self.db_type == DatabaseType.POSTGRESQL:
                cur.execute("UPDATE users SET blocked = %s WHERE user_id = %s", (blocked, user_id))
            else:
                cur.execute("UPDATE users SET blocked = ? WHERE user_id = ?", (int(blocked), user_id))
            
            con.commit()
            con.close()
        except Exception as e:
            logger.error(f"❌ Failed to set user block status: {e}")
    
    def _normalize_url(self, url: str) -> str:
        """Normalize URL for fingerprinting"""
        return url.split("?")[0].split("#")[0].lower().strip()
    
    def _make_fingerprint(self, service_type: str, provider: str, url: str) -> str:
        """Create offer fingerprint"""
        normalized_url = self._normalize_url(url)
        raw = f"{service_type.lower()}|{provider.lower()}|{normalized_url}"
        return hashlib.sha256(raw.encode()).hexdigest()
    
    def insert_offer(self, offer) -> Tuple[bool, Optional[str]]:
        """Insert offer into database"""
        try:
            from config_schema import ServiceType, config_manager
            
            service_type = ServiceType(offer.service_type)
            channel_id = config_manager.get_channel_for_service(service_type)
            fingerprint = self._make_fingerprint(offer.service_type, offer.provider, offer.referral_link)
            
            con = self.connect()
            cur = con.cursor()
            
            try:
                if self.db_type == DatabaseType.POSTGRESQL:
                    cur.execute("""
                        INSERT INTO offers (
                            fingerprint, service_type, provider, title_en, title_hi, title_gu,
                            description_en, description_hi, description_gu, referral_link, validity, terms,
                            status, channel_id, created_at, created_idx
                        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, (fingerprint, offer.service_type, offer.provider, offer.title_en, offer.title_hi, offer.title_gu,
                        offer.description_en, offer.description_hi, offer.description_gu, offer.referral_link,
                        offer.validity, offer.terms, 'queued', channel_id, int(time.time()), int(time.time())))
                else:
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
            except sqlite3.IntegrityError if self.db_type == DatabaseType.SQLITE else Exception as e:
                if "duplicate" in str(e).lower() or "unique" in str(e).lower():
                    return False, "Duplicate offer"
                raise e
            finally:
                con.close()
        except ValueError as e:
            return False, str(e)
        except Exception as e:
            logger.error(f"❌ Failed to insert offer: {e}")
            return False, str(e)
    
    def next_queued_by_service(self, service_type) -> Optional[Tuple]:
        """Get next queued offer by service type"""
        try:
            con = self.connect()
            cur = con.cursor()
            
            if self.db_type == DatabaseType.POSTGRESQL:
                cur.execute(
                    "SELECT id, service_type, provider, title_en, title_hi, title_gu, description_en, description_hi, description_gu, referral_link, validity, terms, channel_id, rotation_index FROM offers WHERE service_type = %s AND status = 'queued' ORDER BY created_at ASC LIMIT 1",
                    (service_type.value,)
                )
            else:
                cur.execute(
                    "SELECT id, service_type, provider, title_en, title_hi, title_gu, description_en, description_hi, description_gu, referral_link, validity, terms, channel_id, rotation_index FROM offers WHERE service_type = ? AND status = 'queued' ORDER BY created_at ASC LIMIT 1",
                    (service_type.value,)
                )
            
            row = cur.fetchone()
            con.close()
            return row
        except Exception as e:
            logger.error(f"❌ Failed to get next queued offer: {e}")
            return None
    
    def next_queued_by_channel(self, channel_id: str) -> Optional[Tuple]:
        """Get next queued offer by channel"""
        try:
            con = self.connect()
            cur = con.cursor()
            
            if self.db_type == DatabaseType.POSTGRESQL:
                cur.execute(
                    "SELECT id, service_type, provider, title_en, title_hi, title_gu, description_en, description_hi, description_gu, referral_link, validity, terms, channel_id, rotation_index FROM offers WHERE channel_id = %s AND status = 'queued' ORDER BY created_at ASC LIMIT 1",
                    (channel_id,)
                )
            else:
                cur.execute(
                    "SELECT id, service_type, provider, title_en, title_hi, title_gu, description_en, description_hi, description_gu, referral_link, validity, terms, channel_id, rotation_index FROM offers WHERE channel_id = ? AND status = 'queued' ORDER BY created_at ASC LIMIT 1",
                    (channel_id,)
                )
            
            row = cur.fetchone()
            con.close()
            return row
        except Exception as e:
            logger.error(f"❌ Failed to get next queued offer by channel: {e}")
            return None
    
    def mark_posted(self, offer_id: int, success: bool = True, error_message: Optional[str] = None):
        """Mark offer as posted"""
        try:
            con = self.connect()
            cur = con.cursor()
            
            if self.db_type == DatabaseType.POSTGRESQL:
                cur.execute("UPDATE offers SET status = %s, posted_at = %s WHERE id = %s",
                           ("posted" if success else "failed", int(time.time()), offer_id))
                cur.execute("SELECT channel_id FROM offers WHERE id = %s", (offer_id,))
                channel_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO posting_history (offer_id, channel_id, posted_at, success, error_message) VALUES (%s, %s, %s, %s, %s)",
                    (offer_id, channel_id, int(time.time()), success, error_message)
                )
                if success:
                    cur.execute("UPDATE offers SET rotation_index = rotation_index + 1 WHERE id = %s", (offer_id,))
            else:
                cur.execute("UPDATE offers SET status = ?, posted_at = ? WHERE id = ?",
                           ("posted" if success else "failed", int(time.time()), offer_id))
                cur.execute("SELECT channel_id FROM offers WHERE id = ?", (offer_id,))
                channel_id = cur.fetchone()[0]
                cur.execute(
                    "INSERT INTO posting_history (offer_id, channel_id, posted_at, success, error_message) VALUES (?, ?, ?, ?, ?)",
                    (offer_id, channel_id, int(time.time()), success, error_message)
                )
                if success:
                    cur.execute("UPDATE offers SET rotation_index = rotation_index + 1 WHERE id = ?", (offer_id,))
            
            con.commit()
            con.close()
        except Exception as e:
            logger.error(f"❌ Failed to mark offer as posted: {e}")
    
    def get_stats(self) -> Dict[str, Dict[str, int]]:
        """Get database statistics"""
        try:
            from config_schema import ServiceType
            
            con = self.connect()
            cur = con.cursor()
            stats = {}
            
            for service_type in ServiceType:
                if self.db_type == DatabaseType.POSTGRESQL:
                    cur.execute(
                        "SELECT COUNT(CASE WHEN status = 'queued' THEN 1 END), COUNT(CASE WHEN status = 'posted' THEN 1 END), COUNT(CASE WHEN status = 'failed' THEN 1 END) FROM offers WHERE service_type = %s",
                        (service_type.value,)
                    )
                else:
                    cur.execute(
                        "SELECT COUNT(CASE WHEN status = 'queued' THEN 1 END), COUNT(CASE WHEN status = 'posted' THEN 1 END), COUNT(CASE WHEN status = 'failed' THEN 1 END) FROM offers WHERE service_type = ?",
                        (service_type.value,)
                    )
                
                row = cur.fetchone()
                stats[service_type.value] = {"queued": row[0] or 0, "posted": row[1] or 0, "failed": row[2] or 0}
            
            con.close()
            return stats
        except Exception as e:
            logger.error(f"❌ Failed to get stats: {e}")
            return {}

# Initialize database manager (defaults to SQLite, uses PostgreSQL if DATABASE_URL is set)
database_type = DatabaseType.POSTGRESQL if os.environ.get("DATABASE_URL") else DatabaseType.SQLITE
db_manager = DatabaseManager(database_type)
