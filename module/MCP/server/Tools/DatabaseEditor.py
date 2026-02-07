# ================ 数据库修改类 ================
import os
from sqlalchemy import create_engine, Table, Column, String, MetaData, select, update, delete, inspect, func
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

# ================ 数据库编辑类 ================
class DatabaseEditor:
    """
    工具类：数据库编辑，无需初始化和成员变量。全部为静态方法。
    使用 SQLAlchemy 提供安全的数据库操作，自动防止 SQL 注入。
    """

    @staticmethod
    def _get_engine_and_table(db_name: str, table_name: str):
        """
        内部辅助方法：获取数据库引擎和表对象
        SQLAlchemy 会自动验证和转义表名，防止 SQL 注入
        :param db_name: 数据库名称
        :param table_name: 数据表名称
        :return: 数据库引擎和表对象
        :error: 数据库名称不能为空
        :error: 表名不能为空
        """
        engine = create_engine(f'sqlite:///{db_name}', echo=False)
        metadata = MetaData()
        
        table_obj = Table(
            table_name,
            metadata,
            Column('id', String, primary_key=True),
            Column('content', String),
            extend_existing=True
        )
        
        return engine, table_obj, metadata

    def _table_exists(self,engine, table_name: str) -> bool:
        """检查表是否存在"""
        inspector = inspect(engine)
        return table_name in inspector.get_table_names()

    # ================ 创建数据库 ================
    def connect(self, db_name: str) -> tuple[bool, str]:
        """
        若数据库已存在，提前返回。否则创建数据库文件。
        :param db_name: 数据库名称
        :return: 是否成功
        :error: 数据库名称不能为空
        """
        if not db_name:
            return False, "数据库名称不能为空"

        db_dir = os.path.dirname(db_name)
        if db_dir and not os.path.exists(db_dir):
            return False, "数据库目录不存在"

        if os.path.exists(db_name):
            return True, "数据库已存在，无需创建"

        try:
            # 使用 SQLAlchemy 创建数据库
            engine = create_engine(f'sqlite:///{db_name}')
            # 创建一个空连接来初始化数据库文件
            with engine.connect() as conn:
                conn.execute(select(1))  # 简单查询以触发文件创建
            engine.dispose()
            return True, "数据库创建成功"
        except Exception as e:
            return False, f"数据库创建失败: {e}"

    # ================ 删除数据库 ================
    def delete(self, db_name: str) -> tuple[bool, str]:
        """删除数据库文件
        :param db_name: 数据库名称
        :return: 是否成功
        :error: 数据库名称不能为空
        """
        if not db_name:
            return False, "数据库名称不能为空"

        if not os.path.exists(db_name):
            return False, "数据库文件不存在"

        try:
            os.remove(db_name)
            return True, "数据库文件删除成功"
        except Exception as e:
            return False, f"数据库文件删除失败: {e}"

    # ================ 插入数据 ================
    def insert_data(self, db_name: str, table_name: str, data_id: str, content: str) -> tuple[bool, str]:
        """
        插入数据到指定表，如果ID已存在则失败
        :param db_name: 数据库名称
        :param table_name: 数据表名称
        :param data_id: 数据ID
        :param content: 内容
        :return: 是否成功
        :error: 数据库名称不能为空
        :error: 表名不能为空
        :error: 数据ID不能为空
        """
        if not all([db_name, table_name, data_id]):
            return False, "数据库名称、表名和数据ID不能为空"
        
        if not os.path.exists(db_name):
            return False, "数据库文件不存在"
        
        try:
            engine, table_obj, metadata = DatabaseEditor._get_engine_and_table(db_name, table_name)
            
            # 创建表（如果不存在）
            metadata.create_all(engine)
            
            # 插入数据
            with engine.connect() as conn:
                stmt = insert(table_obj).values(id=data_id, content=content)
                conn.execute(stmt)
                conn.commit()
            
            engine.dispose()
            return True, "插入数据成功"
            
        except IntegrityError:
            return False, f"数据ID '{data_id}' 已存在"
        except SQLAlchemyError as e:
            return False, f"插入数据失败: {e}"
        except Exception as e:
            return False, f"插入数据失败: {e}"
    
    # ================ 更新数据 ================
    def update_data(self, db_name: str, table_name: str, data_id: str, content: str) -> tuple[bool, str]:
        """
        更新指定ID的数据内容
        :param db_name: 数据库名称
        :param table_name: 数据表名称
        :param data_id: 数据ID
        :param content: 内容
        :return: 是否成功
        :error: 数据库名称不能为空
        :error: 表名不能为空
        :error: 数据ID不能为空
        """
        if not all([db_name, table_name, data_id]):
            return False, "数据库名称、表名和数据ID不能为空"
        
        if not os.path.exists(db_name):
            return False, "数据库文件不存在"
        
        try:
            engine, table_obj, _ = DatabaseEditor._get_engine_and_table(db_name, table_name)
            
            # 检查表是否存在
            if not DatabaseEditor._table_exists(engine, table_name):
                engine.dispose()
                return False, f"表 '{table_name}' 不存在"
            
            # 更新数据
            with engine.connect() as conn:
                stmt = update(table_obj).where(table_obj.c.id == data_id).values(content=content)
                result = conn.execute(stmt)
                conn.commit()
                
                if result.rowcount == 0:
                    engine.dispose()
                    return False, f"数据ID '{data_id}' 不存在"
            
            engine.dispose()
            return True, "更新数据成功"
            
        except SQLAlchemyError as e:
            return False, f"更新数据失败: {e}"
        except Exception as e:
            return False, f"更新数据失败: {e}"
    
    # ================ 删除数据 ================
    def delete_data(self, db_name: str, table_name: str, data_id: str) -> tuple[bool, str]:
        """
        删除指定ID的数据
        :param db_name: 数据库名称
        :param table_name: 数据表名称
        :param data_id: 数据ID
        :return: 是否成功
        :error: 数据库名称不能为空
        :error: 表名不能为空
        :error: 数据ID不能为空
        """
        if not all([db_name, table_name, data_id]):
            return False, "数据库名称、表名和数据ID不能为空"
        
        if not os.path.exists(db_name):
            return False, "数据库文件不存在"
        
        try:
            engine, table_obj, _ = DatabaseEditor._get_engine_and_table(db_name, table_name)
            
            # 检查表是否存在
            if not DatabaseEditor._table_exists(engine, table_name):
                engine.dispose()
                return False, f"表 '{table_name}' 不存在"
            
            # 删除数据
            with engine.connect() as conn:
                stmt = delete(table_obj).where(table_obj.c.id == data_id)
                result = conn.execute(stmt)
                conn.commit()
                
                if result.rowcount == 0:
                    engine.dispose()
                    return False, f"数据ID '{data_id}' 不存在"
            
            engine.dispose()
            return True, "删除数据成功"
            
        except SQLAlchemyError as e:
            return False, f"删除数据失败: {e}"
        except Exception as e:
            return False, f"删除数据失败: {e}"
    
    # ================ 创建数据表 ================
    def create_table(self, db_name: str, table_name: str) -> tuple[bool, str]:
        """
        在指定数据库中创建数据表
        :param db_name: 数据库名称
        :param table_name: 数据表名称
        :return: 是否成功
        :error: 数据库名称不能为空
        :error: 表名不能为空
        """
        if not all([db_name, table_name]):
            return False, "数据库名称和表名不能为空"
        
        if not os.path.exists(db_name):
            return False, "数据库文件不存在"
        
        try:
            engine, table_obj, metadata = DatabaseEditor._get_engine_and_table(db_name, table_name)
            
            # 检查表是否已存在
            if DatabaseEditor._table_exists(engine, table_name):
                engine.dispose()
                return True, f"表 '{table_name}' 已存在"
            
            # 创建表
            metadata.create_all(engine)
            engine.dispose()
            return True, "创建数据表成功"
            
        except SQLAlchemyError as e:
            return False, f"创建数据表失败: {e}"
        except Exception as e:
            return False, f"创建数据表失败: {e}"
    
    # ================ 删除数据表 ================
    def delete_table(self, db_name: str, table_name: str) -> tuple[bool, str]:
        """
        删除指定数据库中的数据表
        :param db_name: 数据库名称
        :param table_name: 数据表名称
        :return: 是否成功
        :error: 数据库名称不能为空
        :error: 表名不能为空
        """
        if not all([db_name, table_name]):
            return False, "数据库名称和表名不能为空"
        
        if not os.path.exists(db_name):
            return False, "数据库文件不存在"
        
        try:
            engine, table_obj, metadata = DatabaseEditor._get_engine_and_table(db_name, table_name)
            
            # 检查表是否存在
            if not DatabaseEditor._table_exists(engine, table_name):
                engine.dispose()
                return False, f"表 '{table_name}' 不存在"
            
            # 删除表
            table_obj.drop(engine)
            engine.dispose()
            return True, "删除数据表成功"
            
        except SQLAlchemyError as e:
            return False, f"删除数据表失败: {e}"
        except Exception as e:
            return False, f"删除数据表失败: {e}"

    # ================ 写入数据库 ================
    def write(self, db_name: str, table_name: str, data_id: str, content: str) -> tuple[bool, str]:
        """
        写入数据到数据库，如果ID已存在则更新内容（UPSERT操作）
        :param db_name: 数据库名称
        :param table_name: 数据表名称
        :param data_id: 数据ID
        :param content: 内容
        :return: 是否成功
        :error: 数据库名称不能为空
        :error: 表名不能为空
        :error: 数据ID不能为空
        """
        if not all([db_name, table_name, data_id]):
            return False, "数据库名称、表名和数据ID不能为空"
        
        # 允许 content 为空字符串
        if content is None:
            return False, "内容不能为 None"
        
        if not os.path.exists(db_name):
            return False, "数据库文件不存在"

        try:
            engine, table_obj, metadata = DatabaseEditor._get_engine_and_table(db_name, table_name)
            
            # 创建表（如果不存在）
            metadata.create_all(engine)
            
            # 插入或更新数据（UPSERT）
            with engine.connect() as conn:
                stmt = insert(table_obj).values(id=data_id, content=content)
                # SQLite 3.24+ 支持 ON CONFLICT
                stmt = stmt.on_conflict_do_update(
                    index_elements=['id'],  # 冲突检测列
                    set_={'content': content}  # 更新的值
                )
                conn.execute(stmt)
                conn.commit()
            
            engine.dispose()
            return True, "写入数据库成功"
            
        except SQLAlchemyError as e:
            return False, f"写入数据库失败: {e}"
        except Exception as e:
            return False, f"写入数据库失败: {e}"

    # ================ 读取数据库 ================
    def read(self, db_name: str, table_name: str, data_id: str) -> tuple[bool, str]:
        """
        从指定表中读取数据
        :param db_name: 数据库名称
        :param table_name: 数据表名称
        :param data_id: 数据ID
        :return: 是否成功
        :error: 数据库名称不能为空
        :error: 表名不能为空
        :error: 数据ID不能为空
        """
        if not all([db_name, table_name, data_id]):
            return False, "数据库名称、表名和数据ID不能为空"
        
        if not os.path.exists(db_name):
            return False, "数据库文件不存在"

        try:
            engine, table_obj, _ = DatabaseEditor._get_engine_and_table(db_name, table_name)
            
            # 检查表是否存在
            if not DatabaseEditor._table_exists(engine, table_name):
                engine.dispose()
                return False, f"表 '{table_name}' 不存在"
            
            # 查询数据
            with engine.connect() as conn:
                stmt = select(table_obj.c.content).where(table_obj.c.id == data_id)
                result = conn.execute(stmt).fetchone()
                
                if result:
                    content = result[0]
                    engine.dispose()
                    return True, content
                else:
                    engine.dispose()
                    return False, f"数据ID '{data_id}' 不存在"
                    
        except SQLAlchemyError as e:
            return False, f"读取数据库失败: {e}"
        except Exception as e:
            return False, f"读取数据库失败: {e}"

    # ================ 列出所有表 ================
    def list_tables(self, db_name: str) -> tuple[bool, list]:
        """
        列出数据库中的所有表
        :param db_name: 数据库名称
        :return: 表名列表
        :error: 数据库名称不能为空
        """
        if not db_name:
            return False, []
        
        if not os.path.exists(db_name):
            return False, []
        
        try:
            engine = create_engine(f'sqlite:///{db_name}')
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            engine.dispose()
            return True, tables
        except Exception as e:
            return False, []

    # ================ 列出表中所有数据 ================
    def list_all_data(self, db_name: str, table_name: str) -> tuple[bool, list]:
        """
        列出表中的所有数据
        :param db_name: 数据库名称
        :param table_name: 数据表名称
        :return: 数据列表
        :error: 数据库名称不能为空
        :error: 表名不能为空
        """
        if not all([db_name, table_name]):
            return False, []
        
        if not os.path.exists(db_name):
            return False, []
        
        try:
            engine, table_obj, _ = DatabaseEditor._get_engine_and_table(db_name, table_name)
            
            if not DatabaseEditor._table_exists(engine, table_name):
                engine.dispose()
                return False, []
            
            with engine.connect() as conn:
                stmt = select(table_obj)
                results = conn.execute(stmt).fetchall()
                data = [{'id': row[0], 'content': row[1]} for row in results]
            
            engine.dispose()
            return True, data
            
        except Exception as e:
            return False, []

    # ================ 获取记录数 ================
    def count_records(self, db_name: str, table_name: str) -> tuple[bool, int]:
        """
        获取表中的记录数
        :param db_name: 数据库名称
        :param table_name: 数据表名称
        :return: 记录数
        :error: 数据库名称不能为空
        :error: 表名不能为空
        """
        if not all([db_name, table_name]):
            return False, 0
        
        if not os.path.exists(db_name):
            return False, 0
        
        try:
            engine, table_obj, _ = DatabaseEditor._get_engine_and_table(db_name, table_name)
            
            if not DatabaseEditor._table_exists(engine, table_name):
                engine.dispose()
                return False, 0
            
            with engine.connect() as conn:
                stmt = select(func.count()).select_from(table_obj)
                count = conn.scalar(stmt)
            
            engine.dispose()
            return True, count if count else 0
            
        except Exception as e:
            return False, 0

    # ================ 检查数据是否存在 ================
    def data_exists(self, db_name: str, table_name: str, data_id: str) -> tuple[bool, bool]:
        """
        检查数据是否存在
        :param db_name: 数据库名称
        :param table_name: 数据表名称
        :param data_id: 数据ID
        :return: 是否存在
        :error: 数据库名称不能为空
        :error: 表名不能为空
        :error: 数据ID不能为空
        """
        if not all([db_name, table_name, data_id]):
            return False, False
        
        if not os.path.exists(db_name):
            return False, False
        
        try:
            engine, table_obj, _ = DatabaseEditor._get_engine_and_table(db_name, table_name)
            
            if not DatabaseEditor._table_exists(engine, table_name):
                engine.dispose()
                return True, False
            
            with engine.connect() as conn:
                stmt = select(table_obj.c.id).where(table_obj.c.id == data_id)
                result = conn.execute(stmt).fetchone()
            
            engine.dispose()
            return True, result is not None
            
        except Exception as e:
            return False, False
