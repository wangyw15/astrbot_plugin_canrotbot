from typing import Literal

from httpx import AsyncClient


class Waifu:
    API_URL = "https://api.waifu.pics/{type}/{category}"
    AVAILABLE_CATEGORY = [
        "waifu",
        "neko",
        "shinobu",
        "megumin",
        "bully",
        "cuddle",
        "cry",
        "hug",
        "awoo",
        "kiss",
        "lick",
        "pat",
        "smug",
        "bonk",
        "yeet",
        "blush",
        "smile",
        "wave",
        "highfive",
        "handhold",
        "nom",
        "bite",
        "glomp",
        "slap",
        "kill",
        "kick",
        "happy",
        "wink",
        "poke",
        "dance",
        "cringe",
    ]

    def __init__(self, proxy: str = "") -> None:
        self.client = AsyncClient(proxy=proxy or None)

    async def get_waifu_url(
        self,
        category: str,
        image_type: Literal["sfw", "nsfw"] = "sfw",
    ) -> str:
        if category not in self.AVAILABLE_CATEGORY:
            raise ValueError(f"Invalid category {category}")

        response = await self.client.get(
            self.API_URL.format(type=image_type, category=category)
        )
        response.raise_for_status()
        return response.json()["url"]
