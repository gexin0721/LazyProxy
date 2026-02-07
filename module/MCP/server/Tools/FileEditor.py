# -*- coding: utf-8 -*-
import os
import json
import sys

# 添加上层目录到路径，以便导入 tools 模块
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../../')))
from tools import logger


class FileEditor:

    # ================ 读取行 ================
    def read_line(self, filepath, line_num,_encoding='utf-8'):
        """
        读取指定行内容
        :param filepath: 文件路径
        :param line_num: 行号
        :param _encoding: 文件编码
        :return: 指定行内容
        :error: 文件不存在
        """
        # 
        if not os.path.exists(filepath):
            return False
        with open(filepath, 'r', encoding=_encoding) as f:
            lines = f.readlines()
            if 0 < line_num <= len(lines):
                return lines[line_num - 1].rstrip('\n')
            return None

    # ================ 读取所有行 ================
    def read_all(self, filepath,_encoding='utf-8'):
        """
        读取所有行内容
        :param filepath: 文件路径
        :param _encoding: 文件编码
        :return: 所有行内容
        :error: 文件不存在
        """
        if not os.path.exists(filepath):
            return False
        # 读取文件
        with open(filepath, 'r', encoding=_encoding) as f:
            return [line.rstrip('\n') for line in f.readlines()]

    # ================ 更新行 ================
    def update_line(self, filepath, line_num, content,_encoding='utf-8'):
        """
        更新指定行内容
        :param filepath: 文件路径
        :param line_num: 行号
        :param content: 内容
        :param _encoding: 文件编码
        :return: 是否成功
        :error: 文件不存在
        """
        if not os.path.exists(filepath):
            return False
        # 读取文件
        with open(filepath, 'r', encoding=_encoding) as f:
            lines = f.readlines()
        # 更新行
        if 0 < line_num <= len(lines):
            lines[line_num - 1] = content + '\n'
            with open(filepath, 'w', encoding=_encoding) as f:
                f.writelines(lines)
            return True
        return False

    # ================ 删除行 ================
    def delete_line(self, filepath, line_num,_encoding='utf-8'):
        """
        删除指定行内容
        :param filepath: 文件路径
        :param line_num: 行号
        :param _encoding: 文件编码
        :return: 是否成功
        :error: 文件不存在
        """
        if not os.path.exists(filepath):
            return False
        # 读取文件
        with open(filepath, 'r', encoding=_encoding) as f:
            lines = f.readlines()
        # 删除行
        if 0 < line_num <= len(lines):
            del lines[line_num - 1]
            with open(filepath, 'w', encoding=_encoding) as f:
                f.writelines(lines)
            return True
        return False

    # ================ 插入行 ================
    def insert_line(self, filepath, line_num, content,_encoding='utf-8'):
        """
        插入指定行内容
        :param filepath: 文件路径
        :param line_num: 行号
        :param content: 内容
        :param _encoding: 文件编码
        :return: 是否成功
        :error: 文件不存在
        """
        if not os.path.exists(filepath):
            return False

        # 读取现有内容
        with open(filepath, 'r', encoding=_encoding) as f:
            lines = f.readlines()
        
        # 插入新行
        if 0 < line_num <= len(lines) + 1:
            lines.insert(line_num - 1, content + '\n')
            with open(filepath, 'w', encoding=_encoding) as f:
                f.writelines(lines)
            return True
        return False

    # ================ 追加行 ================
    def append_line(self, filepath, content,_encoding='utf-8'):
        """
        追加行内容
        :param filepath: 文件路径
        :param content: 内容
        :param _encoding: 文件编码
        :return: 是否成功
        :error: 文件不存在
        """
        if not os.path.exists(filepath):
            return False
        # 追加行
        with open(filepath, 'a', encoding=_encoding) as f:
            f.write(content + '\n')

    # # ================ 添加行（批量） ================
    # def add_arr(self,filepath,batch:dict, _encoding='utf-8'):
    #     """
    #     添加行（批量）
    #     :param filepath: 文件路径
    #     :param batch: 批量数据:dict，如：{"line_num": "行号", "content": "内容"}
    #     :param _encoding: 文件编码
    #     :return: 是否成功
    #     :error: 文件不存在
    #     """
    #     if not os.path.exists(filepath):
    #         return False
    #     # 添加行
    #     for f : batch:


    # ================ 清空文件 ================
    def clear_file(self, filepath,_encoding='utf-8'):
        """
        清空文本文件内容
        :param filepath: 文件路径
        :param _encoding: 文件编码
        :return: 是否成功
        :error: 文件不存在
        """
        # 如果文件不存在，无法清空
        if not os.path.exists(filepath):
            return False

        # 清空文件
        with open(filepath, 'w', encoding=_encoding) as f: # 用'w'模式写入。只写模式打开文件，或文件存在，会清空原有内容，即覆盖写
            pass


    # ================ JSON文件操作 ================
    #  -------------- 读取JSON文件 --------------
    def read_JSON(self, filepath,_encoding='utf-8'):
        """
        读取JSON文件
        :param filepath: 文件路径
        :param _encoding: 文件编码
        :return: JSON数据
        :error: 文件不存在
        """
        # 如果文件不存在，无法读取
        if not os.path.exists(filepath):
            return None
        try:
          # 读取文件
          with open(filepath, 'r', encoding=_encoding) as f:
              return json.load(f)
        except Exception as e:
          logger.error(f"读取JSON文件失败: {e}")
          return None

    
    #  -------------- 写入JSON文件 --------------
    def write_JSON(self, filepath, data, _encoding='utf-8'):
        """
        写入JSON文件（覆盖）
        :param filepath: 文件路径
        :param data: JSON数据
        :param _encoding: 文件编码
        :return: 是否成功
        :error: 文件不存在
        """
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(filepath) or '.', exist_ok=True)
            
            # 用'w'模式写入
            with open(filepath, 'w', encoding=_encoding) as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"写入JSON失败: {e}")
            return False
             
    #  -------------- 追加数据(历史记录)-JSON文件 --------------
    def append_JSON(self, filepath,append_data:dict, _encoding='utf-8'):
        """
        追加数据到JSON文件。
        数据格式为对话历史列表，如：
        [
            {"role": "user", "content": "推荐一部关于太空探索的科幻电影。"},
            {"role": "assistant", "content": "我推荐《xxx》，这是一部经典的科幻作品。"},
            {"role": "user", "content": "这部电影的导演是谁？"}
        ]
        :param filepath: JSON文件路径
        :param append_data: 要追加的字典元素（如对话消息：{"role": "user", "content": "内容"}）
        :param _encoding: 文件编码
        :return: 返回追加后的历史列表，或None（出错）
        :error: 文件不存在
        """
        # 步骤1：检查文件是否存在
        if not os.path.exists(filepath):
            return None

        # 步骤2：确保追加数据有效
        if not append_data:
            return None  # 必须传递数据

        # 步骤3：读取当前历史
        try:
            with open(filepath, 'r', encoding=_encoding) as f:
                buffer = json.load(f)
        except Exception as e:
            # 无法读取或json格式出错
            return None

        # 步骤4：检测格式（为对话历史列表，每条是{"role":.., "content":..}）
        if not isinstance(buffer, list):
            return None  # 文件内容必须为列表
        if not ("role" in append_data and "content" in append_data):
            return None  # 追加内容必须有role和content字段
        if append_data["role"] not in {"user", "assistant", "system"}:
            return None  # 角色只能是三种之一

        # 步骤5：追加数据
        buffer.append(append_data)

        # 步骤6：写回文件
        try:
            with open(filepath, 'w', encoding=_encoding) as f:
                json.dump(buffer, f, ensure_ascii=False, indent=2)
        except Exception as e:
            return None

        return buffer
      