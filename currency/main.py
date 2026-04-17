import json
import re
from typing import Literal

from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core import astrbot_config

from .currency import Currency


class CurrencyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.currency = Currency(astrbot_config.get("http_proxy", ""))

    @filter.llm_tool("fetch_currency")
    async def fetch_currency_tool(self, event: AstrMessageEvent):
        """从中国工商银行获取当前汇率"""
        return json.dumps(await self.currency.fetch(), ensure_ascii=False)

    @filter.command("currency")
    async def currency_command(self, event: AstrMessageEvent, currency: str):
        """通过命令查询指定货币的汇率"""
        result = await self._query_currency(currency)
        return event.plain_result(result)

    @filter.llm_tool("query_currency")
    async def query_currency_tool(self, event: AstrMessageEvent, currency: str):
        """查询指定货币对人民币的汇率。currency 参数可以是货币的中文名称（如 日元、美元）或英文代码（如 JPY、USD）。"""
        return await self._query_currency(currency, "markdown")

    async def _query_currency(
        self, currency: str, format: Literal["plain", "markdown"] = "plain"
    ) -> str:
        currencies = await self.currency.fetch()

        for item in currencies:
            if (
                currency.lower() == item["currencyENName"].lower()
                or currency == item["currencyCHName"]
            ):
                return self.currency.generate_info(item, format)

        return f"未找到货币: {currency}"

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def currency_regex(self, event: AstrMessageEvent):
        """根据正则自动触发汇率转换计算，如100jpy"""
        pattern = re.compile(r"((?:[\d()\-+*/.]+)?)([a-zA-Z]{3})((?:[a-zA-Z]{3})?)")

        match = re.fullmatch(pattern, event.message_str)
        if match is None:
            return

        # 处理数据
        amount: float = float(eval(match[1])) if match[1] else 100.0
        currency_from: str = match[2]
        currency_to: str = match[3] or "cny"

        # 获取汇率数据
        currency_data = await self.currency.fetch()

        price_from = 0.0
        price_to = 0.0
        name_from = ""
        name_to = ""
        for item in currency_data:
            # 源货币
            if currency_from.lower() == item["currencyENName"].lower():
                price_from = float(item["foreignBuy"])
                name_from = item["currencyCHName"]
            elif currency_from.lower() in ["rmb", "cny"]:
                price_from = 100
                name_from = "人民币"

            # 目标货币
            if currency_to.lower() == item["currencyENName"].lower():
                price_to = float(item["foreignSell"])
                name_to = item["currencyCHName"]
            elif currency_to.lower() in ["rmb", "cny"]:
                price_to = 100
                name_to = "人民币"

        # 计算结果
        if price_from and price_to:
            return event.plain_result(
                f"{amount:.4f}{name_from}={amount * price_from / price_to:.4f}{name_to}"
            )

        # 错误处理
        currency_not_found: list[str] = []
        if not price_from:
            currency_not_found.append(currency_from)
        if not price_to:
            currency_not_found.append(currency_to)

        # 只在提供数字时提示错误
        if match[1]:
            return event.plain_result("未找到货币: " + " ".join(currency_not_found))
