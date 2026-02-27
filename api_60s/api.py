from typing import Literal

from httpx import AsyncClient


class API60s:
    def __init__(self) -> None:
        self.client = AsyncClient()
        self.api_url = "https://60s.viki.moe/v2"

    async def news(
        self,
        date: str = "",
        encoding: Literal["text", "json", "markdown", "image", "image-proxy"] = "json",
    ):
        """每天 60 秒读懂世界"""
        resp = await self.client.get(
            self.api_url + "/60s",
            params={
                "date": date,
                "encoding": encoding,
            },
        )

        if resp.is_success and resp.status_code == 200:
            if encoding.startswith("image"):
                return resp.content
            return resp.text

    async def today_in_history(
        self, encoding: Literal["text", "json", "markdown"] = "json"
    ):
        """历史上的今天"""
        resp = await self.client.get(
            self.api_url + "/today-in-history",
            params={
                "encoding": encoding,
            },
        )

        if resp.is_success and resp.status_code == 200:
            return resp.text

    async def gold_price(self, encoding: Literal["text", "json", "markdown"] = "json"):
        """黄金价格"""
        resp = await self.client.get(
            self.api_url + "/gold-price",
            params={
                "encoding": encoding,
            },
        )

        if resp.is_success and resp.status_code == 200:
            return resp.text

    async def fuel_price(
        self,
        region: str = "上海",
        encoding: Literal["text", "json", "markdown"] = "json",
    ):
        """汽油价格"""
        resp = await self.client.get(
            self.api_url + "/fuel-price",
            params={
                "region": region,
                "encoding": encoding,
            },
        )

        if resp.is_success and resp.status_code == 200:
            return resp.text
