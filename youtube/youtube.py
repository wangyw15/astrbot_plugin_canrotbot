from datetime import datetime, timezone
from pathlib import Path

from httpx import AsyncClient
from jinja2 import Template


class YouTube:
    LINK_PATTERN = r"(?:https?:\/\/)?(?:youtu\.be\/|(?:\w{3}\.)?youtube\.com\/(?:watch\?.*v=|shorts\/))([a-zA-Z0-9-_]+)"

    def __init__(self, api_key: str, proxy: str = "") -> None:
        self.client = AsyncClient(proxy=proxy or None)
        self.asset_path = Path(__file__).parent / "assets"
        self.api_key = api_key

    async def get_video_data(self, ytb_id: str) -> dict | None:
        """
        Get YouTube video information by video id

        Args:
            ytb_id: YouTube video id

        Returns:
            Video information in JSON format, empty if failed
        """
        resp = await self.client.get(
            f"https://youtube.googleapis.com/youtube/v3/videos?part=snippet%2Cstatistics&id={ytb_id}&key={self.api_key}"
        )
        if resp.is_success:
            data = resp.json()
            if data["pageInfo"]["totalResults"] > 0:
                return data["items"][0]
        return None

    def get_video_thumbnail_url(self, data: dict) -> str:
        """
        下载 YouTube 封面图

        :param data: YouTube 接口返回的数据

        :return: 封面图数据
        """
        url = ""
        max_width = 0
        for _, v in data["snippet"]["thumbnails"].items():
            if v["width"] > max_width:
                max_width = v["width"]
                url = v["url"]
        return url

    def generate_video_text(self, data: dict, with_url: bool = True) -> str:
        def convert_time(time: str) -> str:
            date = datetime.strptime(time, "%Y-%m-%dT%H:%M:%SZ").replace(
                tzinfo=timezone.utc
            )
            date = date.astimezone(datetime.now().astimezone().tzinfo)
            return date.strftime("%Y年%m月%d日 %H:%M:%S")

        def clean_description(desc: str) -> str:
            desc = "\n".join([x.strip() for x in desc.split("\n") if x.strip() != ""])
            if len(desc) > 200:
                desc = desc[:200] + "..."
            return desc

        template: Template = Template(
            (self.asset_path / "video.jinja").read_text("utf-8")
        )
        return template.render(
            data=data,
            with_url=with_url,
            convert_time=convert_time,
            clean_description=clean_description,
        )
