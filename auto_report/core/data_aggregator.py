# src/core/data_aggregator.py
import logging
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)

class DataAggregator:
    """数据聚合中心，收集来自不同Agent的数据"""
    def __init__(self):
        self.data_store = defaultdict(list) # 使用列表存储历史数据

    def add_data(self, source, data_point):
        """添加数据点"""
        timestamp = datetime.now().isoformat()
        self.data_store[source].append({'timestamp': timestamp, 'data': data_point})
        logger.debug(f"Data added from {source}: {str(data_point)[:100]}...") # 打印前100字符

    def get_data_since(self, source, since_datetime):
        """获取自某个时间点以来的特定来源数据"""
        filtered_data = []
        for item in self.data_store.get(source, []):
            if datetime.fromisoformat(item['timestamp']) >= since_datetime:
                filtered_data.append(item['data'])
        return filtered_data

    def get_all_data(self):
        """获取所有数据 (用于报告生成) - 保持不变"""
        return dict(self.data_store) # 返回副本

    # --- 新增方法：获取原始存储数据，包含时间戳 ---
    def get_raw_data_since(self, since_datetime):
        """
        获取自某个时间点以来的所有原始数据（包含时间戳）。
        这对于 AnalyzerAgent 进行时间范围内的统一分析非常有用。
        """
        filtered_data = defaultdict(list)
        for source, data_points in self.data_store.items():
            for item in data_points:
                if datetime.fromisoformat(item['timestamp']) >= since_datetime:
                    filtered_data[source].append(item) # 包含 {'timestamp', 'data'}
        return dict(filtered_data)
