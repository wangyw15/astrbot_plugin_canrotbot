import re

from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .dice import Dice


class DicePlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def dice_regex_handler(self, event: AstrMessageEvent):
        """识别到d20、2d10等骰子指令自动触发"""
        dice_match = re.fullmatch(Dice.PATTERN, event.message_str)
        if dice_match is None:
            return

        return event.plain_result(f"{dice_match[0]} = {Dice.eval(dice_match[0])}")

    @filter.llm_tool("dice")
    async def dice_tool(self, event: AstrMessageEvent, expr: str):
        """
        计算并返回例如1d10、2d6、d100等骰子表达式，返回值为所有骰子的总和。xdy代表扔x个y面骰子，例如2d6为扔两个6面骰子。

        Args:
            expr(string): 骰子表达式，例如1d10、2d6、d100
        """
        dice_match = re.fullmatch(Dice.PATTERN, expr)
        if dice_match is None:
            return "无效的骰子表达式"

        return str(Dice.eval(dice_match[0]))
