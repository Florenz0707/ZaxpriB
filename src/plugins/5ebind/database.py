import sqlite3
from nonebot.log import logger

DB_PATH = '5edata.db'

def init_db():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                steam_id TEXT NOT NULL
            )
            ''')
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {str(e)}")

def bind_steam_id(user_id: str, steam_id: str):
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
            INSERT INTO users (user_id, steam_id)
            VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET steam_id=excluded.steam_id;
            ''', (user_id, steam_id))
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database binding error: {str(e)}")

def get_steam_id(user_id: str) -> str:
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute('SELECT steam_id FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            return result[0] if result else None
    except sqlite3.Error as e:
        logger.error(f"Database query error: {str(e)}")
        return None
