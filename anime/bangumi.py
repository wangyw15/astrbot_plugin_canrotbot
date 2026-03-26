from typing import Any

from httpx import AsyncClient


class Bangumi:
    BANGUMI_API = "https://api.bgm.tv"

    def __init__(self, proxy: str) -> None:
        self.client = AsyncClient(proxy=proxy or None)

    async def get_airing_calendar(self) -> list[dict[str, Any]]:
        response = await self.client.get(
            self.BANGUMI_API + "/calendar",
            headers={
                "User-Agent": "wangyw15/astrbot_plugin_canrotbot (https://github.com/wangyw15/astrbot_plugin_canrotbot)",
            },
        )

        if not (response.is_success and response.status_code == 200):
            return []

        return response.json()
