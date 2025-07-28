import json
from mcp.server.fastmcp import FastMCP
from database.connection import db_manager
from server.decorators import rate_limit, audit_log
from config.settings import config
from utils.logging_utils import get_logger

logger = get_logger(__name__)

def register_database_stats_tool(mcp: FastMCP):
    @mcp.tool()
    @rate_limit
    @audit_log
    def get_database_stats() -> str:
        """
        Get database statistics with performance monitoring.
        """
        try:
            with db_manager.get_connection() as conn:
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
