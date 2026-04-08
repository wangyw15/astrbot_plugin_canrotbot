from pathlib import Path
from typing import Any

from httpx import AsyncClient


class AniList:
    ANILIST_API = "https://graphql.anilist.co"

    def __init__(self, proxy: str = "") -> None:
        self.client = AsyncClient(proxy=proxy or None)
        self.queries = Path(__file__).parent / "queries"

    async def search_anime_by_title(self, keyword: str) -> dict[str, Any]:
        query = (self.queries / "search_anime.graphql").read_text(encoding="utf-8")
        variables = {
            "search": keyword,
        }
        payload = {
            "query": query,
            "variables": variables,
        }

        response = await self.client.post(
            self.ANILIST_API,
            json=payload,
        )
        if not (response.is_success and response.status_code == 200):
            return {}

        return response.json()
