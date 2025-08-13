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
        logger.debug(f"Data added from {source}: {data_point}")

    def get_data_since(self, source, since_datetime):
        """获取自某个时间点以来的数据"""
        # 简化实现，实际可能需要更高效的查询
        filtered_data = []
        for item in self.data_store.get(source, []):
            if datetime.fromisoformat(item['timestamp']) >= since_datetime:
                filtered_data.append(item['data'])
        return filtered_data

    def get_all_data(self):
        """获取所有数据 (用于报告生成)"""
        return dict(self.data_store) # 返回副本