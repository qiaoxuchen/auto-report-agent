# src/agents/document_agent.py
import os
import logging
from datetime import datetime
import mimetypes

logger = logging.getLogger(__name__)


class DocumentReaderAgent:
    """
    文档读取代理。
    读取指定文件夹下的文本文件，并将内容发送到数据聚合器。
    """

    def __init__(self, config, data_aggregator):
        self.config = config
        self.watch_path = config.get('watch_path')
        self.data_aggregator = data_aggregator
        self.supported_extensions = config.get('supported_extensions', ['.txt'])
        self.scan_interval = config.get('scan_interval', 3600)  # 默认1小时

        if not self.watch_path or not os.path.exists(self.watch_path):
            if config.get('enabled', False):  # 仅在启用时才警告
                logger.error(f"Invalid or non-existent document watch path: {self.watch_path}")
                raise ValueError(f"Invalid or non-existent document watch path: {self.watch_path}")
            else:
                logger.info("DocumentReaderAgent is disabled.")
                self.watch_path = None  # 确保不会被意外使用

        self._last_scan_time = None
        self._scanned_files = {}  # {filepath: mtime} 记录已扫描文件的修改时间

        logger.info(
            f"DocumentReaderAgent initialized. Watch path: {self.watch_path}, Supported extensions: {self.supported_extensions}")

    def _is_supported_file(self, filepath):
        """检查文件是否为支持的文本类型"""
        _, ext = os.path.splitext(filepath)
        return ext.lower() in self.supported_extensions

    def _read_file_content(self, filepath):
        """尝试以文本方式读取文件内容"""
        # 尝试几种常见的编码
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
        for encoding in encodings:
            try:
                with open(filepath, 'r', encoding=encoding) as f:
                    content = f.read()
                logger.debug(f"Successfully read {filepath} with encoding {encoding}")
                return content
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.warning(f"Error reading {filepath} with encoding {encoding}: {e}")
                break  # 其他错误直接跳出

        logger.warning(f"Failed to read {filepath} as text with common encodings.")
        return f"[Error: Could not read file {filepath} as text]"

    def scan_and_aggregate(self):
        """扫描目录并聚合文档内容"""
        if not self.watch_path:
            return

        current_time = datetime.now()
        logger.info(f"Starting document scan in {self.watch_path}...")

        try:
            for root, _, files in os.walk(self.watch_path):
                for file in files:
                    filepath = os.path.join(root, file)
                    if self._is_supported_file(filepath):
                        try:
                            # 检查文件是否已存在且未修改
                            stat = os.stat(filepath)
                            mtime = stat.st_mtime

                            if filepath in self._scanned_files and self._scanned_files[filepath] == mtime:
                                logger.debug(f"File {filepath} unchanged, skipping.")
                                continue

                            content = self._read_file_content(filepath)

                            # 将文档信息存入数据聚合器
                            # 注意：这里调用的是 DataAggregator 的 add_data 方法
                            doc_info = {
                                "filename": os.path.relpath(filepath, self.watch_path),  # 相对路径更清晰
                                "full_path": filepath,
                                "size": stat.st_size,
                                "last_modified": datetime.fromtimestamp(mtime).isoformat(),
                                "content_snippet": content[:1000] + ("..." if len(content) > 1000 else ""),  # 增加片段长度
                                # "full_content": content # 如果需要传递全文给大模型，可以取消注释，但注意数据量
                            }
                            self.data_aggregator.add_data('document', doc_info)
                            self._scanned_files[filepath] = mtime
                            logger.debug(f"Document content aggregated from: {filepath}")

                        except Exception as e:
                            logger.error(f"Error processing file {filepath}: {e}")

            self._last_scan_time = current_time
            logger.info("Document scan and aggregation completed.")

        except Exception as e:
            logger.error(f"Error during document scan: {e}")

    def start_periodic_scan(self, scheduler):
        """通过调度器启动周期性扫描任务"""
        if self.scan_interval > 0 and self.watch_path:
            logger.info(f"Starting periodic document scan task every {self.scan_interval} seconds.")
            scheduler.add_job(self.scan_and_aggregate, 'interval', seconds=self.scan_interval, id='document_scan_job')
        elif self.watch_path:
            # 如果间隔<=0，只在启动时扫描一次
            logger.info("Document scan task will run once at startup only.")
            self.scan_and_aggregate()  # 立即执行一次
