import json
import re

from httpx import HTTPStatusError

from astrbot.api import message_components as Comp
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core import astrbot_config

from .niconico import Niconico


class NiconicoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.niconico = Niconico(astrbot_config.get("http_proxy", ""))

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def niconico_link(self, event: AstrMessageEvent):
        """监听n站链接"""
        match = re.search(self.niconico.LINK_PATTERN, event.message_str)
        if match is None:
            return

        try:
            data = await self.niconico.fetch_video_data(match[1])
            return event.chain_result(
                [
                    Comp.Image.fromURL(data["video"]["thumbnail"]["nHdUrl"]),
                    Comp.Plain(
                        self.niconico.generate_video_text(
                            data, event.get_platform_name() != "qq_official"
                        )
                    ),
                ]
            )
        except HTTPStatusError:
            return
        except ValueError:
            return

    @filter.llm_tool("niconico_get_video_data")
    async def niconico_get_video_data_tool(
        self, event: AstrMessageEvent, watch_id: str
    ):
        """
        获取ニコニコ動画视频所对应的视频信息

        Args:
            watch_id(string): 视频编号，格式为以sm开头的一串数字

        Returns:
            视频信息，如果获取失败则返回None
        """
        try:
            return json.dumps(
                await self.niconico.fetch_video_data(watch_id), ensure_ascii=False
            )
        except Exception as e:
            return str(e)
