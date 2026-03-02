from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

from .fortune import Fortune
from .history import HistoryManager
from .themes import manager


class SigninPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.fortune = Fortune()
        self.history = HistoryManager(self.name)

    async def initialize(self) -> None:
        self.fortune.load()

    @filter.command("signin")
    async def signin_command(self, event: AstrMessageEvent, theme: str = "random"):
        """每日签到"""
        uid = event.get_sender_id()
        if self.history.already_signin(uid):
            image_path = self.history.get_latest_image_path(uid)
            if image_path.exists():
                return event.image_result(str(image_path))
            else:
                today_record = self.history.get_today_record(uid)
                title = today_record["title"]
                content = today_record["content"]
                theme = today_record["theme"]
        else:
            title, content = self.fortune()

        theme_instance = manager.get_theme(theme)
        if theme_instance is None:
            return event.plain_result(f"签到主题 {theme} 不存在")

        html = await theme_instance.generate(title, content)
        image = await self.html_render(
            html,
            {},
            options={
                "type": "png",
                "clip": {
                    "x": 0,
                    "y": 0,
                    "width": 480,
                    "height": 480,
                },
            },
        )
        self.history.add_record(uid, title, content, theme_instance.name)
        await self.history.set_latest_image_url(uid, image)
        return event.image_result(image)

    @filter.llm_tool("signin_get_today_record")
    async def get_today_record_tool(self, event: AstrMessageEvent):
        """获取用户当前的签到运势内容。若当天没有签到过，则返回未签到"""
        if today_record := self.history.get_today_record(event.get_sender_id()):
            return today_record["title"] + "\n" + today_record["content"]
        return "用户今天还未签到过"

    @filter.llm_tool("signin")
    async def signin_tool(self, event: AstrMessageEvent):
        """
        每日签到

        每天第一次签到会提供新的运势，当天多次签到只会返回第一次签到的结果
        """
        yield await self.signin_command(event)

        if today_record := self.history.get_today_record(event.get_sender_id()):
            yield today_record["title"] + "\n" + today_record["content"]
