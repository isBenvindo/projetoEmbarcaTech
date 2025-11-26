# back-end/app/db/session.py

import psycopg2.pool
import logging
from contextlib import contextmanager
from app.core.config import settings

logger = logging.getLogger(__name__)

# Create a connection pool. It's thread-safe and will be created only once.
db_pool = psycopg2.pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10, # Adjust maxconn based on expected load
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    dbname=settings.DB_NAME,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD
)

@contextmanager
def get_db_connection():
    """
    Provides a database connection from the pool.
    
    This is a context manager that automatically handles getting a
    connection and returning it to the pool.
    """
    conn = None
    try:
        conn = db_pool.getconn()
        yield conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        # Reraise the exception to be handled by FastAPI's error handlers
        raise
    finally:
        if conn:
            db_pool.putconn(conn)

def db_dependency():
    """
    A FastAPI dependency that yields a database connection.
    This manages the connection lifecycle for each API request.
    """
    with get_db_connection() as conn:
        yield conn