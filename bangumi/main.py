import json
from typing import Any

from astrbot.api import message_components as Comp
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core import astrbot_config
from astrbot.core.star.filter.command import GreedyStr

from .bangumi import Bangumi
from .message import BangumiMessage


class BangumiPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.bangumi = Bangumi(astrbot_config.get("http_proxy", ""))

    @filter.command_group("bangumi")
    async def bangumi_group(self):
        pass

    @bangumi_group.command("calendar")
    async def calendar_command(self, event: AstrMessageEvent):
        """通过番组计划获取当前番剧放送日历"""
        data = await self.bangumi.get_airing_calendar()
        return event.plain_result(BangumiMessage.calendar(data))

    @bangumi_group.command("search")
    async def search_anime_command(self, event: AstrMessageEvent, keyword: GreedyStr):
        """通过Bangumi搜索番剧"""
        data = await self.bangumi.search_anime_by_keyword(keyword)
        if not data:
            return event.plain_result("Bangumi搜索结果为空")

        data = data[0]
        return event.chain_result(
            [
                Comp.Image.fromURL(data["images"]["large"]),
                Comp.Plain(
                    BangumiMessage.search(
                        data, with_url=event.get_platform_name() != "qq_official"
                    )
                ),
            ]
        )

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

    @filter.llm_tool("bangumi_search_anime")
    async def search_anime_tool(
        self, event: AstrMessageEvent, keyword: str, count: int = 10
    ) -> str:
        """
        通过番组计划Bangumi API根据标题搜索并获取番剧的详细信息。
        若用户提到了番剧，优先使用该tool搜索详细信息。

        Args:
            keyword(string): 番剧标题关键词，一般需要番剧的正式名称
            count(number): 返回结果条数，默认为前10条
        """
        data: list[dict[str, Any]] = await self.bangumi.search_anime_by_keyword(
            keyword, count
        )

        ret: list[dict[str, Any]] = []
        for anime in data:
            ret.append(
                {
                    "name": anime["name"],
                    "name_cn": anime["name_cn"],
                    "summary": anime["summary"],
                    "date": anime["date"],
                    "platform": anime["platform"],
                    "tags": [tag["name"] for tag in anime["tags"]],
                    "meta_tags": ["meta_tags"],
                    "episodes": anime["eps"],
                    "total_episodes": anime["total_episodes"],
                    "score": anime["rating"]["score"],
                    "additional_info": {
                        item["key"]: item["value"] for item in anime["infobox"]
                    },
                }
            )

        return json.dumps(ret, ensure_ascii=False)
