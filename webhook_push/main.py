from collections.abc import Callable

from astrbot.api.event import AstrMessageEvent, MessageChain, filter
from astrbot.api.star import Context, Star

from .webhook_manager import WebhookPushManager

_send_message_func: Callable | None = None


async def send_message(umo: str, message: MessageChain):
    if _send_message_func:
        await _send_message_func(umo, message)
    else:
        raise NotImplementedError("context.send_message not available for now")


class WebhookPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

        self.context = context
        self.manager = WebhookPushManager(self.name)

        global _send_message_func
        _send_message_func = self.context.send_message

    async def initialize(self):
        # 注册适配器
        from .webhook_adapter import WebhookPushAdapter as WebhookPushAdapter

    @filter.command("webhook")
    async def webhook_command(self, event: AstrMessageEvent):
        """获取 Webhook 推送 token"""
        umo = event.unified_msg_origin
        token = self.manager.get_token(umo)
        return event.plain_result(f"当前对话 UMO: {umo}\nWebhook推送token: {token}")
