import sqlite3
from pathlib import Path
DATABSE_DIR = Path(__file__).parent / "templates/database/items.db" 
# 查询数据库
def query_database(item_id):
    # 连接到 SQLite 数据库
    conn = sqlite3.connect(DATABSE_DIR)
    cursor = conn.cursor()

    # 查询数据
    cursor.execute('SELECT name, market_hash_name FROM items WHERE id = ?', (item_id,))
    result = cursor.fetchone()

    # 关闭连接
    conn.close()

    if result:
        return result
    else:
        return None, None