import json
import re
from typing import Literal

from astrbot.api import message_components as Comp
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .bilibili import Bilibili


class BilibiliPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.bilibili = Bilibili()

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def bilibili_link(self, event: AstrMessageEvent):
        """监听b站完整链接和短链接，例如https://www.bilibili.com/video/BV14iZ3YcEZw/ 或 https://b23.tv/xxxxxxx"""
        vid = None

        # 匹配短链接
        if short_match := re.search(
            self.bilibili.short_link_pattern, event.message_str
        ):
            vid = await self.bilibili.get_bvid_from_short_link(short_match[0])
        else:
            # 匹配完整链接
            if full_match := re.search(self.bilibili.vid_pattern, event.message_str):
                vid = full_match[1]

        if vid is None:
            return

        data = await self.bilibili.fetch_video_data(vid)
        if data is None:
            return
        return event.chain_result(
            [
                Comp.Image.fromURL(data["pic"]),
                Comp.Plain(
                    self.bilibili.generate_video_text(
                        data, event.get_platform_name() != "qq_official"
                    )
                ),
            ]
        )

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def project_command(self, event: AstrMessageEvent):
        """列出B站会员购获取的上海地区活动。输入“我要看展”即可触发。"""
        if event.message_str != "我要看展":
            return

        data = await self.bilibili.get_projects()
        return event.plain_result(
            self.bilibili.generate_project_text(
                data, event.get_platform_name() != "qq_official"
            )
        )

    @filter.llm_tool("bilibili_get_video_data")
    async def bilibili_get_video_data_tool(self, event: AstrMessageEvent, vid: str):
        """
        获取Bilibili的视频av号或bv号对应的视频信息

        Args:
            vid(string): av号或bv号

        Returns:
            视频信息，如果获取失败则返回None
        """
        return json.dumps(await self.bilibili.fetch_video_data(vid), ensure_ascii=False)

    @filter.llm_tool("bilibili_get_bvid_from_short_link")
    async def bilibili_get_bvid_from_short_link_tool(
        self, event: AstrMessageEvent, url: str
    ):
        """
        若链接为的域名b23.tv，并且路径不是av或bv开头，这个链接就是Bilibili的短链接。
        这个工具能够从短链接获取bv号。

        Args:
            url(string): 短链接

        Returns:
            Bilibili视频bv号
        """
        return await self.bilibili.get_bvid_from_short_link(url)

    @filter.llm_tool("bilibili_get_all_projects")
    async def bilibili_get_all_projects_tool(
        self,
        event: AstrMessageEvent,
        area: str = "310000",
        project_type: Literal["全部类型", "演出", "展览", "本地生活"] = "全部类型",
        limit: int = 10,
    ):
        """
        从Bilibili会员购页面上，根据给定的地区，获取漫展、演出等活动

        Args:
            area(string): 地区代码（默认为上海，地区代码310000）
            project_type(string): 活动类型，有全部类型、演出、展览、本地生活，默认为全部类型
            limit(number): 返回条目数量限制；为0代表不限制数量，默认为10

        Returns:
            活动列表
        """
        return json.dumps(
            await self.bilibili.get_projects(area, project_type, limit),
            ensure_ascii=False,
        )
