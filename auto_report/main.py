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
from agents.document_agent import DocumentReaderAgent
from agents.api_agent import LarkDataAgent
from agents.analyzer_agent import AnalyzerAgent  # 新增导入
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
    sys.exit(0)


def main():
    """主函数"""
    config = load_config()
    setup_logger(config.get('core', {}).get('logging', {}))
    logger = logging.getLogger(__name__)
    logger.info("Starting AutoReport Agent...")
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    data_aggregator = DataAggregator()

    # --- 按模块化配置初始化各数据采集Agent ---
    data_sources_config = config.get('data_sources', {})

    screen_agent = ScreenCaptureAgent(
        data_sources_config.get('screen_capture', {}),
        data_aggregator
    ) if data_sources_config.get('screen_capture', {}).get('enabled', False) else None

    file_agent = FileMonitorAgent(
        data_sources_config.get('file_monitor', {}),
        data_aggregator
    ) if data_sources_config.get('file_monitor', {}).get('enabled', False) else None

    document_agent = DocumentReaderAgent(
        data_sources_config.get('document_reader', {}),
        data_aggregator
    ) if data_sources_config.get('document_reader', {}).get('enabled', False) else None

    lark_agent = LarkDataAgent(
        data_sources_config.get('third_party_apis', {}).get('lark', {}),
        data_aggregator
    ) if data_sources_config.get('third_party_apis', {}).get('lark', {}).get('enabled', False) else None

    # --- 初始化核心分析Agent ---
    analyzer_agent = AnalyzerAgent(config, data_aggregator)

    scheduler = BlockingScheduler()
    # 传递所有Agent给调度器
    setup_schedulers(
        scheduler,
        screen_agent,
        file_agent,
        document_agent,
        lark_agent,
        analyzer_agent,  # 传递 analyzer_agent
        config
    )

    # --- 启动需要持续运行的监控/扫描任务 ---
    if file_agent:
        file_agent.start_monitoring()
    if document_agent:
        document_agent.start_periodic_scan(scheduler)

    try:
        logger.info("AutoReport Agent is running. Press Ctrl+C to exit.")
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Shutting down AutoReport Agent...")
        scheduler.shutdown()
        if file_agent:
            file_agent.stop_monitoring()
        logger.info("AutoReport Agent shut down.")


if __name__ == '__main__':
    main()