import sqlite3
from nonebot.log import logger

DB_PATH = 'serverdata.db'

def init_db():
    """初始化数据库，创建表格"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute('''
            CREATE TABLE IF NOT EXISTS servers (
                group_id TEXT,
                address TEXT,
                PRIMARY KEY (group_id, address)
            )
            ''')
            conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database initialization error: {str(e)}")

def add_server_address(group_id: str, address: str):
    """将群ID和服务器地址存储到数据库中，避免重复绑定"""
    try:
        # 检查是否已存在该群ID和服务器地址的组合
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute('SELECT 1 FROM servers WHERE group_id = ? AND address = ?', (group_id, address))
            if cursor.fetchone() is not None:
                logger.info(f"服务器地址 {address} 已绑定到群 {group_id}，无需重复绑定。")
                return  # 直接返回，不进行重复绑定

            # 插入新的群ID和服务器地址
            conn.execute('''
            INSERT INTO servers (group_id, address)
            VALUES (?, ?)
            ''', (group_id, address))
            conn.commit()
            logger.info(f"成功绑定服务器地址 {address} 到群 {group_id}。")
    except sqlite3.Error as e:
        logger.error(f"Database insert error: {str(e)}")

def delete_server_address(group_id: str, address: str) -> bool:
    """
    删除数据库中的群ID和服务器地址组合。
    如果数据库中不存在该组合，则返回 False。
    """
    try:
        with sqlite3.connect(DB_PATH) as conn:
            # 检查是否已存在该群ID和服务器地址的组合
            cursor = conn.execute('SELECT 1 FROM servers WHERE group_id = ? AND address = ?', (group_id, address))
            if cursor.fetchone() is None:
                logger.info(f"服务器地址 {address} 未绑定到群 {group_id}，无法删除。")
                return False  # 记录不存在，返回 False

            # 删除指定的群ID和服务器地址组合
            conn.execute('''
            DELETE FROM servers
            WHERE group_id = ? AND address = ?
            ''', (group_id, address))
            conn.commit()
            logger.info(f"成功删除服务器地址 {address} 从群 {group_id}。")
            return True  # 成功删除，返回 True
    except sqlite3.Error as e:
        logger.error(f"Database delete error: {str(e)}")
        return False  # 发生错误，返回 False
    
def get_server_addresses(group_id: str):
    """根据群ID查询所有服务器地址"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.execute('SELECT address FROM servers WHERE group_id = ?', (group_id,))
            results = cursor.fetchall()
            return [row[0] for row in results]
    except sqlite3.Error as e:
        logger.error(f"Database query error: {str(e)}")
        return []
