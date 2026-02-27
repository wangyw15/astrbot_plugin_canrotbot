import json
import random

from httpx import AsyncClient

from astrbot.api import logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star

RESOURCE_URL = (
    "https://raw.githubusercontent.com/hitokoto-osc/sentences-bundle/master/{}"
)


class HitokotoPlugin(Star):
    def __init__(self, context: Context):
        super().__init__(context)

        self.version: dict[str, str | dict] = {}
        self.categories: list[dict] = []
        self.sentences: dict[str, list[dict]] = {}
        self.all_category_keys = ""

    async def initialize(self):
        async with AsyncClient() as client:
            # 加载 version.json
            if not self.version:
                resp = await client.get(RESOURCE_URL.format("version.json"))
                if resp.is_success:
                    self.version = resp.json()
                    logger.info(
                        f"hitokoto sentences_bundle version: {self.version['bundle_version']}"
                    )

            # 加载 categories.json
            if not self.categories:
                resp = await client.get(RESOURCE_URL.format("categories.json"))
                if resp.is_success:
                    self.categories = resp.json()
                    logger.info(
                        f"hitokoto sentences_bundle categories count: {len(self.categories)}"
                    )

            # 加载 sentences
            if not self.sentences:
                for category in self.categories:
                    self.all_category_keys += category["key"]

                    resp = await client.get(RESOURCE_URL.format(category["path"][2:]))
                    if resp.is_success:
                        self.sentences[category["key"]] = resp.json()
                        logger.info(
                            f"hitokoto sentences_bundle {category['name']} sentences count: {len(self.sentences[category['key']])}"
                        )

    def random_hitokoto(self, selected_categories: str = ""):
        if not self.sentences or not self.all_category_keys:
            return None

        if not selected_categories:
            selected_categories = self.all_category_keys

        selected_sentences = []
        for key in selected_categories:
            if key in self.all_category_keys:
                selected_sentences.extend(self.sentences[key])

        return random.choice(selected_sentences)

    def get_hitokoto_by_uuid(self, uuid: str):
        if not self.categories or not self.sentences:
            return None

        for category in self.categories:
            for sentence in self.sentences[category["key"]]:
                if sentence["uuid"] == uuid:
                    return sentence
        return None

    @filter.llm_tool("hitokoto_random_one")
    async def random_hitokoto_tool(
        self, event: AstrMessageEvent, selected_categories: str = ""
    ):
        """
        随机生成一条一言内容

        Args:
            selected_categories(string): a: 动画, b: 漫画, c: 游戏, d: 文学, e: 原创, f: 来自网络, g: 其他, h: 影视, i: 诗词, j: 网易云, k: 哲学, l: 抖机灵, 为空则为所有种类

        Returns:
            一言信息，失败则返回None
        """
        return json.dumps(self.random_hitokoto(selected_categories), ensure_ascii=False)

    @filter.llm_tool("hitokoto_get_by_uuid")
    async def get_hitokoto_by_uuid_tool(self, event: AstrMessageEvent, uuid: str):
        """
        根据给定uuid获取对应的一言信息

        Args:
            uuid(string): 一言的uuid

        Returns:
            一言信息，失败则返回None
        """
        if ret := self.get_hitokoto_by_uuid(uuid):
            return json.dumps(ret, ensure_ascii=False)
        return None

    @filter.command("hitokoto")
    async def hitokoto(self, event: AstrMessageEvent, category: str = "abc"):
        """
        获取随机一言
        """
        if data := self.random_hitokoto(category):
            ret_msg = (
                f"{data['hitokoto']}\n"
                f"-- {'' if not data['from_who'] else data['from_who']}「{data['from']}」\n"
                f"https://hitokoto.cn/?uuid={data['uuid']}"
            )
            return event.plain_result(ret_msg)
        else:
            return event.plain_result("获取一言失败")
