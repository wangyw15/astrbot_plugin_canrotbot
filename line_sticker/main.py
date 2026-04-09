import re
from pathlib import Path

import astrbot.api.message_components as Comp
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core import astrbot_config
from astrbot.core.utils.astrbot_path import get_astrbot_data_path

from .line_sticker import LineSticker


class LineStickerPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.line_sticker = LineSticker(astrbot_config.get("http_proxy", ""))
        self.data_path = Path(get_astrbot_data_path()) / "plugin_data" / self.name
        if not self.data_path.exists():
            self.data_path.mkdir(parents=True)

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def line_sticker_link(self, event: AstrMessageEvent):
        """监听Line贴纸链接"""
        match = re.search(self.line_sticker.LINK_PATTERN, event.message_str)
        if match is None:
            return

        sticker_id = match[1]
        file_path: Path | None = None
        for i in self.data_path.glob("*.zip"):
            if i.stem == sticker_id:
                file_path = i
                break

        if file_path is None:
            sticker = await self.line_sticker.get_line_sticker(sticker_id)

            if sticker is None:
                return

            sticker_name, file_data = sticker
            file_path = self.data_path / f"{sticker_id}.zip"
            with file_path.open("wb") as f:
                f.write(file_data)

        return event.chain_result([Comp.File(file_path.name, file=str(file_path))])
