# src/core/scheduler.py
import logging

logger = logging.getLogger(__name__)

def setup_schedulers(scheduler, screen_agent, file_agent, lark_agent, report_agent, report_config):
    """设置所有定时任务"""
    try:
        # 启动屏幕监控任务
        if screen_agent:
            screen_agent.start_periodic_capture(scheduler)
            logger.info("Screen capture job scheduled.")

        # 启动文件监控 (持续运行，由FileMonitorAgent内部管理)
        # 文件监控在main.py中启动和停止

        # 设置报告生成和发送任务
        schedule_config = report_config.get('schedule', {})
        daily_cron = schedule_config.get('daily')
        weekly_cron = schedule_config.get('weekly')

        if daily_cron and report_agent:
            scheduler.add_job(report_agent.generate_and_send_daily, 'cron',
                              minute=daily_cron.split()[0],
                              hour=daily_cron.split()[1],
                              day=daily_cron.split()[2],
                              month=daily_cron.split()[3],
                              day_of_week=daily_cron.split()[4],
                              id='daily_report_job')
            logger.info(f"Daily report job scheduled: {daily_cron}")

        if weekly_cron and report_agent:
            scheduler.add_job(report_agent.generate_and_send_weekly, 'cron',
                              minute=weekly_cron.split()[0],
                              hour=weekly_cron.split()[1],
                              day=weekly_cron.split()[2],
                              month=weekly_cron.split()[3],
                              day_of_week=weekly_cron.split()[4],
                              id='weekly_report_job')
            logger.info(f"Weekly report job scheduled: {weekly_cron}")

    except Exception as e:
        logger.error(f"Error setting up schedulers: {e}")
        raise