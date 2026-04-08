import re

from httpx import AsyncClient


class CAS:
    CAS_PATTERN = r"(\d{2,7})-(\d{2})-(\d)"

    def __init__(self, proxy: str = "") -> None:
        self.client = AsyncClient(proxy=proxy or None)

    def validate_cas(self, cas_number: str) -> bool:
        if match := re.fullmatch(self.CAS_PATTERN, cas_number):
            part1 = match[1]
            part2 = match[2]
            part3 = match[3]

            check_digit = 0
            for i, digit in enumerate(reversed(part1 + part2)):
                check_digit += int(digit) * (i + 1)
            check_digit = check_digit % 10

            if part3 == str(check_digit):
                return True

        return False

    async def get_structural_formula(self, cas_number: str) -> bytes | None:
        if not self.validate_cas(cas_number):
            return None

        url = "https://www.chemicalbook.com/CAS/GIF/{cas}.gif"
        resp = await self.client.get(
            url.format(cas=cas_number),
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36 Edg/146.0.0.0"
            },
        )

        try:
            resp.raise_for_status()
        except Exception:
            return None

        return resp.content
