from typing import Any

from httpx import AsyncClient


class AniList:
    ANILIST_API = "https://graphql.anilist.co"

    def __init__(self, proxy: str = "") -> None:
        self.client = AsyncClient(proxy=proxy or None)

    async def search_anime_by_title(self, keyword: str) -> dict[str, Any]:
        query = """
query SearchQuery($search: String) {
    Page(page: 0, perPage: 1) {
        media(type: ANIME, search: $search) {
            title {
                native
                english
            }
            description
            format
            episodes
            season
            seasonYear
            startDate {
                year
                month
                day
            }
            endDate {
                year
                month
                day
            }
            status
            synonyms
            genres
            tags {
                name
            }
        }
    }
}
"""
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
