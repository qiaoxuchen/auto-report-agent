# src/agents/analyzer_agent.py
import os
import smtplib
import requests
import json
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class AnalyzerAgent:
    """
    统一数据分析与报告生成代理。
    收集所有数据，调用大模型API进行分析，并生成/发送报告。
    """

    def __init__(self, config, data_aggregator):
        self.config = config
        self.data_aggregator = data_aggregator

        # 配置
        self.output_dir = config.get('core', {}).get('report_output_dir', './reports')
        os.makedirs(self.output_dir, exist_ok=True)

        self.email_config = config.get('notifications', {}).get('email', {})
        self.llm_config = config.get('llm', {})

        # 检查大模型配置
        if not self.llm_config.get('enabled', False) or not self.llm_config.get('api_key'):
            logger.error("LLM is not properly configured or disabled. AnalyzerAgent cannot function.")
            raise ValueError("LLM configuration is missing or disabled.")

        self.use_llm = True
        self.llm_api_key = self.llm_config['api_key']
        self.llm_model = self.llm_config.get('model', 'glm-4-plus')
        self.llm_base_url = self.llm_config.get('base_url', 'https://open.bigmodel.cn/api/paas/v4/chat/completions')
        self.llm_timeout = self.llm_config.get('timeout', 120)
        logger.info(f"AnalyzerAgent initialized with LLM: {self.llm_model}")

    def _get_time_range(self, report_type):
        """根据报告类型确定数据时间范围"""
        now = datetime.now()
        if report_type == 'daily':
            since = now - timedelta(days=1)
        elif report_type == 'weekly':
            since = now - timedelta(weeks=1)
        elif report_type == 'monthly':
            since = now - timedelta(days=30)  # 简化处理
        elif report_type == 'quarterly':
            since = now - timedelta(days=90)  # 简化处理
        elif report_type == 'yearly':
            since = now - timedelta(days=365)  # 简化处理
        else:
            logger.warning(f"Unknown report type '{report_type}', defaulting to daily range.")
            since = now - timedelta(days=1)
        return since

    def _build_llm_prompt(self, report_type, description, filtered_data):
        """构建发送给大模型的提示词 (Prompt)"""
        time_range_str = self._get_time_range(report_type).strftime('%Y-%m-%d %H:%M:%S')
        now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        prompt = f"""
你是一个专业的工作总结助手。请根据用户在 {time_range_str} 到 {now_str} 期间的活动数据，为用户生成一份**{description}**。

数据按来源分类如下：
"""
        if not filtered_data:
            prompt += "\n- 无可用数据。\n"
        else:
            for source, data_points in filtered_data.items():
                if data_points:
                    prompt += f"\n--- 来源: {source} ---\n"
                    # 对于每个来源，我们只传递关键信息，避免token过长
                    for item in data_points:
                        data_content = item.get('data', {})
                        timestamp = item.get('timestamp', 'N/A')

                        if source == 'screen':
                            prompt += f"  [屏幕截图分析 - {timestamp}]\n"
                            prompt += f"    文件: {data_content.get('filename', 'N/A')}\n"
                            prompt += f"    内容摘要: {data_content.get('extracted_text_snippet', 'N/A')}\n"
                        elif source == 'file':
                            prompt += f"  [文件变更 - {timestamp}]\n"
                            prompt += f"    事件: {data_content.get('event_type', 'N/A')}\n"
                            prompt += f"    路径: {data_content.get('src_path', 'N/A')}\n"
                        elif source == 'document':
                            prompt += f"  [文档内容 - {timestamp}]\n"
                            prompt += f"    文件: {data_content.get('filename', 'N/A')}\n"
                            prompt += f"    最后修改: {data_content.get('last_modified', 'N/A')}\n"
                            prompt += f"    内容摘要: {data_content.get('content_snippet', 'N/A')}\n"
                        elif source == 'lark_calendar':
                            prompt += f"  [飞书日程 - {timestamp}]\n"
                            prompt += f"    主题: {data_content.get('summary', 'N/A')}\n"
                            prompt += f"    描述: {data_content.get('description', 'N/A')}\n"
                            prompt += f"    时间: {data_content.get('start_time', 'N/A')} to {data_content.get('end_time', 'N/A')}\n"
                        elif source == 'lark_message':
                            prompt += f"  [飞书消息 - {timestamp}]\n"
                            prompt += f"    群组: {data_content.get('chat_name', 'N/A')}\n"
                            prompt += f"    内容: {data_content.get('content', 'N/A')}\n"
                        else:
                            # 通用处理
                            prompt += f"  [数据点 - {timestamp}]\n"
                            prompt += f"    内容: {str(data_content)[:200]}...\n"  # 限制长度
                        prompt += "\n"  # 每个数据点后空一行

        prompt += f"""

请根据以上信息，生成一份结构清晰、语言自然流畅的{description}。报告应包含以下部分：

1.  **核心工作内容**: 总结在此期间的主要工作和活动。
2.  **关键成果/进展**: 提及完成的重要任务或取得的成果。
3.  **遇到的问题与思考** (可选): 如果数据中有体现，可以简述。
4.  **下一步计划** (可选): 基于当前工作，提出简要的后续计划。

**要求**:
*   内容准确，基于提供的数据进行总结。
*   语言专业、简洁、有条理。
*   不要遗漏重要信息，也不要编造未提及的内容。
*   最终输出应为纯文本格式的{description}，无需Markdown或其他格式。
"""
        return prompt

    def _call_llm_api(self, prompt):
        """调用大模型API"""
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
            response = requests.post(self.llm_base_url, headers=headers, data=json.dumps(data),
                                     timeout=self.llm_timeout)
            response.raise_for_status()
            result = response.json()
            report_content = result['choices'][0]['message']['content']
            logger.info("LLM analysis completed successfully.")
            return report_content
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling LLM API: {e}")
            return f"调用大模型分析时出错: {e}"
        except (KeyError, IndexError) as e:
            logger.error(f"Error parsing LLM API response: {e}")
            return f"解析大模型响应时出错: {e}"

    def analyze_and_report(self, report_type, description):
        """
        核心方法：分析数据并生成报告。
        :param report_type: 'daily', 'weekly', 'monthly' 等
        :param description: 报告的中文描述，如 '日报', '周报'
        """
        logger.info(f"Starting analysis for {description}...")

        # 1. 确定时间范围
        since = self._get_time_range(report_type)

        # 2. 从 DataAggregator 获取该时间范围内的所有原始数据
        filtered_data = self.data_aggregator.get_raw_data_since(since)
        logger.debug(f"Data collected for analysis: {list(filtered_data.keys())}")

        # 3. 构建提示词
        prompt = self._build_llm_prompt(report_type, description, filtered_data)

        # 4. 调用大模型API进行分析
        report_content = self._call_llm_api(prompt)

        # 5. 保存报告
        filename = self.save_report(report_content, f"{report_type}_report")

        # 6. 发送报告 (如果配置了)
        if filename:
            subject = f"【自动报告】{description} - {datetime.now().strftime('%Y-%m-%d')}"
            # 可以选择发送内容或附件
            success = self.send_email(subject, report_content)
            if success:
                logger.info(f"{description} generated and sent successfully.")
            else:
                logger.error(f"Failed to send {description} email.")
        else:
            logger.error(f"Failed to save {description}.")

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
