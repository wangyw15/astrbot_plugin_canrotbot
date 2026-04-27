from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .slot_machine import ScoreManager, SlotMachine


class SlotMachinePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.slot_machine = SlotMachine()
        self.score_manager = ScoreManager()

    def _spin(self, uid: str) -> str:
        record = self.score_manager.get_record(uid)
        self.slot_machine.spin(record["current_zero_streak"])
        self.slot_machine.calculate_score()

        self.score_manager.add_spin(
            uid,
            self.slot_machine.grid,
            self.slot_machine.total_score,
            self.slot_machine.score_details,
        )
        return self.slot_machine.generate_result()

    @filter.command("slot")
    async def slot_machine_command(self, event: AstrMessageEvent, spin_count: int = 1):
        """转老虎机，可指定次数"""
        uid = event.get_sender_id()
        if spin_count <= 1:
            return event.plain_result(self._spin(uid))

        results = [self._spin(uid) for _ in range(spin_count)]
        sep = "\n" + "-" * 10 + "\n"
        return event.plain_result(sep.join(results))

    @filter.command("slot_record")
    async def slot_machine_record_record_command(self, event: AstrMessageEvent):
        """查看老虎机记录"""
        uid = event.get_sender_id()
        return event.plain_result(self.score_manager.get_record_text(uid))

    @filter.llm_tool("slot_machine")
    async def slot_machine_tool(self, event: AstrMessageEvent):
        """转一次5*3的老虎机，返回内容包括老虎机的结果、总得分与详细得分"""
        uid = event.get_sender_id()
        return self._spin(uid)

    @filter.llm_tool("slot_machine_record")
    async def slot_machine_record_tool(self, event: AstrMessageEvent):
        """查看用户的老虎机历史记录，返回总得分、总次数和最佳记录"""
        uid = event.get_sender_id()
        return self.score_manager.get_record_text(uid)
