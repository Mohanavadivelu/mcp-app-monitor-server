"""
Application configuration settings
"""
import os
from pathlib import Path


class Config:
    """Configuration class for MCP Application Monitor Server"""
    
    def __init__(self):
        # Database configuration
        self.DB_PATH = Path(__file__).parent.parent / "data" / "app_monitor.db"
        
        # Logging configuration
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.ENABLE_AUDIT_LOG = os.getenv("ENABLE_AUDIT_LOG", "true").lower() == "true"
        
        # Query limits
        self.MAX_QUERY_RESULTS = int(os.getenv("MAX_QUERY_RESULTS", "1000"))
        
        # Rate limiting
        self.RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "100"))
        self.RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "60"))
        
        # Security
        self.ADMIN_USER = os.getenv("ADMIN_USER", "admin")
        self.DB_ENCRYPTION_KEY = os.getenv("DB_ENCRYPTION_KEY", "")
        
        # Backup configuration
        self.DB_BACKUP_ENABLED = os.getenv("DB_BACKUP_ENABLED", "false").lower() == "true"
        self.DB_BACKUP_INTERVAL = int(os.getenv("DB_BACKUP_INTERVAL", "3600"))
        
        # Ensure data directory exists
        self.DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# Global configuration instance
config = Config()
