from contextlib import contextmanager
from typing import Generator, Optional
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from app.config import settings

_db_pool: Optional[pool.ThreadedConnectionPool] = None


def get_db_pool() -> pool.ThreadedConnectionPool:
    global _db_pool
    if _db_pool is None or _db_pool.closed:
        _db_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=20,
            dsn=settings.DATABASE_URL
        )
    return _db_pool


def close_db_pool() -> None:
    global _db_pool
    if _db_pool is not None and not _db_pool.closed:
        _db_pool.closeall()
        _db_pool = None


@contextmanager
def get_db_cursor(commit: bool = True, user_id: Optional[int] = None) -> Generator[RealDictCursor, None, None]:
    """
    Context manager yielding a RealDictCursor with transactional safety.
    If user_id is provided, sets transaction-local app.current_user_id for audit logging.
    """
    db_pool = get_db_pool()
    conn = db_pool.getconn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if user_id is not None:
                cur.execute("SELECT set_config('app.current_user_id', %s, true);", (str(user_id),))
            yield cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        db_pool.putconn(conn)

