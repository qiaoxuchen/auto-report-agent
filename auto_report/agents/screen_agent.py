# src/agents/screen_agent.py
import os
import time
import logging
from PIL import ImageGrab # 或使用 DXcam
import pytesseract
from datetime import datetime

logger = logging.getLogger(__name__)

class ScreenCaptureAgent:
    def __init__(self, config, data_aggregator):
        self.config = config
        self.interval = config.get('interval', 300)
        self.output_dir = config.get('output_dir', './data/screenshots')
        self.data_aggregator = data_aggregator
        os.makedirs(self.output_dir, exist_ok=True)
        logger.info(f"ScreenCaptureAgent initialized with interval {self.interval}s, output to {self.output_dir}")

    def capture_and_analyze(self):
        """截屏并进行简单OCR分析"""
        try:
            # 截屏
            screenshot = ImageGrab.grab()
            timestamp = int(time.time())
            filename = os.path.join(self.output_dir, f"screenshot_{timestamp}.png")
            screenshot.save(filename)
            logger.debug(f"Screenshot saved: {filename}")

            # OCR (简化处理)
            text = pytesseract.image_to_string(screenshot)
            logger.debug(f"OCR Text extracted (first 100 chars): {text[:100]}...")

            # 将分析结果存入数据聚合器
            # 注意：这里调用的是 DataAggregator 的 add_data 方法
            analysis_result = {
                "filename": filename,
                "timestamp": datetime.now().isoformat(),
                "extracted_text_snippet": text[:500] # 增加一点长度，供分析使用
            }
            self.data_aggregator.add_data('screen', analysis_result)

        except Exception as e:
            logger.error(f"Error in screen capture/analysis: {e}")

    def start_periodic_capture(self, scheduler):
        """通过调度器启动周期性任务"""
        logger.info("Starting periodic screen capture task.")
        scheduler.add_job(self.capture_and_analyze, 'interval', seconds=self.interval, id='screen_capture_job')
