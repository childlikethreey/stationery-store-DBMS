import mysql.connector
import os
from contextlib import contextmanager

def get_connection():
    return mysql.connector.connect(
        host=os.getenv("SERVER"),
        user=os.getenv("ROOT_USERNAME"),
        password=os.getenv("ROOT_PASSWORD"),
        database=os.getenv("DBNAME"),
        port=os.getenv("PORT"),
        autocommit=False
    )

@contextmanager
def connect_manger():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True, buffered=True)
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()
    
