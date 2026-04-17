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
                product = await self.chemical_book.get_product(cas_number)
                if product is None:
                    return

                if product["info"] is None:
                    return event.plain_result(
                        f"Chemical Book网站不提供 {product['title']} 的信息"
                    )

                msg_chain = []
                if product["info"]["structural_formula"]:
                    if image := await self.chemical_book.fetch_bytes(
                        product["info"]["structural_formula"]
                    ):
                        msg_chain.append(Comp.Image.fromBytes(image))
                msg_chain.append(
                    Comp.Plain(self.chemical_book.get_product_text(product))
                )

                return event.chain_result(msg_chain)

    @filter.llm_tool("chemical_book_get_product")
    async def chemical_book_get_product_tool(
        self, event: AstrMessageEvent, cas_number: str
    ):
        """
        从ChemicalBook查询指定CAS号化学品的详细信息，包括英文名称、分子式、分子量、供应商报价等。
        当用户询问CAS号对应的化学品信息、供应商、价格或相关问题时优先使用。

        Args:
            cas_number(string): CAS号，格式为\\d{2,7}-\\d{2}-\\d
        """
        if not self.cas.validate(cas_number):
            return "CAS号格式不正确"

        product = await self.chemical_book.get_product(cas_number)
        if product is None:
            return "未找到该CAS号对应的产品信息"

        if product["info"] is None:
            return f"Chemical Book网站不提供 {product['title']} 的信息"

        return self.chemical_book.get_product_text(product)
