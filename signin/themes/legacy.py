import base64
import json
import random

from jinja2 import Template

from astrbot.api import logger

from . import manager


class LegacyTheme(manager.SigninTheme):
    def __init__(self, name: str, aliases: list[str]) -> None:
        self._name = name
        self._aliases = aliases

    @property
    def name(self) -> str:
        return self._name

    @property
    def aliases(self) -> list[str]:
        return self._aliases

    async def generate(self, title: str, content: str):
        theme_path = manager.ASSET_PATH / "images" / self.name
        image = random.choice(list(theme_path.iterdir()))

        font = manager.ASSET_PATH / "fonts"
        css: Template = Template(
            (manager.ASSET_PATH / "templates" / "main.css").read_text("utf-8")
        )
        render_css = css.render(
            mamelon="file://" + str((font / "Mamelon.otf").absolute()),
            sakura="file://" + str((font / "sakura.ttf").absolute()),
        )

        template: Template = Template(
            (manager.ASSET_PATH / "templates" / "legacy.jinja").read_text("utf-8")
        )
        return template.render(
            main_style=render_css,
            image="data:image/png;base64,"
            + base64.b64encode(image.read_bytes()).decode("utf-8"),
            title=title,
            content=content,
        )


def load_legacy_themes():
    with open(manager.ASSET_PATH / "legacy_themes.json", encoding="utf-8") as f:
        themes: dict[str, list[str]] = json.load(f)

    for name, aliases in themes.items():
        manager.register_theme(LegacyTheme(name, aliases))
        logger.info(f"已加载签到主题: {name}")


load_legacy_themes()
