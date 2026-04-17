from typing import Any

from httpx import AsyncClient, HTTPStatusError


class Bangumi:
    BANGUMI_API = "https://api.bgm.tv"

    def __init__(self, proxy: str) -> None:
        self.client = AsyncClient(proxy=proxy or None)
        self.client.headers = {
            "User-Agent": "wangyw15/astrbot_plugin_canrotbot (https://github.com/wangyw15/astrbot_plugin_canrotbot)",
        }

    async def get_airing_calendar(self) -> list[dict[str, Any]]:
        response = await self.client.get(self.BANGUMI_API + "/calendar")

        try:
            response.raise_for_status()
        except HTTPStatusError:
            return []

        return response.json()
