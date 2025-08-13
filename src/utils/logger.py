# src/utils/logger.py
import logging
import os

def setup_logger(config):
    """设置日志"""
    log_level = getattr(logging, config.get('level', 'INFO').upper(), logging.INFO)
    log_file = config.get('file')

    # 创建日志记录器
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 如果配置了文件路径，则添加文件处理器
    if log_file:
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logging.info("Logger configured.")