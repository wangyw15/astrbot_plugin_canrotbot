from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, MessageChain, filter
from astrbot.api.star import Context, Star
from astrbot.core.db import CronJob

from .tieba import AccountManager, BaiduAccount, ResultManager, TiebaSignin


class TiebaSigninPlugin(Star):
    SIGNIN_JOB_NAME = "tieba_signin"

    def __init__(self, context: Context):
        super().__init__(context)
        self.context = context

        self.account_manager = AccountManager(self.name)
        self.result_manager = ResultManager(self.name)
        self.tieba_signin = TiebaSignin(self.name)

        self.signin_job: CronJob | None = None

    async def clear_signin_jobs(self):
        if self.signin_job is not None:
            await self.context.cron_manager.delete_job(self.signin_job.job_id)

        for job in await self.context.cron_manager.list_jobs():
            if job.name == self.SIGNIN_JOB_NAME:
                await self.context.cron_manager.delete_job(job.job_id)

    async def initialize(self):
        await self.clear_signin_jobs()

        self.signin_job = await self.context.cron_manager.add_basic_job(
            name=self.SIGNIN_JOB_NAME,
            cron_expression="0 0 * * *",
            handler=self.tieba_auto_signin,
            description="贴吧自动签到",
            persistent=True,
        )

    async def terminate(self):
        await self.clear_signin_jobs()

    @filter.command_group("tieba")
    async def tieba_command_group():
        """tieba 命令组"""
        pass

    @tieba_command_group.command("add")
    async def tieba_add_account_command(
        self, event: AstrMessageEvent, name: str, bduss: str, stoken: str
    ):
        """添加百度账号"""
        self.account_manager.add_account(event.unified_msg_origin, name, bduss, stoken)
        return event.plain_result(f"{name} 已添加")

    @tieba_command_group.command("delete")
    async def tieba_delete_account_command(self, event: AstrMessageEvent, name: str):
        """删除百度账号"""
        result = self.account_manager.delete_account(event.unified_msg_origin, name)
        if result:
            return event.plain_result(f"{name} 已删除")
        return event.plain_result(f"{name} 不存在")

    @tieba_command_group.command("deleteall")
    async def tieba_delete_all_accounts_command(self, event: AstrMessageEvent):
        """删除所有百度账号"""
        self.account_manager.delete_all_accounts(event.unified_msg_origin)
        return event.plain_result("所有账号已删除")

    @tieba_command_group.command("list")
    async def tieba_list_accounts_command(self, event: AstrMessageEvent):
        """列出所有百度账号"""
        accounts = self.account_manager.get_all_owned_accounts(event.unified_msg_origin)
        if not accounts:
            return event.plain_result("没有添加任何账号")
        account_list = "\n".join([f"- {account['name']}" for account in accounts])
        return event.plain_result(f"已添加的账号：\n{account_list}")

    @tieba_command_group.command("signin")
    async def tieba_signin_command(self, event: AstrMessageEvent, name: str = ""):
        """签到指定账号，不提供name则签到所有账号"""
        user_id = event.unified_msg_origin
        accounts: list[BaiduAccount] = []

        if name:
            account = self.account_manager.get_account(user_id, name)
            if account is None:
                yield event.plain_result(f"账号 {name} 不存在")
                return

            accounts.append(account)
        else:
            accounts = self.account_manager.get_all_owned_accounts(user_id)
            if not accounts:
                yield event.plain_result("还未添加任何账号")
                return

        yield event.plain_result("正在签到中")

        for account in accounts:
            await self.tieba_signin.signin(account)

        results = self.result_manager.get_today_result(user_id)
        if not results:
            yield event.plain_result("签到完成，但无法获取结果")
            return

        message = self.result_manager.generate_result_response(
            results, format="markdown"
        )
        yield event.plain_result(message)

    @tieba_command_group.command("result")
    async def tieba_result_command(self, event: AstrMessageEvent, name: str = ""):
        """查看最新签到结果，不提供name则查看所有账号的今日结果"""
        user_id = event.unified_msg_origin

        results = self.result_manager.get_today_result(user_id, name)
        if not results:
            return event.plain_result("今天还没有签到记录")

        message = self.result_manager.generate_result_response(
            results, format="markdown"
        )
        return event.plain_result(message)

    async def tieba_auto_signin(self):
        logger.info("开始贴吧自动签到")
        accounts = self.account_manager.get_all_accounts()
        for account in accounts:
            await self.tieba_signin.signin(account)

        results = self.result_manager.get_today_all_result()
        for owner, results in results.items():
            await self.context.send_message(
                owner,
                MessageChain().message(
                    self.result_manager.generate_result_response(results)
                ),
            )
            logger.info(f"已向 {owner} 推送签到结果")
