import json
from typing import Any

from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core import astrbot_config

from .bangumi import Bangumi
from .message import BangumiMessage


class BangumiPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.bangumi = Bangumi(astrbot_config.get("http_proxy", ""))

    @filter.command_group("bangumi")
    async def bangumi_command(self):
        pass

    @bangumi_command.command("calendar")
    async def bangumi_calendar_command(self, event: AstrMessageEvent):
        """通过番组计划获取当前番剧放送日历"""
        data = await self.bangumi.get_airing_calendar()
        return event.plain_result(BangumiMessage.bangumi_calendar(data))

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
