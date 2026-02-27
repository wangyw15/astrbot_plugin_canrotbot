import re

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .qalculate import Qalculate


class QalculatePlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)

        self.config = config
        self.qalc = None

        if "qalculate_bin" in config:
            self.qalc = Qalculate(config["qalculate_bin"])
            if self.qalc.check_qalculate():
                logger.info("检测到qalculate")
            else:
                self.qalc = None

    def calculate(self, expression: str) -> str:
        if re.fullmatch(r"^([\d()\-+*/.]+)=?$", expression):
            return "{}={:g}".format(expression, eval(expression.rstrip("=")))

        if self.qalc is not None:
            return self.qalc.calculate(expression)

        return ""

    @filter.llm_tool("calculate")
    async def calculate_tool(self, event: AstrMessageEvent, expression: str):
        """
        计算给定的数学表达式，会根据给定的表达式判断计算工具。
        若仅包含四则运算与括号，则会使用eval进行计算。
        其余情况会调用qalculate进行计算：
        支持所有常见运算符 — 算术、逻辑、位运算、元素级运算、(不)等式
        表达式可以包含数字、常数、函数、单位、变量、矩阵、向量和时间/日期的任意组合

        Args:
            expression(string): 表达式

        Return:
            表达式与计算结果
        """
        return self.calculate(expression) or "不支持计算当前表达式"

    @filter.command("calc")
    async def calculate_command(self, event: AstrMessageEvent, expression: str):
        """计算器"""
        expression = expression.strip().rstrip("=")
        return event.plain_result(self.calculate(expression) or "不支持计算当前表达式")

    @filter.event_message_type(filter.EventMessageType.ALL)
    async def calculate_regex(self, event: AstrMessageEvent):
        """根据正则自动触发计算，如1+1="""
        pattern = re.compile(r"^([\d()\-+*/.]+)=$")

        if match := re.fullmatch(pattern, event.message_str):
            if result := self.calculate(match[1]):
                return event.plain_result(result)
