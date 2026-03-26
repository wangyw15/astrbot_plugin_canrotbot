import json
from typing import Any

from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core import astrbot_config
from astrbot.core.star.filter.command import GreedyStr

from .anilist import AniList
from .bangumi import Bangumi
from .message import AnimeMessage


class AnimePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.anilist = AniList(astrbot_config.get("http_proxy", ""))
        self.bangumi = Bangumi(astrbot_config.get("http_proxy", ""))

    @filter.command_group("anime")
    async def anime_command(self):
        pass

    @anime_command.command("search")
    async def anilist_search_command(self, event: AstrMessageEvent, keyword: GreedyStr):
        """通过AniList搜索番剧"""
        data = await self.anilist.search_anime_by_title(keyword)
        return event.plain_result(AnimeMessage.anilist_search(data))

    @anime_command.command("calendar")
    async def bangumi_calendar_command(self, event: AstrMessageEvent):
        """通过番组计划获取当前番剧放送日历"""
        data = await self.bangumi.get_airing_calendar()
        return event.plain_result(AnimeMessage.bangumi_calendar(data))

    @filter.llm_tool("bangumi_airing_calendar")
    async def get_airing_calendar_simple(self, event: AstrMessageEvent) -> str:
        """
        从番组计划（Bangumi）获取当前的每日放送日历
        """
        data: list[dict[str, Any]] = await self.bangumi.get_airing_calendar()

        ret: dict[str, Any] = {}
        for i in data:
            ret[i["weekday"]["cn"]] = {
                "items": [
                    {
                        "name": j["name"],
                        "name_cn": j["name_cn"],
                        "summary": j["summary"],
                        "url": j["url"],
                    }
                    for j in i["items"]
                ]
            }

        return json.dumps(ret, ensure_ascii=False)

    @filter.llm_tool("anilist_search_anime_by_title")
    async def search_anime_by_title(self, event: AstrMessageEvent, keyword: str) -> str:
        """
        通过 AniList API 根据标题获取番剧的详细信息
        该 API 仅支持使用英语和日语搜索，不保证支持中文搜索

        Args:
            keyword(string): 番剧标题关键词
        """
        data = await self.anilist.search_anime_by_title(keyword)
        return json.dumps(data, ensure_ascii=False)
