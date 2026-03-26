import asyncio
from pathlib import Path
from typing import Any, cast

from quart import Request

from astrbot.api import logger
from astrbot.api.event import MessageChain
from astrbot.api.platform import Platform, PlatformMetadata
from astrbot.core.platform.register import register_platform_adapter

from .main import send_message
from .webhook_manager import WebhookPushManager


@register_platform_adapter(
    adapter_name="webhook_push",
    desc="Webhook 推送消息提醒",
    adapter_display_name="Webhook 推送",
    logo_path=str(Path(__file__).parent.resolve() / "icon.png"),
    support_streaming_message=False,
    default_config_tmpl={
        "enable": False,
        "unified_webhook_mode": True,
        "webhook_uuid": "webhook_push",
    },
    config_metadata={
        "webhook_uuid": {
            "hint": "统一 Webhook 回调地址的唯一标识符，用于构成回调地址 /api/platform/webhook/{webhook_uuid}，不可重复。",
            "type": "string",
            "invisible": False,
        },
        "unified_webhook_mode": {
            "invisible": True,
        },
        "logo_token": {
            "invisible": True,
        },
    },
)
class WebhookPushAdapter(Platform):
    """Webhook 推送适配器"""

    def __init__(
        self, platform_config: dict, platform_settings: dict, event_queue: asyncio.Queue
    ):
        super().__init__(platform_config, event_queue)

        self.manager = WebhookPushManager("webhook_push")

    def meta(self) -> PlatformMetadata:
        return PlatformMetadata(
            name="webhook_push",
            description="Webhook 推送消息提醒",
            id=cast(str, self.config.get("id")),
            support_streaming_message=False,
            support_proactive_message=False,
        )

    async def run(self) -> None:
        """启动适配器"""
        if self.unified_webhook():
            logger.info("Webhook 推送适配器运行中")
            await asyncio.Event().wait()

    async def webhook_callback(self, request: Request) -> Any:
        """统一 Webhook 回调入口"""
        token = request.args.get("token", "")
        if not token:
            return {"code": 1, "message": "Webhook push token not provided"}, 401

        umo = self.manager.get_umo(token)
        if not umo:
            return {"code": 1, "message": "Webhook push token not found"}, 401

        template_name = request.args.get("template", "default")
        template = self.manager.get_template(template_name)

        if template is None:
            await send_message(
                umo, MessageChain().message(f"Webhook推送模板 {template_name} 未找到")
            )
            return

        # IsThereAnyDeal的ping会发送类型application/json的纯文本ping内容
        # https://docs.isthereanydeal.com/#tag/Webhooks/operation/webhook-ping-post
        # 避免获取内容报错
        try:
            form_data = await request.form
        except:  # noqa
            form_data = ""
        try:
            json_data = await request.json
        except:  # noqa
            json_data = ""
        try:
            text_data = await request.get_data(as_text=True)
        except:  # noqa
            text_data = ""

        content = template.render(
            args=request.args,
            headers=dict(request.headers.items()),
            body={
                "form": form_data,
                "json": json_data,
                "text": text_data,
            },
            with_url=True,  # [TODO] 根据平台判断是否能够发送链接
        )

        await send_message(umo, MessageChain().message(content))
        logger.info("Webhook 已推送")
        return {"code": 0}, 200
