from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .kuji import Kuji


class KujiPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.kuji = Kuji()

    @filter.llm_tool("kuji_random")
    async def random_kuji(self, event: AstrMessageEvent) -> str:
        """
        从日本浅草寺的签文中获取一个随机的御神签，以测试运气。
        """
        return self.kuji.generate_text(self.kuji.get_kuji())

    @filter.command("kuji")
    async def kuji_command(self, event: AstrMessageEvent):
        """从日本浅草寺的签文中获取一个随机的御神签"""
        kuji = self.kuji.get_kuji()
        # TODO: 本地的HTML渲染
        # return event.image_result(
        #     await self.kuji.generate_image(self.html_render, kuji)
        # )
        return event.plain_result(self.kuji.generate_text(kuji))
