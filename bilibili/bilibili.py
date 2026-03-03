import re
from datetime import datetime
from pathlib import Path
from typing import Literal

from httpx import AsyncClient
from jinja2 import Template


class Bilibili:
    def __init__(self) -> None:
        self.client = AsyncClient()
        self.client.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.5666.197 Safari/537.36"
        }

        self.vid_pattern = re.compile(
            r"(?:https?:\/\/)?(?:(?:www\.)?bilibili.com\/video|b23\.tv)\/((?:[AaBb][Vv])[0-9A-Za-z]+)"
        )
        self.short_link_pattern = re.compile(r"https:\/\/b23.tv\/(?!BV)[0-9A-Za-z]{7}")

        self.projects_url = "https://show.bilibili.com/api/ticket/project/listV3?page={page}&pagesize=20&platform=web&area={area}&p_type={project_type}&style=1"

        self.asset_path = Path(__file__).parent / "assets"

    async def fetch_json_data(self, url: str) -> dict | None:
        resp = await self.client.get(url)
        if resp.is_success and resp.status_code == 200:
            return resp.json()

    async def fetch_video_data(self, vid: str) -> dict | None:
        url = ""
        if vid.lower().startswith("bv"):
            url = f"https://api.bilibili.com/x/web-interface/view?bvid={vid}"
        elif vid.lower().startswith("av"):
            url = f"https://api.bilibili.com/x/web-interface/view?aid={vid[2:]}"
        if not url:
            return None
        raw_data = await self.fetch_json_data(url)
        if raw_data and raw_data["code"] == 0:
            return raw_data["data"]
        return None

    async def get_bvid_from_short_link(self, url: str) -> str | None:
        resp = await self.client.get(url, follow_redirects=False)
        if resp.status_code == 302:
            if match := re.match(self.vid_pattern, resp.headers["Location"]):
                return match[1]
        return None

    async def get_projects(
        self,
        area: str = "310000",
        project_type: Literal["全部类型", "演出", "展览", "本地生活"] = "全部类型",
        limit: int = 0,
    ) -> list[dict]:
        first_page = await self.fetch_json_data(
            self.projects_url.format(page=1, area=area, project_type=project_type)
        )
        if first_page and first_page["errno"] == 0:
            total_pages = first_page["data"]["numPages"]
            result: list[dict] = first_page["data"]["result"]
            for page in range(2, total_pages + 1):
                if len(result) >= limit:
                    break

                page_data = await self.fetch_json_data(
                    self.projects_url.format(
                        page=page, area=area, project_type=project_type
                    )
                )
                if page_data and page_data["errno"] == 0:
                    result.extend(page_data["data"]["result"])
            return result
        return []

    def generate_video_text(self, data: dict, with_url: bool = True) -> str:
        def timestamp_to_str(timestamp: str) -> str:
            return datetime.fromtimestamp(float(timestamp)).strftime(
                "%Y年%m月%d日 %H:%M:%S"
            )

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
            timestamp_to_str=timestamp_to_str,
            clean_description=clean_description,
        )

    def generate_project_text(self, projects: list[dict], with_url: bool = True) -> str:
        template: Template = Template(
            (self.asset_path / "project.jinja").read_text("utf-8")
        )
        return template.render(
            data=projects,
            with_url=with_url,
        )
