"""
Logging utilities for the MCP Application Monitor Server
"""
import logging
import sys
from pathlib import Path
from config.settings import config


def setup_logging():
    """Setup logging with security considerations"""
    log_handlers = [logging.StreamHandler(sys.stderr)]
    
    # Add file handler if audit logging is enabled
    if config.ENABLE_AUDIT_LOG:
        log_file = Path(__file__).parent.parent / "logs" / "mcp_server.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        log_handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=log_handlers
    )
    
    return logging.getLogger(__name__)


def get_logger(name: str = __name__):
    """Get a logger instance"""
    return logging.getLogger(name)
