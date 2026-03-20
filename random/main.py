import json

from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .random_select import RandomSelect


class RandomPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.random = RandomSelect()

    @filter.command("random")
    async def random_command(self, event: AstrMessageEvent, items: str):
        """随机选择命令"""
        result = self.random(items)
        return event.plain_result("选择了：" + " ".join(result))

    @filter.command("coin")
    async def coin_command(self, event: AstrMessageEvent):
        """抛硬币"""
        return event.plain_result(self.random("正面,反面")[0])

    @filter.llm_tool("random_select")
    async def random_select_tool(self, items: str) -> str:
        """
        随机从每个列表中选择一个项目。
        同一列表中的项目用逗号分隔；不同列表用分号分隔。

        Args:
            items(string): 包含多个列表的字符串。同一列表中的项目用逗号分隔，列表之间用分号分隔。

        Returns:
            以JSON格式返回选中的项目
        """
        return json.dumps({"selected": self.random(items)}, ensure_ascii=False)
