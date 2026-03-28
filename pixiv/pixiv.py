from typing import Any, TypedDict

from httpx import AsyncClient, HTTPStatusError


class Urls(TypedDict):
    mini: str
    thumb: str
    small: str
    regular: str
    original: str


class Illustration(TypedDict):
    illust_id: str
    title: str
    description: str
    upload_date: str
    urls: Urls
    tags: list[str]
    like: int
    comment: int
    view: int


class Pixiv:
    ILLUSTRATION_PATTERN = r"(?:https?:\/\/)?(?:www\.)?pixiv\.net\/artworks\/(\d+)"

    ILLUSTRATION_API = "https://www.pixiv.net/ajax/illust/{illust_id}"

    def __init__(self, proxy: str = "") -> None:
        self.client = AsyncClient(proxy=proxy or None)

    async def get_illustration_info(self, illust_id: str) -> Illustration | None:
        response = await self.client.get(
            self.ILLUSTRATION_API.format(illust_id=illust_id)
        )

        try:
            response.raise_for_status()
        except HTTPStatusError:
            return None

        raw_data: dict[str, Any] = response.json()
        if raw_data["error"]:
            return None

        body: dict[str, Any] = raw_data["body"]
        return {
            "illust_id": body["illustId"],
            "title": body["title"],
            "description": body["description"],
            "upload_date": body["uploadDate"],
            "urls": body["urls"],
            "tags": [x["tag"] for x in body["tags"]["tags"]],
            "like": body["likeCount"],
            "comment": body["commentCount"],
            "view": body["viewCount"],
        }

    async def download(self, url: str) -> bytes | None:
        response = await self.client.get(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.51",
                "Referer": "https://www.pixiv.net/",
            },
        )

        try:
            response.raise_for_status()
        except HTTPStatusError:
            return None

        return response.content
