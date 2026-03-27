from datetime import datetime
from pathlib import Path

import astrbot.api.message_components as Comp
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star
from astrbot.core.message.message_event_result import MessageEventResult
from astrbot.core.utils.astrbot_path import get_astrbot_data_path

from .calendar import WorkCalendar


class WorkCalendarPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.calendar = WorkCalendar(self)
        self.data_path = Path(get_astrbot_data_path()) / "plugin_data" / self.name
        if not self.data_path.exists():
            self.data_path.mkdir(parents=True)

    @filter.command_group("work_calendar")
    async def work_calendar_command_group(self):
        pass

    @work_calendar_command_group.command("generate")
    async def generate_calendar_command(
        self,
        event: AstrMessageEvent,
        calendar_cycle: str,
        calendar_start: str,
        calendar_end: str,
    ) -> MessageEventResult:
        """生成排班日历，示例：[("白班","08:00","20:00"),("夜班","20:00","08:00"),None,None] 20251001 20251231"""
        parsed_cycles = self.calendar.parse_str(calendar_cycle)
        start_date = self.calendar.parse_date(calendar_start)
        end_date = self.calendar.parse_date(calendar_end)

        if start_date is None:
            return event.plain_result(f"无法解析起始日期: {calendar_start}")
        if end_date is None:
            return event.plain_result(f"无法解析结束日期: {calendar_end}")

        filename = "work_calendar_"
        if user_name := event.get_sender_name():
            filename += user_name + "_"
        filename += datetime.now().strftime("%Y%m%dT%H%M%S") + ".ics"

        content = self.calendar.generate_calendar(
            parsed_cycles, start_date, end_date
        ).to_ical()

        file_path = self.data_path / filename
        with file_path.open("wb") as f:
            f.write(content)

        return event.chain_result([Comp.File(filename, file=str(file_path))])

    @filter.llm_tool("work_calendar_generate_ics")
    async def generate_calendar_tool(
        self,
        event: AstrMessageEvent,
        calendar_cycle: str,
        calendar_start: str,
        calendar_end: str,
    ):
        """
        生成排班日历并返回ICS文件。根据指定的班次周期和日期范围，生成一个排班日历文件（ICS格式），可用于导入到各类日历软件中。

        Args:
            calendar_cycle(string): 班次周期定义，格式为 Python 列表字符串，例如：`[("白班","08:00","20:00"),("夜班","20:00","08:00"),None,None]`。其中每个元组包含班次名称、开始时间、结束时间，None 表示休息。
            calendar_start(string): 日历开始日期，格式为 YYYYMMDD，例如：'20251001'。
            calendar_end(string): 日历结束日期，格式为 YYYYMMDD，例如：'20251231'。
        """
        return await self.generate_calendar_command(
            event, calendar_cycle, calendar_start, calendar_end
        )  # type: ignore

    @filter.llm_tool("work_calendar_get_weekday")
    async def get_weekday_tool(
        self,
        event: AstrMessageEvent,
        date: str,
    ) -> str:
        """获取指定日期是星期几。

        Args:
            date: 日期字符串，格式为 YYYYMMDD，例如：'20251001'。

        Returns:
            星期几的字符串表示，例如：'星期一'、'星期二'等，如果日期解析失败则返回错误信息。
        """
        parsed_date = self.calendar.parse_date(date)
        if parsed_date is None:
            return f"无法解析日期: {date}，请使用 YYYYMMDD 格式（如：20251001）"

        weekdays = [
            "星期一",
            "星期二",
            "星期三",
            "星期四",
            "星期五",
            "星期六",
            "星期日",
        ]
        weekday = parsed_date.weekday()
        return weekdays[weekday]
