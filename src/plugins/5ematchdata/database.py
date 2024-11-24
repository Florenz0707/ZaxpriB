import sqlite3
from nonebot.log import logger


MATCH_DB_PATH = './resources/databases/5ematch.db'
# 绑定比赛字符串并生成自增的 match_id
def bind_match(match_str: str) -> int:
    try:
        with sqlite3.connect(MATCH_DB_PATH) as conn:
            # 先查询是否已存在该比赛字符串
            cursor = conn.execute('SELECT match_id FROM matches WHERE match_str = ?', (match_str,))
            result = cursor.fetchone()
            
            if result:
                return result[0]  # 如果已存在，则返回 match_id
            
            # 否则插入新的比赛字符串并获取自增的 match_id
            cursor = conn.execute('''
            INSERT INTO matches (match_str)
            VALUES (?)
            ''', (match_str,))
            conn.commit()
            return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error(f"Database match binding error: {str(e)}")
        return None

# 根据 match_id 获取比赛字符串
def get_match_by_id(match_id: int) -> str:
    try:
        with sqlite3.connect(MATCH_DB_PATH) as conn:
            cursor = conn.execute('SELECT match_str FROM matches WHERE match_id = ?', (match_id,))
            result = cursor.fetchone()
            return result[0] if result else {"error": "No match found"}
    except sqlite3.Error as e:
        logger.error(f"Database match query error: {str(e)}")
        return {"error": "No match found"}