"""
CarePlus Hospital - Database Connection & Execution Layer
Supports primary MySQL database (InnoDB) with seamless automatic local fallback.
"""
import re
import os
import sqlite3
import pymysql
from pymysql.cursors import DictCursor
from flask import current_app, g

def get_db():
    """
    Opens a unique database connection per request context if not already opened.
    Returns the active database connection.
    """
    if 'db' not in g:
        db_type = current_app.config.get('DB_TYPE', 'auto')
        conn = None
        backend = 'mysql'
        
        # 1. Try MySQL if configured
        if db_type in ('mysql', 'auto'):
            try:
                conn = pymysql.connect(
                    host=current_app.config['DB_HOST'],
                    user=current_app.config['DB_USER'],
                    password=current_app.config['DB_PASSWORD'],
                    database=current_app.config['DB_NAME'],
                    port=current_app.config['DB_PORT'],
                    cursorclass=DictCursor,
                    autocommit=False,
                    charset='utf8mb4'
                )
                backend = 'mysql'
            except Exception as e:
                if db_type == 'mysql':
                    raise e
                # In 'auto' mode, fall back to SQLite if MySQL is offline
                backend = 'sqlite'
                
        # 2. SQLite Fallback
        if backend == 'sqlite' or db_type == 'sqlite':
            sqlite_path = current_app.config.get('SQLITE_PATH')
            if not os.path.exists(sqlite_path):
                # Auto-initialize sqlite database if missing
                from database.init_db import init_sqlite
                init_sqlite()
            conn = sqlite3.connect(sqlite_path, timeout=30.0, check_same_thread=False, isolation_level=None)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            backend = 'sqlite'
            
        g.db = conn
        g.db_backend = backend

    return g.db

def close_db(e=None):
    """
    Closes the database connection at the end of the request context.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()

def _adapt_query(query, backend):
    """Translates SQL syntax and parameter placeholders across backends."""
    if backend == 'sqlite':
        # Replace %s with ? for SQLite parameterized queries
        adapted = re.sub(r'%s', '?', query)
        # Adapt MySQL specific functions
        adapted = re.sub(r'NOW\(\)', "datetime('now', 'localtime')", adapted, flags=re.IGNORECASE)
        adapted = re.sub(r'CURDATE\(\)', "date('now', 'localtime')", adapted, flags=re.IGNORECASE)
        return adapted
    return query

def query_db(query, args=(), one=False):
    """
    Executes SELECT queries safely using parameterized inputs.
    Returns a dictionary or list of dictionaries.
    """
    conn = get_db()
    backend = getattr(g, 'db_backend', 'mysql')
    adapted_query = _adapt_query(query, backend)
    
    if backend == 'sqlite':
        cursor = conn.cursor()
        cursor.execute(adapted_query, args)
        rows = cursor.fetchall()
        result = [dict(row) for row in rows]
        return (result[0] if result else None) if one else result
    else:
        with conn.cursor() as cursor:
            cursor.execute(adapted_query, args)
            result = cursor.fetchall()
            return (result[0] if result else None) if one else result

def execute_db(query, args=(), commit=True):
    """
    Executes INSERT, UPDATE, DELETE queries safely.
    Returns the lastrowid or affected rows count.
    """
    conn = get_db()
    backend = getattr(g, 'db_backend', 'mysql')
    adapted_query = _adapt_query(query, backend)
    
    try:
        if backend == 'sqlite':
            cursor = conn.cursor()
            cursor.execute(adapted_query, args)
            last_id = cursor.lastrowid
            affected = cursor.rowcount
            return last_id if last_id else affected
        else:
            with conn.cursor() as cursor:
                cursor.execute(adapted_query, args)
                last_id = cursor.lastrowid
                affected = cursor.rowcount
                if commit:
                    conn.commit()
                return last_id if last_id else affected
    except Exception as e:
        conn.rollback()
        raise e
