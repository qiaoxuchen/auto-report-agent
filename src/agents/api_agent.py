# src/agents/api_agent.py
import lark_oapi as lark
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class LarkDataAgent:
    def __init__(self, config, data_aggregator):
        self.config = config
        self.app_id = config.get('app_id')
        self.app_secret = config.get('app_secret')
        self.data_aggregator = data_aggregator
        self.client = None
        if self.app_id and self.app_secret:
            self.client = lark.Client.builder() \
                .app_id(self.app_id) \
                .app_secret(self.app_secret) \
                .log_level(lark.LogLevel.INFO) \
                .build()
            logger.info("LarkDataAgent initialized.")
        else:
            logger.warning("Lark app_id or app_secret not provided. Lark integration disabled.")

    # 注意：获取用户个人数据（如聊天记录）需要用户授权Token，通常通过OAuth流程获得。
    # 此处示例仅展示如何调用应用级API或获取应用可访问的数据（如机器人所在群聊的消息）。
    # 获取用户Token需要前端配合和后端处理回调。

    def fetch_app_access_token(self):
        """获取应用访问凭证 (App Access Token)"""
        if not self.client:
            logger.warning("Lark client not initialized.")
            return None
        try:
            req = lark.AppAccessTokenReq.builder() \
                .app_id(self.app_id) \
                .app_secret(self.app_secret) \
                .build()
            resp = self.client.ext.authentication.v1.app_access_token.create(req)
            if resp.code == 0:
                logger.debug("App access token fetched successfully.")
                return resp.data.app_access_token
            else:
                logger.error(f"Failed to fetch app access token: {resp.msg}")
                return None
        except Exception as e:
            logger.error(f"Error fetching app access token: {e}")
            return None

    def fetch_tenant_access_token(self):
         """获取租户访问凭证 (Tenant Access Token)"""
         # 类似地获取 Tenant Access Token
         pass

    def fetch_calendar_events_mock(self):
        """模拟获取日程事件 (实际需调用API)"""
        logger.info("Fetching calendar events from Lark (mock implementation).")
        # 示例数据
        events = [
            {"summary": "项目评审会议", "description": "讨论项目进度", "start_time": "2023-10-27T10:00:00+08:00", "end_time": "2023-10-27T11:00:00+08:00"},
            {"summary": "团队周会", "description": "", "start_time": "2023-10-28T09:30:00+08:00", "end_time": "2023-10-28T10:30:00+08:00"}
        ]
        for event in events:
            self.data_aggregator.add_data('lark_calendar', event)

    def fetch_recent_messages_mock(self):
         """模拟获取最近消息 (实际需调用API)"""
         logger.info("Fetching recent messages from Lark (mock implementation).")
         # 示例数据
         messages = [
             {"chat_name": "项目A讨论组", "content": "请大家查收最新需求文档。", "create_time": "2023-10-27T15:20:00+08:00"},
             {"chat_name": "技术分享", "content": "分享一个关于Python性能优化的链接。", "create_time": "2023-10-27T16:45:00+08:00"}
         ]
         for msg in messages:
             self.data_aggregator.add_data('lark_message', msg)

    def fetch_data(self):
        """获取Lark相关数据的主方法"""
        # token = self.fetch_app_access_token() # 获取Token
        # if not token:
        #     logger.error("Cannot fetch Lark data without access token.")
        #     return

        # 调用具体的API方法
        self.fetch_calendar_events_mock() # 示例
        self.fetch_recent_messages_mock() # 示例
        logger.info("Lark data fetch cycle completed (mock).")

    # 如果需要定时获取Lark数据，可以在scheduler.py中添加一个定时任务调用 self.fetch_data