import json

from astrbot.api.event import AstrMessageEvent, MessageChain, filter
from astrbot.api.star import Context, Star
from astrbot.core.db import CronJob
from astrbot.core.star.filter.command import GreedyStr

from .rss import Rss, RssSubscription


class RssPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)
        self.context = context
        self.rss = Rss()
        self.update_jobs: list[CronJob] = []

    async def initialize(self):
        for subscription in self.rss.list_all_subscriptions():
            await self.add_update_job(subscription)

    async def terminate(self):
        while self.update_jobs:
            job = self.update_jobs.pop()
            await self.context.cron_manager.delete_job(job.job_id)

    @filter.command_group("rss")
    async def rss_command_group():
        """rss 命令组"""
        pass

    @rss_command_group.command("add")
    async def rss_add_command(
        self, event: AstrMessageEvent, name: str, url: str, cron: GreedyStr
    ):
        """添加RSS订阅，cron表达式默认值为0 * * * *，填入no则不会自动更新"""
        umo = event.unified_msg_origin

        if cron == "no":
            cron_str = None
        else:
            cron_str = str(cron or "0 * * * *")

        if not self.rss.validate_url(url):
            return event.plain_result("❌ URL 格式错误")

        if subscription := self.rss.add_subscription(name, umo, url, cron_str):
            await self.add_update_job(subscription)
            msg = f"✅ 已成功添加订阅 '{name}'\n📍 URL: {url}\n⏰ "
            if cron_str is None:
                msg += "不自动检查更新"
            else:
                msg += f"Cron表达式: {cron_str}"
            return event.plain_result(msg)

        return event.plain_result(f"❌ 订阅 '{name}' 已存在，请使用其他名称")

    @rss_command_group.command("del")
    async def rss_del_command(self, event: AstrMessageEvent, name: str):
        """删除RSS订阅"""
        umo = event.unified_msg_origin

        if sub := self.rss.get_subscription(name, umo):
            await self.delete_update_job(sub)
            self.rss.delete_subscription(name, umo)
            return event.plain_result(f"✅ 已成功删除订阅 '{name}'")

        return event.plain_result(f"❌ 未找到订阅 '{name}'")

    @rss_command_group.command("list")
    async def rss_list_command(self, event: AstrMessageEvent):
        """列出当前会话的所有订阅"""
        umo = event.unified_msg_origin
        subscriptions = self.rss.list_subscriptions(umo)

        if not subscriptions:
            return event.plain_result("📭 当前没有订阅任何RSS源")

        result = ["📰 当前订阅列表："]
        for sub in subscriptions:
            result.append(f"\n• {sub['name']}")
            result.append(f"  URL: {sub['url']}")
            result.append(f"  Cron表达式: {sub['cron']}")

        return event.plain_result("\n".join(result))

    @rss_command_group.command("update")
    async def rss_update_command(
        self,
        event: AstrMessageEvent,
        name: str,
        force: bool = False,
        max_display: int = 10,
    ):
        """手动检查订阅更新"""
        umo = event.unified_msg_origin
        subscription = self.rss.get_subscription(name, umo)

        if not subscription:
            yield event.plain_result(f"❌ 未找到订阅 '{name}'")
            return

        yield event.plain_result(f"🔍 正在检查 '{name}' 的更新...")

        entries = await self.rss.update_rss(
            subscription["umo"], subscription["url"], force
        )

        # 使用Jinja模板格式化结果
        result_text = self.rss.generate_update_result(name, entries, max_display)
        yield event.plain_result(result_text)

    async def add_update_job(self, subscription: RssSubscription):
        if subscription["cron"] is None:
            return

        self.update_jobs.append(
            await self.context.cron_manager.add_basic_job(
                name=f"rss_{subscription['umo']}_{subscription['name']}",
                cron_expression=subscription["cron"],
                handler=self.get_update_job_handler(subscription),
                description=f"RSS 自动更新 {subscription['umo']} {subscription['name']}",
                persistent=True,
            )
        )

    def get_update_job_handler(self, subscription: RssSubscription):
        async def _update_handler():
            entries = await self.rss.update_rss(
                subscription["umo"], subscription["url"]
            )
            if not entries:
                return

            msg = self.rss.generate_update_result(subscription["name"], entries, 10)
            await self.context.send_message(
                subscription["umo"], MessageChain().message(msg)
            )

        return _update_handler

    async def delete_update_job(self, subscription: RssSubscription) -> bool:
        job_name = f"rss_{subscription['umo']}_{subscription['name']}"
        update_job: CronJob | None = None

        for job in self.update_jobs:
            if job.name == job_name:
                update_job = job

        if update_job is not None:
            self.update_jobs.remove(update_job)
            await self.context.cron_manager.delete_job(update_job.job_id)
            return True

        return False

    # LLM工具
    @filter.llm_tool("rss_list_subscription")
    async def rss_list_tool(self, event: AstrMessageEvent):
        """
        列出用户所有的RSS订阅
        """
        umo = event.unified_msg_origin
        subscriptions = self.rss.list_subscriptions(umo)

        if not subscriptions:
            return "当前没有订阅任何RSS源"

        result = ["当前订阅列表："]
        for sub in subscriptions:
            result.append(f"\n- {sub['name']}")
            result.append(f"- URL: {sub['url']}")
            result.append(f"- 检查间隔: {sub['cron']}")

        return "\n".join(result)

    @filter.llm_tool("rss_add_subscription")
    async def rss_add_tool(
        self, event: AstrMessageEvent, name: str, url: str, cron: str = "0 * * * *"
    ):
        """
        添加RSS订阅，自动更新是通过RSS插件本身的机制检查更新并推送，不会经过AI总结

        Args:
            name(string): 订阅名称
            url(string): RSS订阅地址
            cron(string): Cron表达式，默认为每小时检查一次（0 * * * *），填入空值则不自动检查更新
        """
        umo = event.unified_msg_origin

        if not self.rss.validate_url(url):
            return event.plain_result("URL 格式错误")

        if subscription := self.rss.add_subscription(name, umo, url, cron or None):
            await self.add_update_job(subscription)
            result = f"已成功添加订阅 '{name}'\nURL: {url}\n"
            if cron:
                result += f"Cron表达式: {cron}"
            else:
                result += "不自动检查更新"
            return result

        return f"订阅 '{name}' 已存在，请使用其他名称"

    @filter.llm_tool("rss_delete_subscription")
    async def rss_del_tool(self, event: AstrMessageEvent, name: str):
        """
        删除RSS订阅

        Args:
            name(string): 订阅名称
        """
        umo = event.unified_msg_origin

        if sub := self.rss.get_subscription(name, umo):
            await self.delete_update_job(sub)
            self.rss.delete_subscription(name, umo)
            return f"已成功删除订阅 '{name}'"

        return f"未找到订阅 '{name}'"

    @filter.llm_tool("rss_update_subscription")
    async def rss_update_tool(
        self,
        event: AstrMessageEvent,
        name: str,
        include_description: bool = False,
        force: bool = False,
        max_display: int = 10,
    ):
        """
        手动检查RSS订阅更新

        Args:
            name(string): 订阅名称
            include_description(boolean): 是否包含条目详细内容，默认为False
            force(boolean): 是否强制更新，默认为False
            max_display(number): 最多显示多少条更新，默认为10，-1则返回显示所有
        """
        umo = event.unified_msg_origin
        subscription = self.rss.get_subscription(name, umo)

        if not subscription:
            return f"未找到订阅 '{name}'"

        entries = await self.rss.update_rss(
            subscription["umo"], subscription["url"], force
        )

        # 将entries转换为JSON格式返回
        entries_data = []
        for entry in entries:
            entry_dict = {
                "title": entry["title"],
                "link": entry["link"],
                "description": entry["description"] if include_description else "",
                "published": entry["published"].isoformat(),
                "guid": entry["guid"],
            }
            entries_data.append(entry_dict)

        result = {
            "subscription_name": name,
            "total_count": len(entries_data),
            "entries": entries_data[:max_display] if max_display >= 0 else entries_data,
        }

        return json.dumps(result, ensure_ascii=False)
