from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .api import API60s


class API60sPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.api = API60s()

    @filter.llm_tool("daily_news")
    async def daily_news_tool(self, event: AstrMessageEvent) -> str:
        """
        返回当天的新闻内容，内容会每日更新。调用完之后不要再调用网页搜索。
        """
        if data := await self.api.news(encoding="markdown"):
            return data  # type: ignore
        return "获取失败"

    @filter.llm_tool("today_in_historys")
    async def today_in_history_tool(self, event: AstrMessageEvent) -> str:
        """
        历史上的今天，内容会每日更新。
        """
        if data := await self.api.today_in_history(encoding="markdown"):
            return data
        return "获取失败"

    @filter.llm_tool("fuel_price")
    async def fuel_price_tool(
        self, event: AstrMessageEvent, region: str = "上海"
    ) -> str:
        """
        今天的汽柴油价格，内容会每日更新。

        Args:
            region(string): 地区，默认为上海
        """
        if data := await self.api.fuel_price(region=region, encoding="markdown"):
            return data
        return "获取失败"

    @filter.llm_tool("gold_price")
    async def gold_price_tool(self, event: AstrMessageEvent) -> str:
        """
        今天的黄金价格，内容会每日更新。
        """
        if data := await self.api.gold_price(encoding="markdown"):
            return data
        return "获取失败"

    @filter.command("daily")
    async def daily_news_command(self, event: AstrMessageEvent):
        """【日更】每天 60 秒读懂世界"""
        data: str | None = await self.api.news(encoding="text")  # type: ignore
        if data is None:
            return event.plain_result("获取失败")
        return event.plain_result(data)
