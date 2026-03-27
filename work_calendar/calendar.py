import ast
from datetime import datetime, timedelta
from typing import NamedTuple

import icalendar

from astrbot.api.star import Star


class CyclePeriod(NamedTuple):
    name: str
    start: datetime
    end: datetime


T_Cycles = list[CyclePeriod | None]
T_RawCycles = list[tuple[str, str, str] | list[str] | None]


class WorkCalendar:
    def __init__(self, plugin: Star) -> None:
        self.plugin = plugin

    def parse_time(self, time_str: str):
        time_format = [
            "%H:%M",
            "%H%M",
        ]

        for i in time_format:
            try:
                return datetime.strptime(time_str, i)
            except ValueError:
                continue

    def parse_date(self, date_str: str) -> datetime | None:
        date_format = [
            "%Y/%m/%d",
            "%Y-%m-%d",
            "%Y.%m.%d",
            "%Y%m%d",
        ]

        for i in date_format:
            try:
                return datetime.strptime(date_str, i)
            except ValueError:
                continue

    def parse_cycles(self, raw_cycles: T_RawCycles) -> T_Cycles:
        cycles: T_Cycles = []

        for i in raw_cycles:
            if i is None:
                cycles.append(None)
            else:
                name, start_str, end_str = i

                start_time = self.parse_time(start_str)
                end_time = self.parse_time(end_str)

                if start_time is None:
                    raise ValueError(f"Cannot parse start time: {start_str}")
                if end_time is None:
                    raise ValueError(f"Cannot parse end time: {end_str}")

                cycles.append(
                    CyclePeriod(
                        name,
                        start_time,
                        end_time,
                    )
                )

        return cycles

    def parse_str(self, cycle_str: str) -> T_Cycles:
        raw_cycles: T_RawCycles = ast.literal_eval(cycle_str)
        parsed_cycles = self.parse_cycles(raw_cycles)
        return parsed_cycles

    def generate_calendar(
        self, cycles: T_Cycles, start_date: datetime, end_date: datetime
    ) -> icalendar.Calendar:
        cal = icalendar.Calendar()

        current_date = start_date
        while current_date <= end_date:
            current_period = cycles[(current_date - start_date).days % len(cycles)]
            if current_period is not None:
                name = current_period.name
                start_time = current_period.start
                end_time = current_period.end

                if start_time < end_time:
                    start_time = datetime(
                        current_date.year,
                        current_date.month,
                        current_date.day,
                        start_time.hour,
                        start_time.minute,
                    )
                    end_time = datetime(
                        current_date.year,
                        current_date.month,
                        current_date.day,
                        end_time.hour,
                        end_time.minute,
                    )
                else:
                    start_time = datetime(
                        current_date.year,
                        current_date.month,
                        current_date.day,
                        start_time.hour,
                        start_time.minute,
                    )
                    next_day = current_date + timedelta(days=1)
                    end_time = datetime(
                        next_day.year,
                        next_day.month,
                        next_day.day,
                        end_time.hour,
                        end_time.minute,
                    )

                event = icalendar.Event()
                event.start = start_time
                event.end = end_time
                event.add("summary", name)

                cal.add_component(event)

            # bump date and cycle
            current_date += timedelta(days=1)

        return cal
