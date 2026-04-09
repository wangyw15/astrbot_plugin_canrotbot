from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core import astrbot_config

from .waifu import Waifu


class WaifuPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.waifu = Waifu(astrbot_config.get("http_proxy", ""))

    @filter.command("waifu")
    async def waifu_command(self, event: AstrMessageEvent, category: str = "waifu"):
        """获取一张 waifu 图片"""
        if category not in self.waifu.AVAILABLE_CATEGORY:
            return event.plain_result(f"无效的分类 {category}")

        return event.image_result(await self.waifu.get_waifu_url(category))

    @filter.llm_tool("waifu_get_available_categories")
    async def get_available_categories_tool(self, event: AstrMessageEvent) -> str:
        """
        获取所有可用的waifu图片分类
        """
        return ", ".join(self.waifu.AVAILABLE_CATEGORY)

    @filter.llm_tool("waifu_send_image")
    async def send_waifu_image_tool(
        self, event: AstrMessageEvent, category: str = "waifu"
    ):
        """
        向用户发送一张随机的 waifu 图片。
        该工具会自动将图片发送给用户，因此不需要在响应中再次发送。

        Args:
            category(string): 图片分类，默认为 waifu。可以通过waifu_get_available_categories这个工具来确认可接受的category参数。
        """
        if category not in self.waifu.AVAILABLE_CATEGORY:
            return f"无效的分类 {category}"

        return await self.waifu_command(event, category)
