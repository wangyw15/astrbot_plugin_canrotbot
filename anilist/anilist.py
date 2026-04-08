from pathlib import Path
from typing import Any

from httpx import AsyncClient


class AniList:
    ANILIST_API = "https://graphql.anilist.co"

    def __init__(self, proxy: str = "") -> None:
        self.client = AsyncClient(proxy=proxy or None, timeout=15)
        self.queries = Path(__file__).parent / "queries"

    async def query(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        response = await self.client.post(
            self.ANILIST_API,
            json={
                "query": query,
                "variables": variables,
            },
            headers={"Content-Type": "application/json", "Accept": "application/json"},
        )
        response.raise_for_status()
        return response.json()

    async def search_anime_by_title(self, keyword: str) -> dict[str, Any]:
        response = await self.query(
            query=(self.queries / "search_anime.graphql").read_text(encoding="utf-8"),
            variables={
                "search": keyword,
            },
        )
        return response["data"]["Page"]["media"][0]

    async def get_user_complete_anime_list(self, user_name: str) -> dict[str, Any]:
        result: dict[str, Any] = {"user": {}, "lists": []}
        finished = False

        while not finished:
            response = await self.query(
                query=(self.queries / "get_completed_anime.graphql").read_text(
                    encoding="utf-8"
                ),
                variables={"userName": user_name, "chunk": 1, "perChunk": 500},
            )
            response: dict[str, Any] = response["data"]["MediaListCollection"]

            finished = not response["hasNextChunk"]

            if not result["user"]:
                result["user"] = response["user"]

            if not result["lists"]:
                result["lists"] = response["lists"]
                continue

            result["lists"][0]["entries"].extend(response["lists"][0]["entries"])

        return result
