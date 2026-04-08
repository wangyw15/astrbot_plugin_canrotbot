import json

from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .weather import Weather


class AviationPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.weather = Weather()

    @filter.llm_tool("metar")
    async def metar_tool(self, event: AstrMessageEvent, icao_codes: str):
        """
        从Aviation Weather Center获取航空例行天气报告（METAR）报文，查询机场天气时优先使用

        Args:
            icao_codes(string): 一个ICAO代码或多个机场代码，用逗号分隔
        """
        if result := await self.weather.metar(icao_codes):
            return json.dumps(result, ensure_ascii=False)
        else:
            return "获取失败"

    @filter.llm_tool("taf")
    async def taf_tool(
        self, event: AstrMessageEvent, icao_codes: str, include_metar: bool
    ):
        """
        从Aviation Weather Center获取终端机场天气预报（TAF）报文

        Args:
            icao_codes(string): 一个ICAO代码或多个机场代码，用逗号分隔
            include_metar(boolean): 是否包含METAR报文
        """
        if result := await self.weather.taf(icao_codes, include_metar):
            return json.dumps(result, ensure_ascii=False)
        else:
            return "获取失败"

    @filter.command("metar")
    async def metar_command(self, event: AstrMessageEvent, icao_codes: str):
        """查询指定机场的METAR报文"""
        codes = icao_codes.replace("，", ",").replace(",", " ").split()
        if result := await self.weather.metar(codes):
            msg = ""
            for metar in result:
                msg += metar["icaoId"] + "(" + metar["name"] + ")\n"
                msg += metar["rawOb"] + "\n\n"
            return event.plain_result(msg.strip())
        return event.plain_result("METAR信息获取失败")

    @filter.command("taf")
    async def taf_command(self, event: AstrMessageEvent, icao_codes: str):
        """查询指定机场的TAF报文"""
        codes = icao_codes.replace("，", ",").replace(",", " ").split()
        if result := await self.weather.taf(codes):
            msg = ""
            for taf in result:
                msg += taf["icaoId"] + "(" + taf["name"] + ")\n"
                msg += taf["rawTAF"] + "\n\n"
            return event.plain_result(msg.strip())
        return event.plain_result("TAF信息获取失败")
