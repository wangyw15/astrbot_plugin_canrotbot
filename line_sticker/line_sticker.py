from bs4 import BeautifulSoup
from httpx import AsyncClient

from astrbot.api import logger


class LineSticker:
    LINK_PATTERN = r"(?:https?:\/\/)?store\.line\.me\/stickershop\/product\/(\d+)"

    def __init__(self, proxy: str = "") -> None:
        self.client = AsyncClient(proxy=proxy or None)

    async def get_line_sticker(self, sticker_id: str) -> tuple[str, bytes] | None:
        info_resp = await self.client.get(
            f"https://store.line.me/stickershop/product/{sticker_id}/en"
        )
        info_resp.raise_for_status()
        soup = BeautifulSoup(info_resp.text, "html.parser")

        # 贴纸名称
        sticker_name = sticker_id
        if elem := soup.select_one('p[data-test="sticker-name-title"]'):
            sticker_name = elem.text.strip()

        # 下载文件
        sticker_resp = await self.client.get(
            f"https://stickershop.line-scdn.net/stickershop/v1/product/{sticker_id}/iphone/stickerpack@2x.zip"
        )
        if sticker_resp.status_code == 200:
            logger.info(f"Downloaded {sticker_name} stickerpack@2x.zip")
            return sticker_name, sticker_resp.content

        sticker_resp = await self.client.get(
            f"https://stickershop.line-scdn.net/stickershop/v1/product/{sticker_id}/iphone/stickers@2x.zip"
        )
        if sticker_resp.status_code == 200:
            logger.info(f"Downloaded {sticker_name} stickers@2x.zip")
            return sticker_name, sticker_resp.content

        return None
