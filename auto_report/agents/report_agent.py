# src/agents/report_agent.py
import os
import smtplib
import requests
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ReportGeneratorAgent:
    def __init__(self, config, data_aggregator):
        self.config = config
        self.output_dir = config.get('output_dir', './reports')
        os.makedirs(self.output_dir, exist_ok=True)
        self.email_config = config.get('email', {})
        self.llm_config = config.get('llm', {})
        self.data_aggregator = data_aggregator

        # 检查大模型配置
        if not self.llm_config.get('enabled', False) or not self.llm_config.get('api_key'):
             logger.warning("LLM is not properly configured. Reports will be basic.")
             self.use_llm = False
        else:
             self.use_llm = True
             self.llm_api_key = self.llm_config['api_key']
             self.llm_model = self.llm_config.get('model', 'glm-4-plus')
             self.llm_base_url = self.llm_config.get('base_url', 'https://open.bigmodel.cn/api/paas/v4/chat/completions')
             self.llm_timeout = self.llm_config.get('timeout', 120)
             logger.info(f"LLM enabled: {self.llm_model}")

        logger.info(f"ReportGeneratorAgent initialized. Output: {self.output_dir}")

    def _aggregate_data_for_report(self, report_type):
        """为报告聚合所需数据，现在包含文档数据"""
        now = datetime.now()
        if report_type == 'daily':
            since = now - timedelta(days=1)
        elif report_type == 'weekly':
            since = now - timedelta(weeks=1)
        elif report_type == 'monthly':
            since = now - timedelta(days=30)  # 简化处理
        else:
            since = now - timedelta(days=1)  # 默认日报

        aggregated_data = {}
        all_data = self.data_aggregator.get_all_data()

        for source, data_points in all_data.items():
            # 过滤时间
            filtered_points = [dp['data'] for dp in data_points if datetime.fromisoformat(dp['timestamp']) >= since]

            # 对于文档数据，我们可能只想摘要关键信息，而不是全部内容片段
            if source == 'document' and filtered_points:
                # 可以在这里对文档数据进行初步处理，例如只保留文件名和最后修改时间
                # 或者保留内容片段用于大模型分析
                processed_docs = []
                for doc in filtered_points:
                    # 示例：只传递文件名和摘要
                    processed_docs.append({
                        "filename": doc.get('filename'),
                        "last_modified": doc.get('last_modified'),
                        "content_snippet": doc.get('content_snippet', '')[:200] + "..."  # 进一步缩短
                    })
                aggregated_data[source] = processed_docs
            else:
                aggregated_data[source] = filtered_points

        return aggregated_data

    def _generate_report_with_llm(self, report_type, aggregated_data):
        """调用大模型API生成报告"""
        if not self.use_llm:
            return "LLM not configured. Cannot generate report."

        prompt = f"请根据以下数据，为用户生成一份{report_type}。数据按来源分类：\n"
        for source, data_points in aggregated_data.items():
            if data_points:
                prompt += f"\n【{source}】\n"
                for item in data_points:
                    prompt += f"- {str(item)}\n"

        prompt += f"\n请总结以上信息，生成一份结构清晰、语言自然的{report_type}。内容应包括主要工作内容、遇到的问题（如果有）、下一步计划（可选）。报告应简洁明了，突出重点。"

        headers = {
            'Authorization': f'Bearer {self.llm_api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            "model": self.llm_model,
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            logger.debug(f"Calling LLM API with prompt (first 500 chars): {prompt[:500]}...")
            response = requests.post(self.llm_base_url, headers=headers, data=json.dumps(data), timeout=self.llm_timeout)
            response.raise_for_status()
            result = response.json()
            report_content = result['choices'][0]['message']['content']
            logger.info(f"LLM generated {report_type} successfully.")
            return report_content
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling LLM API: {e}")
            return f"调用大模型生成{report_type}时出错: {e}"
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing LLM API response: {e}")
            return f"解析大模型响应时出错: {e}"


    def generate_daily_report(self):
        """生成日报"""
        aggregated_data = self._aggregate_data_for_report('daily')
        if self.use_llm:
            return self._generate_report_with_llm("日报", aggregated_data)
        else:
            # Fallback to simple text if LLM is disabled
            return f"日报 (Fallback)\n\n数据: {aggregated_data}"

    def generate_weekly_report(self):
        """生成周报"""
        aggregated_data = self._aggregate_data_for_report('weekly')
        if self.use_llm:
            return self._generate_report_with_llm("周报", aggregated_data)
        else:
            return f"周报 (Fallback)\n\n数据: {aggregated_data}"

    def generate_monthly_report(self):
         """生成月报"""
         aggregated_data = self._aggregate_data_for_report('monthly')
         if self.use_llm:
             return self._generate_report_with_llm("月报", aggregated_data)
         else:
             return f"月报 (Fallback)\n\n数据: {aggregated_data}"

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
        """发送邮件"""
        if not self.email_config.get('enabled', False):
            logger.info("Email sending is disabled in config.")
            return True

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

            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()
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
                 success = self.send_email(subject, report_content)
                 if success:
                     logger.info("Weekly report generated and sent successfully.")
                 else:
                     logger.error("Failed to send weekly report email.")
             else:
                 logger.error("Failed to save weekly report.")

    def generate_and_send_monthly(self):
         """生成并发送月报"""
         logger.info("Generating and sending monthly report...")
         report_content = self.generate_monthly_report()
         if report_content:
              filename = self.save_report(report_content, "monthly_report")
              if filename:
                  subject = f"【自动报告】月报 - {datetime.now().strftime('%Y年%m月')}"
                  success = self.send_email(subject, report_content)
                  if success:
                      logger.info("Monthly report generated and sent successfully.")
                  else:
                      logger.error("Failed to send monthly report email.")
              else:
                  logger.error("Failed to save monthly report.")