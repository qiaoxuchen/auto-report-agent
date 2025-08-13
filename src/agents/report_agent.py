# src/agents/report_agent.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
# from email.mime.base import MIMEBase # 用于附件
# from email import encoders # 用于附件编码
from jinja2 import Environment, FileSystemLoader
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ReportGeneratorAgent:
    def __init__(self, config, data_aggregator):
        self.config = config
        self.template_path = config.get('template_path')
        self.output_dir = config.get('output_dir', './reports')
        os.makedirs(self.output_dir, exist_ok=True)
        self.email_config = config.get('email', {})
        self.data_aggregator = data_aggregator

        self.template_env = Environment(loader=FileSystemLoader(os.path.dirname(self.template_path)))
        self.template = self.template_env.get_template(os.path.basename(self.template_path))
        logger.info(f"ReportGeneratorAgent initialized. Template: {self.template_path}, Output: {self.output_dir}")

    def _aggregate_data_for_report(self, report_type):
        """为报告聚合所需数据"""
        # 简化：获取最近一段时间的数据
        now = datetime.now()
        if report_type == 'daily':
            since = now - timedelta(days=1)
        elif report_type == 'weekly':
            since = now - timedelta(weeks=1)
        else:
            since = now - timedelta(days=30) # 默认月度

        aggregated_data = {}
        all_data = self.data_aggregator.get_all_data()

        for source, data_points in all_data.items():
            # 过滤时间
            filtered_points = [dp['data'] for dp in data_points if datetime.fromisoformat(dp['timestamp']) >= since]
            aggregated_data[source] = filtered_points

        return aggregated_data


    def generate_daily_report(self):
        """生成日报"""
        aggregated_data = self._aggregate_data_for_report('daily')
        report_data = {
            "date": datetime.now().strftime("%Y-%m-%d"),
            "type": "日报",
            "content": aggregated_data,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return self._render_report(report_data)

    def generate_weekly_report(self):
        """生成周报"""
        aggregated_data = self._aggregate_data_for_report('weekly')
        report_data = {
            "date": f"第 {datetime.now().strftime('%U')} 周 ({(datetime.now() - timedelta(days=datetime.now().weekday())).strftime('%Y-%m-%d')} 至 {datetime.now().strftime('%Y-%m-%d')})",
            "type": "周报",
            "content": aggregated_data,
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return self._render_report(report_data)

    def _render_report(self, report_data):
        """使用模板渲染报告"""
        try:
            rendered_report = self.template.render(report_data)
            logger.debug(f"Report rendered (first 200 chars): {rendered_report[:200]}...")
            return rendered_report
        except Exception as e:
            logger.error(f"Error rendering report: {e}")
            return f"报告生成失败: {e}"

    def save_report(self, report_content, filename_prefix="report"):
        """保存报告到文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"{filename_prefix}_{timestamp}.txt")
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report_content)
            logger.info(f"Report saved to: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving report: {e}")
            return None

    def send_email(self, subject, body, attachments=None):
        """发送邮件 [[30]]"""
        if not self.email_config.get('enabled', False):
            logger.info("Email sending is disabled in config.")
            return True # 视为成功，因为未启用

        smtp_server = self.email_config.get('smtp_server')
        smtp_port = self.email_config.get('smtp_port')
        sender_email = self.email_config.get('sender_email')
        sender_password = self.email_config.get('sender_password')
        recipient_email = self.email_config.get('recipient_email')

        if not all([smtp_server, smtp_port, sender_email, sender_password, recipient_email]):
            logger.error("Email configuration incomplete.")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'plain', 'utf-8')) # 可以改为 'html'

            # if attachments:
            #     for file_path in attachments:
            #         with open(file_path, "rb") as attachment:
            #             part = MIMEBase('application', 'octet-stream')
            #             part.set_payload(attachment.read())
            #         encoders.encode_base64(part)
            #         part.add_header(
            #             'Content-Disposition',
            #             f'attachment; filename= {os.path.basename(file_path)}',
            #         )
            #         msg.attach(part)

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls() # 启用TLS加密 [[35]]
            server.login(sender_email, sender_password)
            text = msg.as_string()
            server.sendmail(sender_email, recipient_email, text)
            server.quit()
            logger.info(f"Email sent to {recipient_email}")
            return True
        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def generate_and_send_daily(self):
        """生成并发送日报"""
        logger.info("Generating and sending daily report...")
        report_content = self.generate_daily_report()
        if report_content:
             filename = self.save_report(report_content, "daily_report")
             if filename:
                 subject = f"【自动报告】日报 - {datetime.now().strftime('%Y-%m-%d')}"
                 # 附件发送示例 (可选)
                 # success = self.send_email(subject, report_content, attachments=[filename])
                 success = self.send_email(subject, report_content)
                 if success:
                     logger.info("Daily report generated and sent successfully.")
                 else:
                     logger.error("Failed to send daily report email.")
             else:
                 logger.error("Failed to save daily report.")

    def generate_and_send_weekly(self):
        """生成并发送周报"""
        logger.info("Generating and sending weekly report...")
        report_content = self.generate_weekly_report()
        if report_content:
             filename = self.save_report(report_content, "weekly_report")
             if filename:
                 subject = f"【自动报告】周报 - 第{datetime.now().strftime('%U')}周"
                 # success = self.send_email(subject, report_content, attachments=[filename])
                 success = self.send_email(subject, report_content)
                 if success:
                     logger.info("Weekly report generated and sent successfully.")
                 else:
                     logger.error("Failed to send weekly report email.")
             else:
                 logger.error("Failed to save weekly report.")