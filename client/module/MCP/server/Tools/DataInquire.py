import os
import sqlite3

# ================ 数据查询类 ================
class DataInquire:
    # ================ 文件 ================
    #  -------------- 查询文件目录 --------------
    # * file_path 文件路径
    def file_directory(self, file_path: str):
        """
        查询文件目录
        :param file_path: 文件路径
        :return: 文件目录
        :error: 文件路径不能为空
        """
        if file_path is None or file_path == "":
            return None
        file_catalog = os.walk(file_path) # 遍历文件目录
        
        return file_catalog

    #  -------------- 查询文件内容 --------------
    # * file_path 文件路径
    def file_content(self, file_path: str):
        """
        查询文件内容
        :param file_path: 文件路径
        :return: 文件内容
        :error: 文件路径不能为空
        """
        if file_path is None or file_path == "":
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        return file_content
    #  -------------- 查询文件行数 --------------
    # * file_path 文件路径
    def file_line_count(self, file_path: str):
        """
        查询文件行数
        :param file_path: 文件路径
        :return: 文件行数
        :error: 文件路径不能为空
        """
        if file_path is None or file_path == "":
            return None
        with open(file_path, 'r', encoding='utf-8') as f:
            file_line_count = len(f.readlines())
        return file_line_count

    # --------------- 模糊查询文件内容 ---------------
    # * file_path 文件路径
    # * content 查询内容
    def file_content_fuzzy(self, file_path: str, content: str):
        """
        模糊查询文件内容
        :param file_path: 文件路径
        :param content: 查询内容
        :return: 文件内容
        :error: 文件路径不能为空
        """
        if file_path is None or file_path == "":
            return None

        buffer = []
        file_catalog = os.walk(file_path) # 遍历文件目录
        # 遍历文件目录下的所有文件
        # root: 文件目录
        # dirs: 文件目录下的所有文件夹
        # files: 文件目录下的所有文件
        for root, dirs, files in file_catalog:
            for file in files:
                if file.endswith('.txt'):
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        file_content = f.read()
                        if content in file_content:
                            buffer.append(file_content)
        return buffer

    # ================ 数据库 ================
    #  -------------- 查询所有数据表 --------------
    # * db_name 数据库名称
    def database_all_table(self, db_name: str):
        """
        查询数据库所有数据表
        :param db_name: 数据库名称
        :return: 数据表列表
        :error: 数据库名称不能为空
        """
        if db_name is None or db_name == "":
            return "数据库名称不能为空"
        
        if not os.path.exists(db_name):
            return "数据库文件不存在"
        
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            return tables
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            return f"查询表列表失败: {e}"
    #  -------------- 查询表中所有数据 --------------
    # * db_name 数据库名称
    # * table_name 数据表名称
    def database_table_content(self, db_name: str, table_name: str):
        """
        查询数据表所有数据
        :param db_name: 数据库名称
        :param table_name: 数据表名称
        :return: 数据表数据
        :error: 数据库名称不能为空
        :error: 表名不能为空
        """
        if db_name is None or db_name == "":
            return "数据库名称不能为空"
        if table_name is None or table_name == "":
            return "表名不能为空"
        
        if not os.path.exists(db_name):
            return "数据库文件不存在"
        
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                conn.close()
                return f"表 '{table_name}' 不存在"
            
            cursor.execute(f"SELECT id, content FROM {table_name}")
            data = cursor.fetchall()
            conn.close()
            return data
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            return f"查询数据失败: {e}"
    #  -------------- 检查数据在表中是否存在 --------------
    # * db_name 数据库名称
    # * table_name 数据表名称
    # * data_id 数据ID
    def database_table_data_exists(self, db_name: str, table_name: str, data_id: str):
        """
        检查数据在表中是否存在
        :param db_name: 数据库名称
        :param table_name: 数据表名称
        :param data_id: 数据ID
        :return: 是否存在
        :error: 数据库名称不能为空
        :error: 表名不能为空
        :error: 数据ID不能为空
        """
        if db_name is None or db_name == "":
            return "数据库名称不能为空"
        if table_name is None or table_name == "":
            return "表名不能为空"
        if data_id is None or data_id == "":
            return "数据ID不能为空"
        
        if not os.path.exists(db_name):
            return False
        
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                conn.close()
                return False
            
            cursor.execute(f"SELECT 1 FROM {table_name} WHERE id=?", (data_id,))
            result = cursor.fetchone() is not None
            conn.close()
            return result
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            return False
    #  -------------- 模糊查询数据库内容 --------------
    # * db_name 数据库名称
    # * content 查询内容
    def database_content_fuzzy(self, db_name: str, content: str):
        """
        模糊查询数据库内容（在所有表中搜索）
        :param db_name: 数据库名称
        :param content: 查询内容
        :return: 查询结果
        :error: 数据库名称不能为空
        :error: 查询内容不能为空
        """
        if db_name is None or db_name == "":
            return "数据库名称不能为空"
        if content is None or content == "":
            return "查询内容不能为空"
        
        if not os.path.exists(db_name):
            return "数据库文件不存在"
        
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            
            # 获取所有表
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # 在所有表中搜索
            results = {}
            for table in tables:
                cursor.execute(f"SELECT id, content FROM {table} WHERE content LIKE ?", (f'%{content}%',))
                data = cursor.fetchall()
                if data:
                    results[table] = data
            
            conn.close()
            return results
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            return f"模糊查询失败: {e}"
      # -------------- 统计数据数量 - 统计表中记录数--------------
    # * db_name 数据库名称
    # * table_name 数据表名称
    def database_table_data_count(self, db_name: str, table_name: str):
        """
        统计数据表数据数量
        :param db_name: 数据库名称
        :param table_name: 数据表名称
        :return: 数据数量
        :error: 数据库名称不能为空
        :error: 表名不能为空
        """
        if db_name is None or db_name == "":
            return "数据库名称不能为空"
        if table_name is None or table_name == "":
            return "表名不能为空"
        
        if not os.path.exists(db_name):
            return "数据库文件不存在"
        
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                conn.close()
                return f"表 '{table_name}' 不存在"
            
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            return f"统计数据失败: {e}"
    #  -------------- 批量查询 - 一次查询多个ID--------------
    # * db_name 数据库名称
    # * table_name 数据表名称
    # * data_ids 数据ID列表
    def database_table_data_batch(self, db_name: str, table_name: str, data_ids: list):
        """
        批量查询数据表数据
        :param db_name: 数据库名称
        :param table_name: 数据表名称
        :param data_ids: 数据ID列表
        :return: 查询结果
        :error: 数据库名称不能为空
        :error: 表名不能为空
        :error: 数据ID列表不能为空
        """
        if db_name is None or db_name == "":
            return "数据库名称不能为空"
        if table_name is None or table_name == "":
            return "表名不能为空"
        if not data_ids:
            return {}
        
        if not os.path.exists(db_name):
            return "数据库文件不存在"
        
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                conn.close()
                return f"表 '{table_name}' 不存在"
            
            # 批量查询
            placeholders = ','.join('?' * len(data_ids))
            cursor.execute(f"SELECT id, content FROM {table_name} WHERE id IN ({placeholders})", data_ids)
            result = {row[0]: row[1] for row in cursor.fetchall()}
            conn.close()
            return result
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            return f"批量查询失败: {e}"
    #  -------------- 按条件筛选 - 根据内容筛选数据--------------
    # * db_name 数据库名称
    # * table_name 数据表名称
    # * content 查询内容
    def database_table_data_filter(self, db_name: str, table_name: str, content: str):
        """
        按条件筛选数据表数据（在指定表中模糊搜索）
        :param db_name: 数据库名称
        :param table_name: 数据表名称
        :param content: 查询内容
        :return: 查询结果
        :error: 数据库名称不能为空
        :error: 表名不能为空
        :error: 查询内容不能为空
        """
        if db_name is None or db_name == "":
            return "数据库名称不能为空"
        if table_name is None or table_name == "":
            return "表名不能为空"
        if content is None or content == "":
            return "查询内容不能为空"
        
        if not os.path.exists(db_name):
            return "数据库文件不存在"
        
        try:
            conn = sqlite3.connect(db_name)
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                conn.close()
                return f"表 '{table_name}' 不存在"
            
            # 模糊查询
            cursor.execute(f"SELECT id, content FROM {table_name} WHERE content LIKE ?", (f'%{content}%',))
            data = cursor.fetchall()
            conn.close()
            return data
        except Exception as e:
            if 'conn' in locals():
                conn.close()
            return f"按条件筛选失败: {e}"