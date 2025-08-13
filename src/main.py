# src/main.py
import os
import logging
import signal
import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from core.scheduler import setup_schedulers
from core.data_aggregator import DataAggregator
from agents.screen_agent import ScreenCaptureAgent
from agents.file_agent import FileMonitorAgent
from agents.api_agent import LarkDataAgent
from agents.report_agent import ReportGeneratorAgent
from utils.logger import setup_logger
import yaml


def load_config(config_path='../config/config.yaml'):
    """加载配置文件"""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file {config_path} not found. Please create it from the template.")
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def signal_handler(sig, frame):
    """优雅关闭信号处理"""
    logger = logging.getLogger(__name__)
    logger.info("Received shutdown signal. Shutting down gracefully...")
    # 这里可以添加清理逻辑，如停止文件监控
    sys.exit(0)

def main():
    """主函数"""
    # 加载配置
    config = load_config()

    # 设置日志
    setup_logger(config.get('logging', {}))
    logger = logging.getLogger(__name__)
    logger.info("Starting AutoReport Agent...")

    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # 初始化核心组件
    data_aggregator = DataAggregator()

    # 初始化各Agent (根据配置决定是否启用)
    screen_agent = ScreenCaptureAgent(config.get('screen_capture', {}), data_aggregator) if config.get('screen_capture', {}).get('enabled', False) else None
    file_agent = FileMonitorAgent(config.get('file_monitor', {}), data_aggregator) if config.get('file_monitor', {}).get('enabled', False) else None
    lark_agent = LarkDataAgent(config.get('lark', {}), data_aggregator) if config.get('lark', {}).get('enabled', False) else None
    report_agent = ReportGeneratorAgent(config.get('report', {}), data_aggregator)

    # 设置调度器
    scheduler = BlockingScheduler()
    setup_schedulers(scheduler, screen_agent, file_agent, lark_agent, report_agent, config.get('report', {}))

    try:
        logger.info("AutoReport Agent is running. Press Ctrl+C to exit.")
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Shutting down AutoReport Agent...")
        scheduler.shutdown()
        if file_agent:
            file_agent.stop_monitoring() # 停止文件监控
        logger.info("AutoReport Agent shut down.")

if __name__ == '__main__':
    main()