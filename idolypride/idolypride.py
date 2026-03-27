import os
from datetime import datetime
from typing import Any, cast
from urllib import parse

from bs4 import BeautifulSoup
from httpx import AsyncClient
from jinja2 import Environment, FileSystemLoader


class IdolyPride:
    def __init__(self, proxy: str = "") -> None:
        self.client = AsyncClient(proxy=proxy or None)
        self.idols: list[dict[str, str]] = []
        template_dir = os.path.join(os.path.dirname(__file__), "templates")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        self.jinja_env.filters["urlencode"] = lambda x: parse.quote(x)

    async def get_idols(self, update: bool = False) -> list[dict[str, str]]:
        if self.idols and not update:
            return self.idols

        resp = await self.client.get(
            "https://wiki.biligame.com/idolypride/%E8%A7%92%E8%89%B2%E5%9B%BE%E9%89%B4"
        )
        if not (resp.is_success and resp.status_code == 200):
            return self.idols

        soup = BeautifulSoup(resp.text)
        for group in soup.select("div.char"):
            group_name_element = group.select_one("div:first-child span")
            if group_name_element is None:
                continue

            group_name = group_name_element.text.split()[0]
            for character in group.select(".sawimg>a"):
                portrait = character.select_one("img")
                if portrait is None:
                    continue

                self.idols.append(
                    {
                        "name": cast(str, character.attrs["title"]),
                        "group": group_name,
                        "portrait": cast(str, portrait.attrs["src"]),
                        "page": "https://wiki.biligame.com"
                        + cast(str, character.attrs["href"]),
                    }
                )

        return self.idols

    async def get_calendar(self) -> list[dict[str, Any]]:
        resp = await self.client.get(
            "https://wiki.biligame.com/idolypride/api.php?"
            "action=expandtemplates&"
            "format=json&"
            "text=%7B%7B%23invoke%3A%E6%97%A5%E5%8E%86%E5%87%BD%E6%95%B0%7CgetAllData%7D%7D"
        )
        if resp.is_success and resp.status_code == 200:
            data = resp.json()["expandtemplates"]["*"]
            # 处理csv
            table: list[list[str]] = [
                line.split(",") for line in data.split(";") if line
            ]
            ret: list[dict] = []
            for row in table:
                try:
                    ret.append(
                        {
                            "start": datetime.strptime(row[0], "%Y/%m/%d"),
                            "end": datetime.strptime(row[1], "%Y/%m/%d"),
                            "name": row[2],
                            "type": row[3],
                            "page": row[4],
                            "color": row[5],
                        }
                    )
                except ValueError:
                    pass
            return ret
        return []

    async def get_today_events(self) -> list[dict[str, Any]]:
        data = await self.get_calendar()
        ret: list[dict] = []
        for i in data:
            if i["start"].date() <= datetime.now().date() <= i["end"].date():
                ret.append(i)
        return ret

    async def calendar_message(self, markdown: bool = False) -> str | None:
        data = await self.get_today_events()
        if not data:
            return None
        template_name = "calendar_md.jinja" if markdown else "calendar.jinja"
        template = self.jinja_env.get_template(template_name)
        return template.render(events=data).strip()
