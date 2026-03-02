import json
import random
from pathlib import Path

from astrbot.api import logger


class Fortune:
    def __init__(self) -> None:
        self.fortune: list[dict] = []
        self.load()

    def load(self):
        fortune_path = Path(__file__).parent / "assets" / "fortunes.json"
        fortune_data: dict = json.loads(fortune_path.read_text("utf-8"))
        self.fortune = fortune_data["copywriting"]
        logger.info(f"数据版本: {fortune_data['version']}")

    def get_fortune(self) -> tuple[str, str]:
        fortune = random.choice(self.fortune)
        title: str = fortune["good-luck"]
        content: str = random.choice(fortune["content"])
        return title, content

    def __call__(self) -> tuple[str, str]:
        return self.get_fortune()
