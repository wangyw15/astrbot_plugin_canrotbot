from httpx import AsyncClient


class Weather:
    def __init__(self) -> None:
        self.api_url = "https://aviationweather.gov/api/data/"
        self.client = AsyncClient()

    async def metar(self, icao_codes: str | list[str]) -> None | list:
        if isinstance(icao_codes, list):
            icao_codes = ",".join(icao_codes)

        resp = await self.client.get(
            self.api_url + "metar",
            params={
                "ids": icao_codes,
                "format": "json",
            },
        )

        if resp.is_success:
            return resp.json()

    async def taf(
        self, icao_codes: str | list[str], include_metar: bool = False
    ) -> None | list:
        if isinstance(icao_codes, list):
            icao_codes = ",".join(icao_codes)

        resp = await self.client.get(
            self.api_url + "taf",
            params={
                "ids": icao_codes,
                "metar": str(include_metar).lower(),
                "format": "json",
            },
        )

        if resp.is_success:
            return resp.json()
