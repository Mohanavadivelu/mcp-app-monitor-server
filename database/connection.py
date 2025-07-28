"""
Database connection and initialization module
"""
import sqlite3
import shutil
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from config.settings import config
from utils.logging_utils import get_logger

logger = get_logger(__name__)


@contextmanager
def get_secure_db_connection():
    """Get a secure database connection with timeout and error handling"""
    conn = None
    try:
        conn = sqlite3.connect(
            config.DB_PATH,
            timeout=10.0,  # Connection timeout
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        # Enable foreign key constraints
        conn.execute("PRAGMA foreign_keys = ON")
        # Set secure pragmas
        conn.execute("PRAGMA journal_mode = DELETE")  # No WAL files created
        conn.execute("PRAGMA synchronous = NORMAL")  # Balance between safety and speed
        yield conn
    except sqlite3.Error as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        if conn:
            conn.close()


def init_database():
    """Initialize the SQLite database with enhanced schema"""
    try:
        with get_secure_db_connection() as conn:
            cursor = conn.cursor()
            
            # Main table with constraints
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS app_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    monitor_app_version TEXT NOT NULL CHECK(length(monitor_app_version) <= 50),
                    platform TEXT NOT NULL CHECK(length(platform) <= 50),
                    user TEXT NOT NULL CHECK(length(user) <= 100),
                    application_name TEXT NOT NULL CHECK(length(application_name) <= 100),
                    application_version TEXT NOT NULL CHECK(length(application_version) <= 50),
                    log_date TEXT NOT NULL,
                    legacy_app BOOLEAN NOT NULL,
                    duration_seconds INTEGER NOT NULL CHECK(duration_seconds >= 0),
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Audit log table
            if config.ENABLE_AUDIT_LOG:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS audit_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        action TEXT NOT NULL,
                        table_name TEXT NOT NULL,
                        record_id INTEGER,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        details TEXT
                    )
                """)
            
            # Create indexes for better performance
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_usage_user ON app_usage(user)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_usage_date ON app_usage(log_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_app_usage_app ON app_usage(application_name)")
            
            conn.commit()
            logger.info("Database initialized successfully")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def backup_database():
    """Create a backup of the database"""
    if not config.DB_BACKUP_ENABLED:
        return
    
    try:
        backup_dir = config.DB_PATH.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        backup_path = backup_dir / f"app_monitor_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        # Create backup using shutil for better error handling
        shutil.copy2(config.DB_PATH, backup_path)
        
        logger.info(f"Database backup created: {backup_path}")
        
        # Clean up old backups (keep last 5)
        backup_files = sorted(backup_dir.glob("app_monitor_backup_*.db"))
        if len(backup_files) > 5:
            for old_backup in backup_files[:-5]:
                old_backup.unlink()
                logger.info(f"Removed old backup: {old_backup}")
                
    except Exception as e:
        logger.error(f"Failed to create database backup: {e}")


def cleanup_wal_files():
    """Clean up WAL and SHM files"""
    try:
        db_dir = config.DB_PATH.parent
        # Clean up backup WAL files
        for wal_file in db_dir.glob("*.db-wal"):
            wal_file.unlink()
            logger.info(f"Removed WAL file: {wal_file}")
        
        # Clean up backup SHM files  
        for shm_file in db_dir.glob("*.db-shm"):
            shm_file.unlink()
            logger.info(f"Removed SHM file: {shm_file}")
            
    except Exception as e:
        logger.error(f"Failed to clean up WAL files: {e}")
