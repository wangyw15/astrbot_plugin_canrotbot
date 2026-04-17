import re

from astrbot.api import message_components as Comp
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core import astrbot_config

from .cas import CAS
from .chemical_book import ChemicalBook


class ChemistryPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

        self.cas = CAS()
        self.chemical_book = ChemicalBook(astrbot_config.get("http_proxy", ""))

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def cas_number_handler(self, event: AstrMessageEvent):
        if match := re.search(self.cas.CAS_PATTERN, event.message_str):
            cas_number = match[0]
            if self.cas.validate(cas_number):
                info = await self.chemical_book.get_product(cas_number)
                if info is None:
                    return

                msg_chain = []
                if info["info"]["structural_formula"]:
                    if image := await self.chemical_book.fetch_bytes(
                        info["info"]["structural_formula"]
                    ):
                        msg_chain.append(Comp.Image.fromBytes(image))
                msg_chain.append(Comp.Plain(self.chemical_book.get_product_text(info)))

                return event.chain_result(msg_chain)
