import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from astrbot.api import message_components as Comp
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core import astrbot_config
from astrbot.core.message.components import BaseMessageComponent

from .pixiv import Pixiv


class PixivPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.pixiv = Pixiv(astrbot_config.get("http_proxy", ""))
        self.template_path = Path(__file__).parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader(self.template_path))

    async def get_illustration_message(
        self, illust_id: str
    ) -> list[BaseMessageComponent] | None:
        data = await self.pixiv.get_illustration_info(illust_id)
        if data is None:
            return None

        template = self.jinja_env.get_template("illustration.jinja")

        message = []
        if image := await self.pixiv.download(data["urls"]["regular"]):
            message.append(Comp.Image.fromBytes(image))
        message.append(Comp.Plain(template.render(data=data)))

        return message

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def illustration_link_listener(self, event: AstrMessageEvent):
        """自动监听 Pixiv 插画链接"""
        match = re.search(self.pixiv.ILLUSTRATION_PATTERN, event.message_str)
        if match is None:
            return

        if message := await self.get_illustration_message(match[1]):
            return event.chain_result(message)

    @filter.llm_tool("pixiv_get_illustration")
    async def illustration_tool(self, event: AstrMessageEvent, illust_id: str):
        """
        获取Pixiv插画信息，获取到的信息和插画会直接发送给用户。
        例如这样的链接就需要使用这个tool来获取内容：https://www.pixiv.net/artworks/{illust_id}
        或用户直接给出Pixiv的插画ID则也需要调用这个tool。

        Args:
            illust_id(string): Pixiv插画ID
        """
        if message := await self.get_illustration_message(illust_id):
            return event.chain_result(message)
        return "无法获取插画信息"
