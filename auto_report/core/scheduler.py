# src/core/scheduler.py
import logging

logger = logging.getLogger(__name__)

def setup_schedulers(scheduler, screen_agent, file_agent, document_agent, lark_agent, analyzer_agent, config):
    """设置所有定时任务，根据配置开关决定是否启用"""
    try:
        # --- 启动数据采集任务 ---
        if screen_agent:
            screen_agent.start_periodic_capture(scheduler)
            logger.info("Screen capture job scheduled.")

        # file_agent 和 document_agent 的持续任务在 main.py 中启动

        # --- 启动报告分析和发送任务 ---
        report_types_config = config.get('analysis', {}).get('report_types', {})

        for report_type, report_config in report_types_config.items():
            if report_config.get('enabled', False) and analyzer_agent:
                cron_expr = report_config['schedule']
                cron_parts = cron_expr.split()
                if len(cron_parts) != 5:
                    logger.error(f"Invalid cron expression for {report_type}: {cron_expr}")
                    continue

                # 为每个启用的报告类型添加一个调度任务
                scheduler.add_job(
                    # 调用 analyzer_agent 的通用分析方法，并传入报告类型
                    analyzer_agent.analyze_and_report, 'cron',
                    minute=cron_parts[0], hour=cron_parts[1], day=cron_parts[2],
                    month=cron_parts[3], day_of_week=cron_parts[4],
                    id=f'{report_type}_analysis_job',
                    args=[report_type, report_config.get('description', report_type)] # 传递类型和描述
                )
                logger.info(f"{report_config.get('description', report_type)} analysis job scheduled: {cron_expr}")

    except Exception as e:
        logger.error(f"Error setting up schedulers: {e}")
        raise