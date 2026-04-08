import json

from astrbot.api import message_components as Comp
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core import astrbot_config
from astrbot.core.star.filter.command import GreedyStr

from .anilist import AniList
from .message import AniListMessage


class AniListPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.anilist = AniList(astrbot_config.get("http_proxy", ""))

    @filter.command_group("anilist")
    async def anilist_command(self):
        pass

    @anilist_command.command("search")
    async def anilist_search_command(self, event: AstrMessageEvent, keyword: GreedyStr):
        """通过AniList搜索番剧"""
        data = await self.anilist.search_anime_by_title(keyword)
        return event.chain_result(
            [
                Comp.Image.fromURL(data["coverImage"]["large"]),
                Comp.Plain(
                    AniListMessage.anilist_search(
                        data, with_url=event.get_platform_name() != "qq_official"
                    )
                ),
            ]
        )

    @filter.llm_tool("anilist_search_anime_by_title")
    async def search_anime_by_title_tool(
        self, event: AstrMessageEvent, keyword: str
    ) -> str:
        """
        通过 AniList API 根据标题获取番剧的详细信息
        该 API 仅支持使用英语和日语搜索，不保证支持中文搜索

        Args:
            keyword(string): 番剧标题关键词
        """
        data = await self.anilist.search_anime_by_title(keyword)
        return json.dumps(data, ensure_ascii=False)

    @filter.llm_tool("anilist_get_user_anime_list")
    async def get_user_complete_anime_list_tool(
        self, event: AstrMessageEvent, user_name: str
    ) -> str:
        """
        通过 AniList API 获取给定用户名看完的所有番剧

        Args:
            user_name(string): 用户名
        """
        raw_data = await self.anilist.get_user_complete_anime_list(user_name)
        data = {
            "user": raw_data["user"],
            "anime": [
                {
                    "title": record["media"]["title"]["native"],
                    "format": record["media"]["format"],
                    "episodes": record["media"]["episodes"],
                    "duration": record["media"]["duration"],
                    "genres": record["media"]["genres"],
                    "tags": [tag["name"] for tag in record["media"]["tags"]],
                    "season": record["media"]["season"],
                    "seasonYear": record["media"]["seasonYear"],
                }
                for record in raw_data["lists"][0]["entries"]
            ],
        }
        return json.dumps(data, ensure_ascii=False)
