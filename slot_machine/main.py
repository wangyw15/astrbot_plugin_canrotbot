from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .slot_machine import SlotMachine


class SlotMachinePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.slot_machine = SlotMachine()

    @filter.command("slot")
    async def slot_machine_command(self, event: AstrMessageEvent):
        """转一次老虎机"""
        self.slot_machine.spin()
        self.slot_machine.calculate_score()
        return event.plain_result(self.slot_machine.generate_result())

    @filter.llm_tool("slot_machine")
    async def slot_machine_tool(self, event: AstrMessageEvent):
        """转一次5*3的老虎机，返回内容包括老虎机的结果、总得分与详细得分"""
        self.slot_machine.spin()
        self.slot_machine.calculate_score()
        return self.slot_machine.generate_result()
