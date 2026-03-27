from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core import astrbot_config

from .idolypride import IdolyPride


class MyPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.ip = IdolyPride(astrbot_config.get("http_proxy", ""))

    @filter.command_group("idolypride")
    async def idolypride_group(self, event: AstrMessageEvent):
        """IDOLY PRIDE 指令组"""
        pass

    @idolypride_group.command("calendar")
    async def calendar_command(self, event: AstrMessageEvent):
        """查看偶像荣耀活动日历"""
        msg = await self.ip.calendar_message()
        if msg:
            yield event.plain_result(msg)
        else:
            yield event.plain_result("今天没有活动~")

    @filter.llm_tool("idolypride_calendar")
    async def idolypride_calendar_tool(self, event: AstrMessageEvent):
        """查询偶像荣耀(IDOLY PRIDE)当前正在进行的活动信息"""
        msg = await self.ip.calendar_message(True)
        if msg:
            return msg
        return "当前没有正在进行的活动"
