import json
import re

from httpx import AsyncClient

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star


class CurrencyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.client = AsyncClient()

    async def terminate(self):
        if hasattr(self, "client") and self.client:
            await self.client.aclose()

    async def fetch_currency(self) -> list[dict[str, str]]:
        try:
            resp = await self.client.get(
                "http://papi.icbc.com.cn/exchanges/ns/getLatest"
            )
            if resp.status_code == 200:
                data = resp.json()
                if data["message"] == "success" and data["code"] == 0:
                    return data["data"]
        except Exception as e:
            logger.error(f"Failed to fetch currency data: {e}")
        return []

    @filter.llm_tool("fetch_currency")
    async def fetch_currency_tool(self, event: AstrMessageEvent):
        """
        Fetch current currency rate from ICBC

        Returns:
            Currency rate in JSON format, all the unit of the price is 100 foreign currency
        """
        return json.dumps(await self.fetch_currency(), ensure_ascii=False)

    @filter.command("currency")
    async def currency_command(self, event: AstrMessageEvent, currency: str):
        """通过命令查询指定货币的汇率"""
        currency_data = await self.fetch_currency()
        if not currency_data:
            return event.plain_result("汇率获取失败")

        for item in currency_data:
            if (
                currency.lower() == item["currencyENName"].lower()
                or currency == item["currencyCHName"]
            ):
                return event.plain_result(
                    f"""
币种：{item["currencyCHName"]}({item["currencyENName"]})
参考价格：  {item["reference"]}
现汇买入价：{item["foreignBuy"]}
现钞买入价：{item["cashBuy"]}
现汇卖出价：{item["foreignSell"]}
现钞卖出价：{item["cashSell"]}
发布时间：{item["publishDate"]} {item["publishTime"]}
单位：人民币/100外币
                """.strip()
                )

        return event.plain_result(f"未找到货币: {currency}")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def currency_regex(self, event: AstrMessageEvent):
        """根据正则自动触发汇率转换计算，如100jpy"""
        pattern = re.compile(r"^([\d()\-+*/.]+)?([a-zA-Z]{3})([a-zA-Z]{3})?$")

        match = re.fullmatch(pattern, event.message_str)
        if match is None:
            return

        # 处理数据
        amount: float = float(eval(match[1])) if match[1] else 100.0
        currency_from: str = match[2]
        currency_to = match[3] or "cny"

        # 获取汇率数据
        currency_data = await self.fetch_currency()
        if not currency_data:
            return event.plain_result("汇率获取失败")

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

        # 只在提供数字是提示错误
        if match[1]:
            return event.plain_result("未找到货币: " + " ".join(currency_not_found))
