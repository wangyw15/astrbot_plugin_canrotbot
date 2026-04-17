from typing import Any

from httpx import AsyncClient, HTTPStatusError


class Bangumi:
    BANGUMI_API = "https://api.bgm.tv"

    def __init__(self, proxy: str) -> None:
        self.client = AsyncClient(proxy=proxy or None)
        self.client.headers = {
            "User-Agent": "wangyw15/astrbot_plugin_canrotbot (https://github.com/wangyw15/astrbot_plugin_canrotbot)",
            "Accept": "application/json",
        }

    async def get_airing_calendar(self) -> list[dict[str, Any]]:
        response = await self.client.get(self.BANGUMI_API + "/calendar")

        try:
            response.raise_for_status()
        except HTTPStatusError:
            return []

        return response.json()

    async def search_anime_by_keyword(
        self, keyword: str, count: int = 10
    ) -> list[dict[str, Any]]:
        payload = {
            "keyword": keyword,
            "sort": "match",
            "filter": {
                "type": [2]  # 2 = 动画
            },
        }

        result: list[dict[str, Any]] = []
        total: int = -1

        while len(result) < count and len(result) < total or total == -1:
            response = await self.client.post(
                self.BANGUMI_API + "/v0/search/subjects",
                params={"limit": 30, "offset": len(result)},
                json=payload,
            )
            try:
                response.raise_for_status()
            except HTTPStatusError:
                return result

            data = response.json()
            result.extend(data["data"])
            total = data["total"]

        return result[:count]
