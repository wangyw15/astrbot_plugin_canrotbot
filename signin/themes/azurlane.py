import random
from datetime import datetime
from typing import cast

import httpx
from bs4 import BeautifulSoup
from jinja2 import Template

from . import manager


class AzurLaneTheme(manager.SigninTheme):
    def __init__(self) -> None:
        self.client = httpx.AsyncClient()
        self.ships: dict[str, str] = {}
        self.last_fetch: datetime | None = None

    @property
    def name(self) -> str:
        return "azurlane"

    @property
    def aliases(self) -> list[str]:
        return ["碧蓝航线", "舰b", "AzurLane", "blhx"]

    async def generate(self, title: str, content: str):
        font = manager.ASSET_PATH / "fonts"
        css: Template = Template(
            (manager.ASSET_PATH / "templates" / "main.css").read_text("utf-8")
        )
        render_css = css.render(
            mamelon="file://" + str((font / "Mamelon.otf").absolute()),
            sakura="file://" + str((font / "sakura.ttf").absolute()),
        )

        template: Template = Template(
            (manager.ASSET_PATH / "templates" / "azurlane.jinja").read_text("utf-8")
        )
        return template.render(
            main_style=render_css,
            image=await self.get_random_ship_image_url(),
            title=title,
            content=content,
        )

    async def get_ships(self) -> dict[str, str]:
        if (
            not self.ships
            or not self.last_fetch
            or (datetime.now() - self.last_fetch).total_seconds() > 3600 * 24
        ):
            resp = await self.client.get(
                "https://wiki.biligame.com/blhx/%E8%88%B0%E8%88%B9%E5%9B%BE%E9%89%B4"
            )
            if resp.is_success and resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                self.ships.clear()
                for i in soup.select(".jntj-1"):
                    a = i.select_one(".jntj-4>a")
                    if a is not None:
                        self.ships[a.get_text()] = "https://wiki.biligame.com" + cast(
                            str, a["href"]
                        )
                self.last_fetch = datetime.now()
        return self.ships

    async def get_random_ship_image_url(self) -> str | None:
        ships = await self.get_ships()
        ship: str = random.choice(list(ships.keys()))
        url: str = ships[ship]
        resp = await self.client.get(url)
        if resp.is_success and resp.status_code == 200:
            soup = BeautifulSoup(resp.text, "html.parser")
            if element := soup.select_one(".wiki-bot-img"):
                return cast(str, element["src"])
        return None


manager.register_theme(AzurLaneTheme())
