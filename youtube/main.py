import json
import re

from astrbot.api import AstrBotConfig
from astrbot.api import message_components as Comp
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core import astrbot_config

from .youtube import YouTube


class YouTubePlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)

        self.youtube = YouTube(config["api_key"], astrbot_config.get("http_proxy", ""))

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def youtube_link(self, event: AstrMessageEvent):
        """监听YouTube视频链接"""
        match = re.search(self.youtube.LINK_PATTERN, event.message_str)
        if match is None:
            return

        data = await self.youtube.get_video_data(match[1])
        if data is None:
            return
        return event.chain_result(
            [
                Comp.Image.fromURL(self.youtube.get_video_thumbnail_url(data)),
                Comp.Plain(
                    self.youtube.generate_video_text(
                        data, event.get_platform_name() != "qq_official"
                    )
                ),
            ]
        )

    @filter.llm_tool("youtube_get_video_id")
    async def youtube_get_video_id_tool(
        self, event: AstrMessageEvent, url: str
    ) -> str | None:
        """
        获取YouTube链接对应的视频id

        Args:
            url(string): YouTube链接

        Returns:
            视频id，如果获取失败则返回None
        """
        match = re.match(self.youtube.LINK_PATTERN, url)
        if match is not None:
            return match[1]
        return None

    @filter.llm_tool("youtube_get_video_data")
    async def youtube_get_video_data_tool(
        self, event: AstrMessageEvent, vid: str
    ) -> str | None:
        """
        获取YouTube视频id对应的视频信息

        Args:
            vid(string): YouTube视频id

        Returns:
            视频信息，如果获取失败则返回None
        """
        return json.dumps(await self.youtube.get_video_data(vid), ensure_ascii=False)
