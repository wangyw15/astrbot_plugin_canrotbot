import random
from datetime import datetime

import httpx
from jinja2 import Template

from . import manager


class MLTDTheme(manager.SigninTheme):
    def __init__(self) -> None:
        self.client = httpx.AsyncClient()
        self.cards: list[str] = []
        self.last_fetch: datetime | None = None

    @property
    def name(self) -> str:
        return "mltd"

    @property
    def aliases(self) -> list[str]:
        return ["麻辣土豆", "百万现场", "百万", "偶像大师百万现场"]

    async def generate(self, title: str, content: str) -> str:
        font = manager.ASSET_PATH / "fonts"
        css: Template = Template(
            (manager.ASSET_PATH / "templates" / "main.css").read_text("utf-8")
        )
        render_css = css.render(
            mamelon="file://" + str((font / "Mamelon.otf").absolute()),
            sakura="file://" + str((font / "sakura.ttf").absolute()),
        )

        template: Template = Template(
            (manager.ASSET_PATH / "templates" / "mltd.jinja").read_text("utf-8")
        )
        return template.render(
            main_style=render_css,
            resource_key=random.choice(await self.get_cards()),
            title=title,
            content=content,
        )

    async def get_cards(self):
        if (
            not self.cards
            or self.last_fetch is None
            or (datetime.now() - self.last_fetch).total_seconds() > 3600 * 24
        ):
            resp = await self.client.get(
                "https://api.matsurihi.me/api/mltd/v2/cards?   includeCostumes=true&includeParameters=true&includeLines=true&includeSkills=true&includeEvents=true"
            )
            if resp.is_success:
                data: list[dict] = resp.json()
                self.cards.clear()
                for card in data:
                    self.cards.append(card["resourceId"])
                self.last_fetch = datetime.now()

        return self.cards


manager.register_theme(MLTDTheme())
