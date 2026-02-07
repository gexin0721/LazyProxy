# -*- coding: utf-8 -*-
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict


class AllEventsHandler(FileSystemEventHandler):
    """监控 Data 文件夹，将所有变化记录到内存字典"""
    
    def __init__(self):
        self.events = []  # 内存存储事件列表
        self.observer = None  # Observer 实例
        self.is_running = False  # 监控状态
    
    def start_monitoring(self, watch_path: str, recursive: bool = True):
        """启动监控
        
        Args:
            watch_path: 要监控的路径
            recursive: 是否递归监控子目录
        """
        if self.is_running:
            print(" 监控已在运行中")
            return
        
        # 检查路径是否存在
        path = Path(watch_path)
        if not path.exists():
            raise FileNotFoundError(f"路径不存在: {watch_path}")
        
        # 创建并启动 Observer
        self.observer = Observer()
        self.observer.schedule(self, watch_path, recursive=recursive)
        self.observer.start()
        self.is_running = True
        print(f"✓ 开始监控: {watch_path}")
    
    def stop_monitoring(self):
        """停止监控"""
        if not self.is_running or not self.observer:
            print(" 监控未运行")
            return
        
        self.observer.stop()
        self.observer.join()
        self.is_running = False
        print("✓ 已停止监控")
    
    def _record_event(self, event_type: str, src_path: str, 
                     dest_path: str = None, is_directory: bool = False):
        """记录事件到内存"""
        event_record = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "event_type": event_type,
            "item_type": "directory" if is_directory else "file",
            "src_path": src_path
        }
        
        if dest_path:
            event_record["dest_path"] = dest_path
        
        self.events.append(event_record)
    
    def get_events(self) -> List[Dict]:
        """获取所有事件并清空"""
        events_copy = self.events.copy()
        self.events.clear()
        return events_copy
    
    # 创建事件
    def on_created(self, event):
        self._record_event("created", event.src_path, is_directory=event.is_directory)
    
    # 删除事件
    def on_deleted(self, event):
        self._record_event("deleted", event.src_path, is_directory=event.is_directory)
    
    # 修改事件
    def on_modified(self, event):
        self._record_event("modified", event.src_path, is_directory=event.is_directory)
    
    # 移动事件
    def on_moved(self, event):
        self._record_event("moved", event.src_path, 
                              dest_path=event.dest_path, 
                              is_directory=event.is_directory)

# 创建监控器
monitor = AllEventsHandler()
# ================ 测试代码 ================
if __name__ == "__main__":
    watch_path = "./Data"
    

    
    try:
        # 启动监控
        monitor.start_monitoring(watch_path, recursive=True)
        print(" 记录: 内存队列")
        print("按 Ctrl+C 停止\n")
        
        # 循环获取事件
        while True:
            time.sleep(5)  # 每5秒检查一次
            events = monitor.get_events()
            if events:
                print(f"\n 获取到 {len(events)} 个事件:")
                for event in events:
                    print(f"  - [{event['timestamp']}] {event['event_type']}: {event['src_path']}")
    
    except FileNotFoundError as e:
        print(f" 错误: {e}")
        print(f"   当前目录: {Path.cwd()}")
        print(f"   绝对路径: {Path(watch_path).absolute()}")
    
    except KeyboardInterrupt:
        print("\n⏹正在停止...")
    
    finally:
        monitor.stop_monitoring()