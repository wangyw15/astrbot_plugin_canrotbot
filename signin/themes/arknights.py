import random
from datetime import datetime

import httpx
from jinja2 import Template

from . import manager


class ArknightsTheme(manager.SigninTheme):
    PROFESSIONS = [
        "PIONEER",
        "WARRIOR",
        "SNIPER",
        "CASTER",
        "SUPPORT",
        "MEDIC",
        "SPECIAL",
        "TANK",
    ]

    def __init__(self) -> None:
        self.client = httpx.AsyncClient()
        self.operators: list[str] = []
        self.last_fetch: datetime | None = None

    @property
    def name(self) -> str:
        return "arknights"

    @property
    def aliases(self) -> list[str]:
        return ["明日方舟", "方舟", "鹰角", "Arknights", "舟游"]

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
            (manager.ASSET_PATH / "templates" / "arknights.jinja").read_text("utf-8")
        )
        return template.render(
            main_style=render_css,
            resource_key=random.choice(await self.get_operators()),
            title=title,
            content=content,
        )

    async def get_operators(self):
        if (
            not self.operators
            or self.last_fetch is None
            or (datetime.now() - self.last_fetch).total_seconds() > 3600 * 24
        ):
            resp = await self.client.get(
                "https://raw.githubusercontent.com/yuanyan3060/ArknightsGameResource/main/gamedata/excel/character_table.json"
            )
            if resp.is_success:
                data: dict = resp.json()
                self.operators.clear()
                for k, v in data.items():
                    if v["profession"] in self.PROFESSIONS:
                        self.operators.append(k)
                self.last_fetch = datetime.now()

        return self.operators


manager.register_theme(ArknightsTheme())
