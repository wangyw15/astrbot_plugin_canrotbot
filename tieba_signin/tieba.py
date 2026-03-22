import asyncio
import json
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Literal, TypedDict

from httpx import AsyncClient
from jinja2 import Template

from astrbot.core.utils.astrbot_path import get_astrbot_data_path


class BaiduAccount(TypedDict):
    owner: str
    name: str
    bduss: str
    stoken: str


class ForumResultCode(Enum):
    """
    贴吧签到结果类型
    """

    SUCCESS = 0
    ALREADY_SIGNED = 1
    ERROR = 2


class ForumResult(TypedDict):
    code: int
    name: str
    days: int
    rank: int
    description: str


class SigninResult(TypedDict):
    owner: str
    name: str
    time: str
    forums: list[ForumResult]


class SigninStatistic(TypedDict):
    name: str
    forums: list[str]
    success: list[str]
    fail: list[str]


class AccountManager:
    def __init__(self, plugin_name: str = "tieba_signin") -> None:
        self.data_path = Path(get_astrbot_data_path()) / "plugin_data" / plugin_name
        if not self.data_path.exists():
            self.data_path.mkdir(parents=True)

        self.account_file = self.data_path / "accounts.jsonl"
        if not self.account_file.exists():
            self.account_file.touch()

    def add_account(self, owner: str, name: str, bduss: str, stoken: str) -> None:
        """
        添加百度账号

        Args:
            name: 账号名称
            owner: 用户ID
            bduss: BDUSS
            stoken: STOKEN
        """
        account: BaiduAccount = {
            "owner": owner,
            "name": name,
            "bduss": bduss,
            "stoken": stoken,
        }
        with self.account_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(account, ensure_ascii=False) + "\n")

    def delete_account(self, owner: str, name: str) -> bool:
        """
        删除百度账号

        Args:
            owner: 用户ID
            name: 账号名称

        Return:
            删除是否成功，不存在时返回False
        """
        with self.account_file.open("r", encoding="utf-8") as f:
            account_lines = f.readlines()

        delete_index = -1
        for i, line in enumerate(account_lines):
            account: BaiduAccount = json.loads(line)
            if account["owner"] == owner and account["name"] == name:
                delete_index = i
                break

        if delete_index == -1:
            return False

        account_lines.pop(i)

        with self.account_file.open("w", encoding="utf-8") as f:
            for line in account_lines:
                f.write(line + "\n")
        return True

    def delete_all_accounts(self, owner: str) -> None:
        """
        删除所有百度账号

        Args:
            owner: 用户ID
        """
        with self.account_file.open("r", encoding="utf-8") as f:
            account_lines = f.readlines()

        delete_indexes: list[int] = []
        for i, line in enumerate(account_lines):
            account: BaiduAccount = json.loads(line)
            if account["owner"] == owner:
                delete_indexes.append(i)

        if not delete_indexes:
            return

        delete_indexes.reverse()
        for i in delete_indexes:
            account_lines.pop(i)

        with self.account_file.open("w", encoding="utf-8") as f:
            for line in account_lines:
                f.write(line + "\n")

    def get_account(self, owner: str, name: str) -> BaiduAccount | None:
        """
        获取百度账号

        Args:
            owner: 用户ID
            name: 账号名称

        Return:
            百度账号
        """
        with self.account_file.open("r", encoding="utf-8") as f:
            while line := f.readline():
                account: BaiduAccount = json.loads(line)
                if account["owner"] == owner and account["name"] == name:
                    return account

        return None

    def get_all_accounts(self) -> list[BaiduAccount]:
        """
        获取所有百度账号

        Return:
            百度账号
        """
        accounts: list[BaiduAccount] = []
        with self.account_file.open("r", encoding="utf-8") as f:
            while line := f.readline():
                if line:
                    accounts.append(json.loads(line))

        return accounts

    def get_all_owned_accounts(self, owner: str) -> list[BaiduAccount]:
        """
        获取所有百度账号

        Args:
            owner: 用户ID

        Return:
            百度账号
        """
        accounts: list[BaiduAccount] = []
        with self.account_file.open("r", encoding="utf-8") as f:
            while line := f.readline():
                account: BaiduAccount = json.loads(line)
                if account["owner"] == owner:
                    accounts.append(account)

        return accounts


class ResultManager:
    def __init__(self, plugin_name: str = "tieba_signin") -> None:
        self.plugin_path = Path(__file__).parent
        self.data_path = Path(get_astrbot_data_path()) / "plugin_data" / plugin_name
        if not self.data_path.exists():
            self.data_path.mkdir(parents=True)

        self.result_file = self.data_path / "results.jsonl"
        if not self.result_file.exists():
            self.result_file.touch()

        self.markdown_template = self.plugin_path / "templates" / "markdown.jinja"
        self.plain_template = self.plugin_path / "templates" / "plain.jinja"

    def save_signin_result(
        self, owner: str, name: str, forum_results: list[ForumResult]
    ) -> None:
        """
        保存签到结果

        Args:
            owner: 用户ID
            name: 账号名称
            result: 签到结果
        """
        data: SigninResult = {
            "owner": owner,
            "name": name,
            "time": datetime.now().isoformat(),
            "forums": forum_results,
        }
        with self.result_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    def get_today_result(self, owner: str, name: str = "") -> list[SigninResult]:
        """
        获取给定用户今日所有签到结果

        Args:
            owner: 用户ID
            name: 账号名称，不传入则默认获取所有账户的内容

        Returns:
            签到结果
        """
        result: list[SigninResult] = []
        with self.result_file.open("r", encoding="utf-8") as f:
            while line := f.readline():
                data: SigninResult = json.loads(line)
                if (
                    data["owner"] == owner
                    and datetime.fromisoformat(data["time"]).date()
                    == datetime.now().date()
                ):
                    if name == "" or name == data["name"]:
                        result.append(data)

        return result

    def get_today_all_result(self) -> dict[str, list[SigninResult]]:
        """
        获取今日所有签到结果

        Returns:
            签到结果
        """
        result: dict[str, list[SigninResult]] = {}
        with self.result_file.open("r", encoding="utf-8") as f:
            while line := f.readline():
                data: SigninResult = json.loads(line)
                if datetime.fromisoformat(data["time"]).date() == datetime.now().date():
                    if data["owner"] not in result:
                        result[data["owner"]] = []
                    result[data["owner"]].append(data)

        return result

    def generate_result_response(
        self,
        results: list[SigninResult],
        format: Literal["plain", "markdown"] = "markdown",
    ) -> str:
        """
        生成文本结果

        :param results: 签到结果

        :return: 文本结果
        """
        statistics: list[SigninStatistic] = []

        for result in results:
            statistics.append(
                {
                    "name": result["name"],
                    "forums": [x["name"] for x in result["forums"]],
                    "success": [
                        x["name"]
                        for x in result["forums"]
                        if x["code"] == ForumResultCode.SUCCESS
                        or x["code"] == ForumResultCode.ALREADY_SIGNED
                    ],
                    "fail": [
                        x["name"]
                        for x in result["forums"]
                        if x["code"] == ForumResultCode.ERROR
                    ],
                }
            )

        if format == "markdown":
            template: Template = Template(self.markdown_template.read_text("utf-8"))
        else:
            template: Template = Template(self.plain_template.read_text("utf-8"))
        return template.render(results=statistics)


class TiebaSignin:
    def __init__(self, plugin_name: str = "tieba_signin") -> None:
        self.result_manager = ResultManager(plugin_name)

    async def signin(self, account: BaiduAccount):
        """
        自动签到

        Args:
            account: 百度账号

        Return:
            签到结果
        """
        result: list[ForumResult] = []

        like_url = "https://tieba.baidu.com/mo/q/newmoindex"
        sign_url = "http://tieba.baidu.com/sign/add"

        client = AsyncClient()
        client.cookies.set("BDUSS", account["bduss"])
        client.cookies.set("STOKEN", account["stoken"])

        # 获取贴吧列表
        resp = await client.get(like_url)
        if not resp.is_success or resp.status_code != 200 or resp.json()["no"] != 0:
            raise Exception("获取贴吧列表失败", resp.json())

        forum_info: dict[str, Any] = resp.json()

        # 签到
        for forum in forum_info["data"]["like_forum"]:
            if forum["is_sign"] == 0:
                await asyncio.sleep(0.5)
                data = {
                    "ie": "utf-8",
                    "kw": forum["forum_name"],
                    "tbs": forum_info["data"]["tbs"],
                }
                resp = await client.post(sign_url, data=data)
                if not resp.is_success or resp.status_code != 200:
                    raise Exception("签到失败", resp.json())

                signin_result: dict[str, Any] = resp.json()
                if signin_result["no"] == 0:
                    result.append(
                        {
                            "code": ForumResultCode.SUCCESS.value,
                            "name": forum["forum_name"],
                            "days": signin_result["data"]["uinfo"]["total_sign_num"],
                            "rank": signin_result["data"]["uinfo"]["user_sign_rank"],
                            "description": "",
                        }
                    )
                else:
                    result.append(
                        {
                            "code": ForumResultCode.ERROR.value,
                            "name": forum["forum_name"],
                            "days": -1,
                            "rank": -1,
                            "description": json.dumps(
                                signin_result, ensure_ascii=False
                            ),
                        }
                    )
            else:
                result.append(
                    {
                        "code": ForumResultCode.ALREADY_SIGNED.value,
                        "name": forum["forum_name"],
                        "days": -1,
                        "rank": -1,
                        "description": "",
                    }
                )

        self.result_manager.save_signin_result(
            account["owner"], account["name"], result
        )
