import re

from astrbot.api import message_components as Comp
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core import astrbot_config

from .cas import CAS


class ChemistryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

        self.cas = CAS(astrbot_config.get("http_proxy", ""))

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def cas_number_handler(self, event: AstrMessageEvent):
        if match := re.search(self.cas.CAS_PATTERN, event.message_str):
            if self.cas.validate_cas(event.message_str):
                image = await self.cas.get_structural_formula(match[0])
                if image is None:
                    return event.plain_result("未找到该CAS对应的结构图")
                return event.chain_result([Comp.Image.fromBytes(image)])
