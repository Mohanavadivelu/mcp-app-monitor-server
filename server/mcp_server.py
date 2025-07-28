"""
MCP Server setup and tools registration
"""
import json
import threading
import time
from datetime import datetime
from mcp.server.fastmcp import FastMCP
from database.connection import get_secure_db_connection, backup_database
from server.decorators import rate_limit, audit_log, validate_input
from config.settings import config
from utils.logging_utils import get_logger

logger = get_logger(__name__)


def create_mcp_server() -> FastMCP:
    """Create and configure the FastMCP server with tools"""
    mcp = FastMCP("Application Monitor Server")
    
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
    
    return mcp


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
