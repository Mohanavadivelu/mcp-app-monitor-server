"""
Security decorators and rate limiting for MCP server
"""
import time
import threading
from functools import wraps
from config.settings import config
from utils.logging_utils import get_logger

logger = get_logger(__name__)


class RateLimiter:
    """Rate limiter implementation with thread safety"""
    
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


# Global rate limiter instance
rate_limiter = RateLimiter(config.RATE_LIMIT_REQUESTS, config.RATE_LIMIT_WINDOW)


def rate_limit(func):
    """Rate limiting decorator"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not rate_limiter.is_allowed():
            logger.warning(f"Rate limit exceeded for function {func.__name__}")
            return "Error: Rate limit exceeded. Please try again later."
        return func(*args, **kwargs)
    return wrapper


def audit_log(func):
    """Audit logging decorator"""
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
    """Input validation decorator"""
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
