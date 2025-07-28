"""
Database connection and initialization module
"""
import sqlite3
import queue
import threading
from contextlib import contextmanager
from pathlib import Path
from config.settings import config
from utils.logging_utils import get_logger
from database.schema import TABLES, INDEXES

logger = get_logger(__name__)

class DatabaseManager:
    """A thread-safe SQLite connection pool manager"""
    def __init__(self, db_path, pool_size=5):
        self.db_path = db_path
        self.pool_size = pool_size
        self.pool = queue.Queue(maxsize=pool_size)
        self.lock = threading.Lock()
        self._create_pool()

    def _create_pool(self):
        """Creates the connection pool"""
        for _ in range(self.pool_size):
            self.pool.put(self._create_connection())

    def _create_connection(self):
        """Creates a new database connection"""
        try:
            conn = sqlite3.connect(
                self.db_path,
                timeout=10.0,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            conn.execute("PRAGMA journal_mode = DELETE")
            conn.execute("PRAGMA synchronous = NORMAL")
            return conn
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool"""
        conn = self.pool.get()
        try:
            yield conn
        finally:
            self.pool.put(conn)

    def close_all(self):
        """Close all connections in the pool"""
        with self.lock:
            while not self.pool.empty():
                conn = self.pool.get()
                conn.close()

db_manager = DatabaseManager(config.DB_PATH)

def init_database():
    """Initialize the SQLite database with enhanced schema"""
    try:
        with db_manager.get_connection() as conn:
            cursor = conn.cursor()
            
            for table_name, table_sql in TABLES.items():
                logger.info(f"Creating table: {table_name}")
                cursor.execute(table_sql)

            for index_sql in INDEXES:
                logger.info(f"Creating index: {index_sql}")
                cursor.execute(index_sql)
            
            conn.commit()
            logger.info("Database initialized successfully")
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
