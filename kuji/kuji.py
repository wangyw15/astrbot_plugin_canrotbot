import base64
import json
import random
from collections.abc import Callable
from pathlib import Path
from typing import Literal

from jinja2 import Template

from astrbot.api import logger

T_Kuji = dict[str, str | list[str]]


class Kuji:
    def __init__(self) -> None:
        self.asset_path = Path(__file__).parent / "assets"
        with (self.asset_path / "kuji.json").open(encoding="utf-8") as f:
            self.kuji_data: list[T_Kuji] = json.load(f)
            logger.info(f"抽签数据条目数量: {len(self.kuji_data)}")

    async def generate_image(
        self,
        html_render: Callable,
        kuji: T_Kuji,
        image_type: Literal["png", "jpeg"] = "png",
    ) -> str:
        background = base64.b64encode(
            (self.asset_path / "templates" / "background.png").read_bytes()
        ).decode()
        return await html_render(
            (self.asset_path / "templates" / "html.jinja").read_text(encoding="utf-8"),
            {"kuji": kuji, "background": "data:image/png;base64," + background},
            options={
                "image_type": image_type,
            },
        )

    def get_kuji(self) -> T_Kuji:
        return random.choice(self.kuji_data)

    def generate_text(self, kuji: T_Kuji) -> str:
        template: Template = Template(
            (self.asset_path / "templates" / "text.jinja").read_text(encoding="utf-8")
        )
        return template.render(kuji=kuji)
