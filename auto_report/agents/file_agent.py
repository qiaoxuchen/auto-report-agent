# src/agents/file_agent.py
import os
import logging
import json
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)

class LogFileHandler(FileSystemEventHandler):
    def __init__(self, log_callback):
        self.log_callback = log_callback

    def on_any_event(self, event):
        if not event.is_directory:
            # 记录事件信息
            event_info = {
                "event_type": event.event_type,
                "src_path": event.src_path,
                "is_directory": event.is_directory,
                "timestamp": datetime.now().isoformat()
            }
            self.log_callback(event_info)

class FileMonitorAgent:
    def __init__(self, config, data_aggregator):
        self.config = config
        self.watch_path = config.get('watch_path')
        self.data_aggregator = data_aggregator
        if not self.watch_path or not os.path.exists(self.watch_path):
             logger.error(f"Invalid or non-existent watch path: {self.watch_path}")
             raise ValueError(f"Invalid or non-existent watch path: {self.watch_path}")

        self.observer = Observer()
        self.log_file_handler = LogFileHandler(self._log_event_to_aggregator)
        self.log_file_path = os.path.join('data', 'file_logs', 'file_events.log')
        os.makedirs(os.path.dirname(self.log_file_path), exist_ok=True)
        logger.info(f"FileMonitorAgent initialized for path: {self.watch_path}")

    def _log_event_to_aggregator(self, event_info):
        """记录文件事件到聚合器 (不再写入单独的日志文件)"""
        # 直接添加到数据聚合器
        # 注意：这里调用的是 DataAggregator 的 add_data 方法
        self.data_aggregator.add_data('file', event_info)
        logger.info(f"File event logged to aggregator: {event_info['event_type']} - {event_info['src_path']}")

    def start_monitoring(self):
        """启动文件监控"""
        self.observer.schedule(self.log_file_handler, self.watch_path, recursive=True)
        self.observer.start()
        logger.info("File monitoring started.")

    def stop_monitoring(self):
        """停止文件监控"""
        self.observer.stop()
        self.observer.join()
        logger.info("File monitoring stopped.")
