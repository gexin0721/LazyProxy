# -*- coding: utf-8 -*-
import os
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime

class WorkspaceManager:
    """
    工作区管理工具
    提供文件扫描、搜索、元数据获取等功能
    """

    def __init__(self):
        pass

    def scan_workspace(self, directory: str, max_depth: int = 3, include_hidden: bool = False) -> Dict:
        """
        扫描工作区目录，返回文件树结构

        参数:
            directory: 要扫描的目录路径
            max_depth: 最大扫描深度，默认3层
            include_hidden: 是否包含隐藏文件，默认False

        返回:
            包含文件树结构的字典
        """
        if not directory or directory == "":
            return {"error": "目录路径不能为空"}

        directory = os.path.abspath(directory)

        if not os.path.exists(directory):
            return {"error": f"目录不存在: {directory}"}

        if not os.path.isdir(directory):
            return {"error": f"路径不是目录: {directory}"}

        try:
            result = {
                "root": directory,
                "scanned_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "total_files": 0,
                "total_dirs": 0,
                "structure": []
            }

            # 扫描目录
            structure = self._scan_directory_recursive(
                directory,
                directory,
                current_depth=0,
                max_depth=max_depth,
                include_hidden=include_hidden
            )

            result["structure"] = structure["items"]
            result["total_files"] = structure["file_count"]
            result["total_dirs"] = structure["dir_count"]

            return result

        except Exception as e:
            return {"error": f"扫描目录失败: {str(e)}"}

    def _scan_directory_recursive(self, root_dir: str, current_dir: str,
                                  current_depth: int, max_depth: int,
                                  include_hidden: bool) -> Dict:
        """
        递归扫描目录
        """
        items = []
        file_count = 0
        dir_count = 0

        # 检查深度限制
        if current_depth >= max_depth:
            return {"items": items, "file_count": file_count, "dir_count": dir_count}

        try:
            entries = os.listdir(current_dir)

            for entry in sorted(entries):
                # 跳过隐藏文件
                if not include_hidden and entry.startswith('.'):
                    continue

                full_path = os.path.join(current_dir, entry)
                relative_path = os.path.relpath(full_path, root_dir)

                try:
                    if os.path.isfile(full_path):
                        # 文件
                        file_info = {
                            "type": "file",
                            "name": entry,
                            "path": relative_path,
                            "size": os.path.getsize(full_path),
                            "extension": os.path.splitext(entry)[1],
                            "modified": datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M:%S")
                        }
                        items.append(file_info)
                        file_count += 1

                    elif os.path.isdir(full_path):
                        # 目录
                        dir_info = {
                            "type": "directory",
                            "name": entry,
                            "path": relative_path,
                            "children": []
                        }

                        # 递归扫描子目录
                        sub_result = self._scan_directory_recursive(
                            root_dir,
                            full_path,
                            current_depth + 1,
                            max_depth,
                            include_hidden
                        )

                        dir_info["children"] = sub_result["items"]
                        items.append(dir_info)
                        dir_count += 1 + sub_result["dir_count"]
                        file_count += sub_result["file_count"]

                except (PermissionError, OSError):
                    # 跳过无权限访问的文件/目录
                    continue

        except (PermissionError, OSError):
            pass

        return {"items": items, "file_count": file_count, "dir_count": dir_count}

    def search_files(self, pattern: str, directory: str,
                    search_type: str = "name", max_results: int = 100) -> Dict:
        """
        在目录中搜索文件

        参数:
            pattern: 搜索模式（文件名模式或扩展名）
            directory: 搜索目录
            search_type: 搜索类型 ("name": 文件名, "extension": 扩展名, "content": 文件内容)
            max_results: 最大返回结果数

        返回:
            搜索结果列表
        """
        if not pattern or pattern == "":
            return {"error": "搜索模式不能为空"}

        if not directory or directory == "":
            return {"error": "目录路径不能为空"}

        directory = os.path.abspath(directory)

        if not os.path.exists(directory):
            return {"error": f"目录不存在: {directory}"}

        try:
            results = []
            count = 0

            for root, dirs, files in os.walk(directory):
                # 跳过隐藏目录
                dirs[:] = [d for d in dirs if not d.startswith('.')]

                for file in files:
                    if count >= max_results:
                        break

                    # 跳过隐藏文件
                    if file.startswith('.'):
                        continue

                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, directory)

                    matched = False

                    if search_type == "name":
                        # 文件名匹配（支持通配符）
                        if pattern.lower() in file.lower():
                            matched = True

                    elif search_type == "extension":
                        # 扩展名匹配
                        ext = os.path.splitext(file)[1]
                        if ext.lower() == pattern.lower() or ext.lower() == f".{pattern.lower()}":
                            matched = True

                    elif search_type == "content":
                        # 文件内容匹配（仅文本文件）
                        try:
                            with open(full_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                                if pattern in content:
                                    matched = True
                        except:
                            # 跳过无法读取的文件
                            continue

                    if matched:
                        results.append({
                            "name": file,
                            "path": relative_path,
                            "full_path": full_path,
                            "size": os.path.getsize(full_path),
                            "extension": os.path.splitext(file)[1],
                            "modified": datetime.fromtimestamp(os.path.getmtime(full_path)).strftime("%Y-%m-%d %H:%M:%S")
                        })
                        count += 1

                if count >= max_results:
                    break

            return {
                "pattern": pattern,
                "search_type": search_type,
                "directory": directory,
                "total_results": len(results),
                "results": results
            }

        except Exception as e:
            return {"error": f"搜索文件失败: {str(e)}"}

    def get_file_metadata(self, filepath: str) -> Dict:
        """
        获取文件的详细元数据

        参数:
            filepath: 文件路径

        返回:
            文件元数据字典
        """
        if not filepath or filepath == "":
            return {"error": "文件路径不能为空"}

        filepath = os.path.abspath(filepath)

        if not os.path.exists(filepath):
            return {"error": f"文件不存在: {filepath}"}

        if not os.path.isfile(filepath):
            return {"error": f"路径不是文件: {filepath}"}

        try:
            stat = os.stat(filepath)

            metadata = {
                "name": os.path.basename(filepath),
                "path": filepath,
                "directory": os.path.dirname(filepath),
                "size": stat.st_size,
                "size_human": self._format_size(stat.st_size),
                "extension": os.path.splitext(filepath)[1],
                "created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
                "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "accessed": datetime.fromtimestamp(stat.st_atime).strftime("%Y-%m-%d %H:%M:%S"),
                "is_readable": os.access(filepath, os.R_OK),
                "is_writable": os.access(filepath, os.W_OK),
                "is_executable": os.access(filepath, os.X_OK)
            }

            # 尝试获取文件行数（仅文本文件）
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    metadata["line_count"] = len(lines)
                    metadata["is_text_file"] = True
            except:
                metadata["is_text_file"] = False

            return metadata

        except Exception as e:
            return {"error": f"获取文件元数据失败: {str(e)}"}

    def _format_size(self, size: int) -> str:
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    def list_files_simple(self, directory: str, extensions: Optional[List[str]] = None) -> Dict:
        """
        简单列出目录下的所有文件（扁平化列表）

        参数:
            directory: 目录路径
            extensions: 文件扩展名过滤列表，如 [".txt", ".json"]

        返回:
            文件列表
        """
        if not directory or directory == "":
            return {"error": "目录路径不能为空"}

        directory = os.path.abspath(directory)

        if not os.path.exists(directory):
            return {"error": f"目录不存在: {directory}"}

        try:
            files = []

            for root, dirs, filenames in os.walk(directory):
                # 跳过隐藏目录
                dirs[:] = [d for d in dirs if not d.startswith('.')]

                for filename in filenames:
                    # 跳过隐藏文件
                    if filename.startswith('.'):
                        continue

                    # 扩展名过滤
                    if extensions:
                        ext = os.path.splitext(filename)[1]
                        if ext not in extensions:
                            continue

                    full_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(full_path, directory)

                    files.append({
                        "name": filename,
                        "path": relative_path,
                        "full_path": full_path,
                        "extension": os.path.splitext(filename)[1]
                    })

            return {
                "directory": directory,
                "total_files": len(files),
                "files": files
            }

        except Exception as e:
            return {"error": f"列出文件失败: {str(e)}"}
