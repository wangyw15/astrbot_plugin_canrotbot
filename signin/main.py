import json
from datetime import datetime
from typing import Any

from mcp.types import CallToolResult

from astrbot.api import message_components as Comp
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core.agent.tool import FunctionTool

from .fortune import Fortune
from .history import HistoryManager
from .themes import manager


class SigninPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.fortune = Fortune()
        self.history = HistoryManager(self.name)

    async def initialize(self) -> None:
        self.fortune.load()

    @filter.command("signin")
    async def signin_command(self, event: AstrMessageEvent, theme: str = "random"):
        """每日签到"""
        uid = event.get_sender_id()
        if self.history.already_signin(uid):
            image_path = self.history.get_latest_image_path(uid)
            if image_path is not None and image_path.exists():
                return event.image_result(str(image_path))
            else:
                if today_record := self.history.get_today_record(uid):
                    title = today_record["title"]
                    content = today_record["content"]
                    theme = today_record["theme"]
        else:
            title, content = self.fortune()

        theme_instance = manager.get_theme(theme)
        if theme_instance is None:
            return event.plain_result(f"签到主题 {theme} 不存在")

        html = await theme_instance.generate(title, content)
        image = await self.html_render(
            html,
            {},
            options={
                "type": "png",
                "clip": {
                    "x": 0,
                    "y": 0,
                    "width": 480,
                    "height": 480,
                },
            },
        )
        self.history.add_record(uid, title, content, theme_instance.name)
        await self.history.set_latest_image_url(uid, image)
        return event.image_result(image)

    @filter.llm_tool("signin_get_today_record")
    async def get_today_record_tool(self, event: AstrMessageEvent):
        """获取用户当前的签到运势内容。若当天没有签到过，则返回未签到"""
        if today_record := self.history.get_today_record(event.get_sender_id()):
            return today_record["title"] + "\n" + today_record["content"]
        return "用户今天还未签到过"

    @filter.llm_tool("signin")
    async def signin_tool(self, event: AstrMessageEvent):
        """
        每日签到

        每天第一次签到会提供新的运势，当天多次签到只会返回第一次签到的结果
        """
        uid = event.get_sender_id()
        today_signed = self.history.get_today_record(uid) is not None

        await self.signin_command(event)

        if today_record := self.history.get_today_record(uid):
            llm_response: dict[str, Any] = dict(today_record.items())
            llm_response.pop("theme")
            llm_response["repeat_signin"] = today_signed
            yield json.dumps(llm_response, ensure_ascii=False)

    @filter.on_llm_tool_respond()
    async def set_signin_tool_call_status(
        self,
        event: AstrMessageEvent,
        tool: FunctionTool,
        tool_args: dict | None,
        tool_result: CallToolResult | None,
    ) -> None:
        if tool.name == "signin":
            event.set_extra("called_signin_tool", True)

    @filter.on_decorating_result()
    async def signin_response_add_image(self, event: AstrMessageEvent):
        if not event.get_extra("called_signin_tool", False):
            return

        if result := event.get_result():
            uid = event.get_sender_id()
            image_path = self.history.get_latest_image_path(uid)
            if image_path is not None and image_path.exists():
                result.chain.insert(0, Comp.Image.fromFileSystem(str(image_path)))

    @filter.llm_tool("signin_get_history_records")
    async def signin_history_tool(
        self, event: AstrMessageEvent, date_from_str: str = "", date_to_str: str = ""
    ):
        """
        获取用户的历史签到记录。
        返回JSON格式的签到历史记录列表，包含签到日期、运势标题和运势内容等信息。
        若日期范围无效或没有记录，返回空列表。
        此外，theme字段为签到结果图片使用的主题，与运势本身无关。若用户没有提到主题相关的内容，则不要对此进行分析或输出。

        Args:
            date_from_str(string): 起始日期，格式为 YYYYMMDD（例如20260328），默认为空表示不限制起始日期。
            date_to_str(string): 结束日期，格式为 YYYYMMDD（例如20260328），默认为空表示不限制结束日期。
        """
        if date_from_str == "":
            date_from = datetime.fromtimestamp(0)
        else:
            date_from = self.history.parse_date(date_from_str)
        if date_from is None:
            return "date_from_str格式有误，示例：20260328"

        if date_to_str == "":
            date_to = datetime.now()
        else:
            date_to = self.history.parse_date(date_to_str)
        if date_to is None:
            return "date_to_str格式有误，示例：20260328"

        records = self.history.get_history_record(
            event.get_sender_id(), date_from.date(), date_to.date()
        )
        return json.dumps(records, ensure_ascii=False)
