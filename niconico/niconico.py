from datetime import datetime
from pathlib import Path
from typing import Any

from httpx import AsyncClient
from jinja2 import Template


class Niconico:
    LINK_PATTERN = (
        r"(?:https?:\/\/)?(?:(?:www\.nicovideo\.jp\/watch)|(?:nico\.ms))\/(sm\d+)"
    )
    BASE_URL = "https://nvapi.nicovideo.jp"

    def __init__(self, proxy: str = "") -> None:
        self.client = AsyncClient(proxy=proxy or None)
        self.client.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5666.197 Safari/537.36",
            "x-Frontend-Id": "6",
            "x-Frontend-version": "6",
        }
        self.template_path = Path(__file__).parent / "templates"

    async def fetch_video_data(self, watch_id: str) -> dict[str, Any]:
        if not watch_id.lower().startswith("sm"):
            raise ValueError(f"无效的watch_id: {watch_id}")

        url = self.BASE_URL + "/v1/videos?watchIds=" + watch_id.lower()
        resp = await self.client.get(url)

        resp.raise_for_status()

        data: dict[str, Any] = resp.json()
        if data["meta"]["status"] != 200:
            raise ValueError(f"API返回代码: {data['meta']['status']}\n{data}")

        return data["data"]["items"][0]

    def generate_video_text(self, data: dict[str, Any], with_url: bool = True) -> str:
        def to_local_time(time: str) -> str:
            return (
                datetime.fromisoformat(time)
                .astimezone()
                .strftime("%Y年%m月%d日 %H:%M:%S")
            )

        def clean_description(desc: str) -> str:
            desc = "\n".join([x.strip() for x in desc.split("\n") if x.strip() != ""])
            if len(desc) > 200:
                desc = desc[:200] + "..."
            return desc

        template: Template = Template(
            (self.template_path / "video.jinja").read_text("utf-8")
        )
        return template.render(
            data=data,
            with_url=with_url,
            to_local_time=to_local_time,
            clean_description=clean_description,
        )
