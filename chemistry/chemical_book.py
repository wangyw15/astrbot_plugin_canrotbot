from pathlib import Path
from typing import TypedDict

from bs4 import BeautifulSoup
from httpx import AsyncClient
from jinja2 import Environment, FileSystemLoader

from .cas import CAS


class PriceItem(TypedDict):
    price: str
    spec: str


class SupplierInfo(TypedDict):
    supplier: str
    prices: list[PriceItem]


class ProductInfo(TypedDict):
    chinese_name: str
    english_name: str
    cas: str
    molecular_formula: str
    molecular_weight: str
    einecs: str
    mdl: str
    structural_formula: str


class Product(TypedDict):
    title: str
    info: ProductInfo | None
    suppliers: list[SupplierInfo]


class ChemicalBook:
    def __init__(self, proxy: str = "") -> None:
        self.cas = CAS()
        self.client = AsyncClient(proxy=proxy or None)
        self.client.headers = {
            "Referer": "https://www.chemicalbook.com/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0",
        }

        self.template_path = Path(__file__).parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader(self.template_path))

    async def fetch_bytes(self, url: str) -> bytes | None:
        resp = await self.client.get(url)

        try:
            resp.raise_for_status()
        except Exception:
            return None

        return resp.content

    async def get_structural_formula(self, cas_number: str) -> bytes | None:
        """可能会有获取不到的情况"""
        if not self.cas.validate(cas_number):
            return None

        url = "https://www.chemicalbook.com/CAS/GIF/{cas}.gif"
        return await self.fetch_bytes(url.format(cas=cas_number))

    async def get_product(self, cas_number: str) -> Product | None:
        if not self.cas.validate(cas_number):
            return None

        url = "https://www.chemicalbook.com/ProductList.aspx?kwd={cas}"
        resp = await self.client.get(url.format(cas=cas_number))
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "html.parser")

        title = ""
        if soup.title:
            title = soup.title.get_text(strip=True)

        info: ProductInfo | None = None
        if plbox := soup.select_one("div.PLbox"):
            info = {
                "chinese_name": "",
                "english_name": "",
                "cas": "",
                "molecular_formula": "",
                "molecular_weight": "",
                "einecs": "",
                "mdl": "",
                "structural_formula": "",
            }
            if h2 := plbox.select_one("h2"):
                info["chinese_name"] = h2.get_text(strip=True)

            if img := plbox.select_one("img"):
                info["structural_formula"] = str(img.get("src", "")).strip()

            if foldbox := plbox.select_one("div.FoldBox"):
                for dl in foldbox.select("dl"):
                    dt = dl.select_one("dt")
                    dd = dl.select_one("dd")
                    if dt and dd:
                        key = dt.get_text(strip=True)
                        value = dd.get_text(strip=True)
                        if key == "英文名称：":
                            info["english_name"] = value
                        elif key == "CAS号：":
                            info["cas"] = value
                        elif key == "分子式：":
                            info["molecular_formula"] = value
                        elif key == "分子量：":
                            info["molecular_weight"] = value
                        elif key == "EINECS号：":
                            info["einecs"] = value
                        elif key == "MDL No.：":
                            info["mdl"] = value

        suppliers: list[SupplierInfo] = []
        for prolistbox in soup.select("div.ProListBox"):
            for item in prolistbox.select("div.ProLbox"):
                if item.select_one("div.AD"):
                    continue

                supplier = ""
                if downwards := item.select_one("div.Downwards"):
                    supplier = str(downwards.get("data-suppliername", "")).strip()
                    if not supplier:
                        a_tag = downwards.select_one("a")
                        if a_tag:
                            supplier = a_tag.get_text(strip=True)

                prices: list[PriceItem] = []
                if plprice := item.select_one("ul.PLPrice"):
                    for li in plprice.select("li"):
                        strong = li.select_one("strong")
                        span = li.select_one("span")
                        if strong and span:
                            price_text = strong.get_text(strip=True).strip()
                            spec = span.get_text(strip=True)
                            prices.append(PriceItem(price=price_text, spec=spec))

                suppliers.append(SupplierInfo(supplier=supplier, prices=prices))

        return {
            "title": title,
            "info": info,
            "suppliers": suppliers,
        }

    def get_product_text(self, product: Product) -> str:
        template = self.jinja_env.get_template("product.jinja")
        return template.render(product=product)
