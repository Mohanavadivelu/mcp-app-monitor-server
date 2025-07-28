DB_JOURNAL_MODE=DELETEDB_JOURNAL_MODE=DELETE#!/usr/bin/env python3
"""
Enhanced MCP Server for Application Monitoring Data
Built with FastMCP with security and stability improvements
"""

import sqlite3
import json
import os
import sys
import logging
import time
import hashlib
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import asyncio
from functools import wraps
import threading
from contextlib import contextmanager

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("Application Monitor Server")

# Configuration
class Config:
    def __init__(self):
        self.DB_PATH = Path(__file__).parent / "app_monitor.db"
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.MAX_QUERY_RESULTS = int(os.getenv("MAX_QUERY_RESULTS", "1000"))
        self.RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        self.ADMIN_USER = os.getenv("ADMIN_USER", "admin")
        self.DB_ENCRYPTION_KEY = os.getenv("DB_ENCRYPTION_KEY", "")
        self.ENABLE_AUDIT_LOG = os.getenv("ENABLE_AUDIT_LOG", "true").lower() == "true"
        self.DB_BACKUP_ENABLED = os.getenv("DB_BACKUP_ENABLED", "false").lower() == "true"
        self.DB_BACKUP_INTERVAL = int(os.getenv("DB_BACKUP_INTERVAL", "3600"))

config = Config()

# Setup logging with security considerations
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr),
        logging.FileHandler(Path(__file__).parent / "mcp_server.log") if config.ENABLE_AUDIT_LOG else logging.NullHandler()
    ]
)
logger = logging.getLogger(__name__)

# Rate limiting
class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
        self.lock = threading.Lock()
    
    def is_allowed(self) -> bool:
        with self.lock:
            now = time.time()
            # Remove old requests
            self.requests = [req_time for req_time in self.requests if now - req_time < self.window_seconds]
            
            if len(self.requests) < self.max_requests:
                self.requests.append(now)
                return True
            return False

rate_limiter = RateLimiter(config.RATE_LIMIT_REQUESTS, config.RATE_LIMIT_WINDOW)

# Security decorators
def rate_limit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not rate_limiter.is_allowed():
            logger.warning(f"Rate limit exceeded for function {func.__name__}")
            return "Error: Rate limit exceeded. Please try again later."
        return func(*args, **kwargs)
    return wrapper

def audit_log(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if config.ENABLE_AUDIT_LOG:
            logger.info(f"Function {func.__name__} called with args: {args[:2]}...")  # Log first 2 args only for security
        result = func(*args, **kwargs)
        if config.ENABLE_AUDIT_LOG:
            logger.info(f"Function {func.__name__} completed successfully")
        return result
    return wrapper

def validate_input(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Basic input validation
        for arg in args:
            if isinstance(arg, str) and len(arg) > 1000:  # Prevent extremely long strings
                return "Error: Input too long"
            if isinstance(arg, str) and any(char in arg for char in ['<', '>', '&', '"', "'"]):
                logger.warning(f"Potentially unsafe input detected in {func.__name__}")
        return func(*args, **kwargs)
    return wrapper

# Database connection with security enhancements
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
        backup_path = config.DB_PATH.parent / f"app_monitor_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        
        with get_secure_db_connection() as source:
            with sqlite3.connect(backup_path) as backup:
                source.backup(backup)
        
        logger.info(f"Database backup created: {backup_path}")
        
        # Clean up old backups (keep last 5)
        backup_files = sorted(config.DB_PATH.parent.glob("app_monitor_backup_*.db"))
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

# Enhanced MCP tools with security features
@mcp.tool()
@rate_limit
@audit_log
@validate_input
def insert_app_usage_record(
    monitor_app_version: str,
    platform: str,
    user: str,
    application_name: str,
    application_version: str,
    log_date: str,
    legacy_app: bool,
    duration_seconds: int
) -> str:
    """
    Insert a new application usage record with enhanced validation.
    """
    try:
        # Additional validation
        if duration_seconds < 0 or duration_seconds > 86400:  # Max 24 hours
            return "Error: Invalid duration_seconds (must be 0-86400)"
        
        # Validate date format
        try:
            datetime.fromisoformat(log_date.replace('Z', '+00:00'))
        except ValueError:
            return "Error: Invalid log_date format (use ISO format)"
        
        with get_secure_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO app_usage (
                    monitor_app_version, platform, user, application_name,
                    application_version, log_date, legacy_app, duration_seconds
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                monitor_app_version[:50], platform[:50], user[:100], 
                application_name[:100], application_version[:50], 
                log_date, legacy_app, duration_seconds
            ))
            
            record_id = cursor.lastrowid
            
            # Audit log
            if config.ENABLE_AUDIT_LOG:
                cursor.execute("""
                    INSERT INTO audit_log (action, table_name, record_id, details)
                    VALUES (?, ?, ?, ?)
                """, ("INSERT", "app_usage", record_id, f"User: {user}, App: {application_name}"))
            
            conn.commit()
            
            logger.info(f"Record inserted successfully with ID: {record_id}")
            return f"Successfully inserted record with ID: {record_id}"
    
    except Exception as e:
        logger.error(f"Error inserting record: {e}")
        return f"Error inserting record: Database operation failed"

@mcp.tool()
@rate_limit
@audit_log
def delete_app_usage_record(record_id: int) -> str:
    """
    Delete an application usage record with audit logging.
    """
    try:
        if record_id <= 0:
            return "Error: Invalid record ID"
        
        with get_secure_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if record exists first
            cursor.execute("SELECT user, application_name FROM app_usage WHERE id = ?", (record_id,))
            record = cursor.fetchone()
            
            if not record:
                return f"No record found with ID: {record_id}"
            
            cursor.execute("DELETE FROM app_usage WHERE id = ?", (record_id,))
            
            # Audit log
            if config.ENABLE_AUDIT_LOG:
                cursor.execute("""
                    INSERT INTO audit_log (action, table_name, record_id, details)
                    VALUES (?, ?, ?, ?)
                """, ("DELETE", "app_usage", record_id, f"Deleted record for user: {record['user']}"))
            
            conn.commit()
            
            logger.info(f"Record {record_id} deleted successfully")
            return f"Successfully deleted record with ID: {record_id}"
    
    except Exception as e:
        logger.error(f"Error deleting record {record_id}: {e}")
        return f"Error deleting record: Database operation failed"

@mcp.tool()
@rate_limit
@audit_log
def get_all_app_usage_records(limit: int = None) -> str:
    """
    Retrieve application usage records with pagination support.
    """
    try:
        # Apply default limit for security
        if limit is None or limit > config.MAX_QUERY_RESULTS:
            limit = config.MAX_QUERY_RESULTS
        
        if limit <= 0:
            return "Error: Invalid limit value"
        
        with get_secure_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, monitor_app_version, platform, user, application_name,
                       application_version, log_date, legacy_app, duration_seconds,
                       created_at
                FROM app_usage 
                ORDER BY created_at DESC 
                LIMIT ?
            """, (limit,))
            
            rows = cursor.fetchall()
            
            records = []
            for row in rows:
                records.append({
                    "id": row["id"],
                    "monitor_app_version": row["monitor_app_version"],
                    "platform": row["platform"],
                    "user": row["user"],
                    "application_name": row["application_name"],
                    "application_version": row["application_version"],
                    "log_date": row["log_date"],
                    "legacy_app": bool(row["legacy_app"]),
                    "duration_seconds": row["duration_seconds"],
                    "created_at": row["created_at"]
                })
            
            result = {
                "total_records": len(records),
                "limit_applied": limit,
                "records": records
            }
            
            return json.dumps(result, indent=2)
    
    except Exception as e:
        logger.error(f"Error retrieving records: {e}")
        return "Error retrieving records: Database operation failed"

@mcp.tool()
@rate_limit  
@audit_log
@validate_input
def get_app_usage_by_user(user: str, limit: int = None) -> str:
    """
    Retrieve application usage records for a specific user with security checks.
    """
    try:
        if not user or len(user.strip()) == 0:
            return "Error: User parameter is required"
        
        user = user.strip()[:100]  # Truncate for security
        
        if limit is None or limit > config.MAX_QUERY_RESULTS:
            limit = config.MAX_QUERY_RESULTS
            
        with get_secure_db_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, monitor_app_version, platform, user, application_name,
                       application_version, log_date, legacy_app, duration_seconds,
                       created_at
                FROM app_usage 
                WHERE user = ? 
                ORDER BY log_date DESC 
                LIMIT ?
            """, (user, limit))
            
            rows = cursor.fetchall()
            
            records = []
            for row in rows:
                records.append({
                    "id": row["id"],
                    "monitor_app_version": row["monitor_app_version"],
                    "platform": row["platform"],
                    "user": row["user"],
                    "application_name": row["application_name"],
                    "application_version": row["application_version"],
                    "log_date": row["log_date"],
                    "legacy_app": bool(row["legacy_app"]),
                    "duration_seconds": row["duration_seconds"],
                    "created_at": row["created_at"]
                })
            
            result = {
                "user": user,
                "total_records": len(records),
                "limit_applied": limit,
                "records": records
            }
            
            return json.dumps(result, indent=2)
    
    except Exception as e:
        logger.error(f"Error retrieving records for user {user}: {e}")
        return f"Error retrieving records: Database operation failed"

@mcp.tool()
@rate_limit
@audit_log
def get_database_stats() -> str:
    """
    Get database statistics with performance monitoring.
    """
    try:
        with get_secure_db_connection() as conn:
            cursor = conn.cursor()
            
            # Total records
            cursor.execute("SELECT COUNT(*) as total FROM app_usage")
            total_records = cursor.fetchone()["total"]
            
            # Unique users
            cursor.execute("SELECT COUNT(DISTINCT user) as unique_users FROM app_usage")
            unique_users = cursor.fetchone()["unique_users"]
            
            # Unique applications
            cursor.execute("SELECT COUNT(DISTINCT application_name) as unique_apps FROM app_usage")
            unique_apps = cursor.fetchone()["unique_apps"]
            
            # Platform distribution
            cursor.execute("SELECT platform, COUNT(*) as count FROM app_usage GROUP BY platform")
            platform_stats = {row["platform"]: row["count"] for row in cursor.fetchall()}
            
            # Legacy app count
            cursor.execute("SELECT COUNT(*) as legacy_count FROM app_usage WHERE legacy_app = 1")
            legacy_count = cursor.fetchone()["legacy_count"]
            
            # Database file size
            db_size = config.DB_PATH.stat().st_size if config.DB_PATH.exists() else 0
            
            stats = {
                "total_records": total_records,
                "unique_users": unique_users,
                "unique_applications": unique_apps,
                "legacy_applications_usage": legacy_count,
                "platform_distribution": platform_stats,
                "database_size_bytes": db_size,
                "last_backup": "Enabled" if config.DB_BACKUP_ENABLED else "Disabled",
                "rate_limiting": f"{config.RATE_LIMIT_REQUESTS} requests per {config.RATE_LIMIT_WINDOW}s"
            }
            
            return json.dumps(stats, indent=2)
    
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        return "Error getting database stats: Database operation failed"

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="MCP Application Monitor Server")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--max-records", type=int, default=10000, help="Maximum records per query")
    parser.add_argument("--timeout", type=int, default=30, help="Server timeout in seconds")
    return parser.parse_args()

def setup_backup_scheduler():
    """Setup periodic database backups"""
    if not config.DB_BACKUP_ENABLED:
        return
    
    def backup_worker():
        while True:
            time.sleep(config.DB_BACKUP_INTERVAL)
            backup_database()
    
    backup_thread = threading.Thread(target=backup_worker, daemon=True)
    backup_thread.start()
    logger.info(f"Backup scheduler started (interval: {config.DB_BACKUP_INTERVAL}s)")

def main():
    """Main function with enhanced error handling and monitoring"""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        # Update logging level
        logging.getLogger().setLevel(getattr(logging, args.log_level))
        
        logger.info("Starting MCP Application Monitor Server")
        logger.info(f"Configuration: Max records={config.MAX_QUERY_RESULTS}, Rate limit={config.RATE_LIMIT_REQUESTS}/{config.RATE_LIMIT_WINDOW}s")
        
        # Initialize the database
        init_database()
        
        # Create initial backup
        if config.DB_BACKUP_ENABLED:
            backup_database()
            setup_backup_scheduler()
        
        # Run the FastMCP server
        logger.info("Server starting...")
        mcp.run()
        
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Critical error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()