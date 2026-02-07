from fastmcp import FastMCP
from fastmcp.tools import Tool
import os
import json

from Tools.DatabaseEditor import DatabaseEditor
from Tools.DataInquire import DataInquire
from Tools.FileEditor import FileEditor
from Tools.WorkspaceManager import WorkspaceManager
from Tools.TaskManager import TaskManager
from Tools.mathematics import mathematics

class MCPServer:
    def __init__(self):
        # 创建MCP服务器节点
        self.mcp = FastMCP("测试服务器")

        self.database_editor = DatabaseEditor()
        self.data_inquire = DataInquire()
        self.file_editor = FileEditor()
        self.workspace_manager = WorkspaceManager()
        self.task_manager = TaskManager()
        self.mathematics = mathematics()
        self.add_tool()

    # ==================== 启动服务器 ====================
    def start(self):
        """启动服务器"""
        self.mcp.run()

    # ==================== 停止服务器 ====================
    def stop(self):
        """停止服务器"""
        self.mcp.close()

    # ==================== 重启服务器 ====================
    def restart(self):
        """重启服务器"""
        self.stop()
        self.start()

    # ==================== 添加工具 ====================
    def add_tool(self):
        """注册所有工具到MCP服务器"""
        # DatabaseEditor 工具 —— 数据库操作工具
        # self.mcp.add_tool(Tool.from_function(self.database_editor.connect))
        # self.mcp.add_tool(Tool.from_function(self.database_editor.delete))
        # self.mcp.add_tool(Tool.from_function(self.database_editor.insert_data))
        # self.mcp.add_tool(Tool.from_function(self.database_editor.update_data))
        # self.mcp.add_tool(Tool.from_function(self.database_editor.delete_data))
        # self.mcp.add_tool(Tool.from_function(self.database_editor.create_table))
        # self.mcp.add_tool(Tool.from_function(self.database_editor.delete_table))
        # self.mcp.add_tool(Tool.from_function(self.database_editor.write))
        # self.mcp.add_tool(Tool.from_function(self.database_editor.read))
        # self.mcp.add_tool(Tool.from_function(self.database_editor.list_tables))
        # self.mcp.add_tool(Tool.from_function(self.database_editor.list_all_data))
        # self.mcp.add_tool(Tool.from_function(self.database_editor.count_records))
        # self.mcp.add_tool(Tool.from_function(self.database_editor.data_exists))

        # # DataInquire 工具 —— 文件操作工具
        # self.mcp.add_tool(Tool.from_function(self.data_inquire.file_directory))
        # self.mcp.add_tool(Tool.from_function(self.data_inquire.file_content))
        # self.mcp.add_tool(Tool.from_function(self.data_inquire.file_line_count))
        # self.mcp.add_tool(Tool.from_function(self.data_inquire.file_content_fuzzy))
        # self.mcp.add_tool(Tool.from_function(self.data_inquire.database_all_table))
        # self.mcp.add_tool(Tool.from_function(self.data_inquire.database_table_content))
        # self.mcp.add_tool(Tool.from_function(self.data_inquire.database_table_data_exists))
        # self.mcp.add_tool(Tool.from_function(self.data_inquire.database_content_fuzzy))
        # self.mcp.add_tool(Tool.from_function(self.data_inquire.database_table_data_count))
        # self.mcp.add_tool(Tool.from_function(self.data_inquire.database_table_data_batch))
        # self.mcp.add_tool(Tool.from_function(self.data_inquire.database_table_data_filter))

        # # FileEditor 工具 —— 文件操作工具
        # self.mcp.add_tool(Tool.from_function(self.file_editor.read_line))
        # self.mcp.add_tool(Tool.from_function(self.file_editor.read_all))
        # self.mcp.add_tool(Tool.from_function(self.file_editor.update_line))
        # self.mcp.add_tool(Tool.from_function(self.file_editor.delete_line))
        # self.mcp.add_tool(Tool.from_function(self.file_editor.insert_line))
        # self.mcp.add_tool(Tool.from_function(self.file_editor.append_line))
        # self.mcp.add_tool(Tool.from_function(self.file_editor.clear_file))
        # self.mcp.add_tool(Tool.from_function(self.file_editor.read_JSON))
        # self.mcp.add_tool(Tool.from_function(self.file_editor.write_JSON))
        # self.mcp.add_tool(Tool.from_function(self.file_editor.append_JSON))

        # WorkspaceManager 工具 —— 工作空间管理工具
        # self.mcp.add_tool(Tool.from_function(self.workspace_manager.scan_workspace))
        # self.mcp.add_tool(Tool.from_function(self.workspace_manager.search_files))
        # self.mcp.add_tool(Tool.from_function(self.workspace_manager.get_file_metadata))
        # self.mcp.add_tool(Tool.from_function(self.workspace_manager.list_files_simple))

        # # TaskManager 工具
        self.mcp.add_tool(Tool.from_function(self.task_manager.exit_task)) #退出任务
        self.mcp.add_tool(Tool.from_function(self.task_manager.plan_task)) #规划任务
        self.mcp.add_tool(Tool.from_function(self.task_manager.generate_todo_list)) #生成TODO列表


        # Mathematics 工具 —— 数学工具
        self.mcp.add_tool(Tool.from_function(self.mathematics.add))
        self.mcp.add_tool(Tool.from_function(self.mathematics.subtract))
        self.mcp.add_tool(Tool.from_function(self.mathematics.multiply))
        self.mcp.add_tool(Tool.from_function(self.mathematics.divide))
        self.mcp.add_tool(Tool.from_function(self.mathematics.power))
        self.mcp.add_tool(Tool.from_function(self.mathematics.sqrt))
if __name__ == "__main__":
    _MCPServer = MCPServer()
    _MCPServer.start()