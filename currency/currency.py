from pathlib import Path
from typing import Literal, TypedDict

from httpx import AsyncClient
from jinja2 import Environment, FileSystemLoader, Template


class CurrencyData(TypedDict):
    currencyType: str
    currencyCHName: str
    currencyENName: str
    reference: str
    foreignBuy: str
    foreignSell: str
    cashBuy: str
    cashSell: str
    publishDate: str
    publishTime: str


class CurrencyResponseSchema(TypedDict):
    code: int
    message: str
    data: list[CurrencyData]


class Currency:
    def __init__(self, proxy: str = "") -> None:
        self.client = AsyncClient(proxy=proxy or None)

        self.template_path = Path(__file__).parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader([self.template_path]))

    def generate_info(
        self,
        currency_data: CurrencyData,
        format: Literal["plain", "markdown"] = "plain",
    ) -> str:
        template: Template | None = None

        if format == "plain":
            template = self.jinja_env.get_template("plain.jinja")
        elif format == "markdown":
            template = self.jinja_env.get_template("markdown.jinja")

        if template is None:
            raise ValueError(f"Template not found: {format}")

        return template.render(currency=currency_data)

    async def fetch(self) -> list[CurrencyData]:
        resp = await self.client.get("http://papi.icbc.com.cn/exchanges/ns/getLatest")
        resp.raise_for_status()

        data: CurrencyResponseSchema = resp.json()
        if data["message"] == "success" and data["code"] == 0:
            return data["data"]
        raise ValueError(
            f"Failed to fetch currency data: code {data['code']}, messsage: {data['message']}"
        )
