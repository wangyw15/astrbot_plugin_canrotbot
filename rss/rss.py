import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TypedDict
from urllib.parse import urlparse

import feedparser
from httpx import AsyncClient
from jinja2 import Template

from astrbot.api import logger
from astrbot.api.star import Star
from astrbot.core.utils.astrbot_path import get_astrbot_data_path


class RssSubscription(TypedDict):
    name: str
    umo: str
    url: str
    cron: str | None


class RssUpdateInfo(TypedDict):
    etag: str
    last_modified: str
    last_updated: str


class RssItem(TypedDict):
    title: str
    link: str
    description: str
    published: datetime
    guid: str


class Rss:
    """RSS订阅管理器。

    管理RSS订阅的增删改查，以及获取更新内容。

    Attributes:
        client: HTTP异步客户端。
        plugin_path: 插件所在路径。
        data_path: 数据存储路径。
        subscription_file: 订阅信息存储文件。
        _cache_headers: URL对应的ETag和Last-Modified缓存。
    """

    def __init__(self, plugin: Star, proxy: str = "") -> None:
        """初始化RSS订阅管理器。

        Args:
            plugin_name: 插件名称，用于构建数据存储路径。
            proxy: HTTP代理地址，为空字符串时不使用代理。
        """
        self.plugin = plugin
        self.client = AsyncClient(proxy=proxy or None)

        self.plugin_path = Path(__file__).parent
        self.data_path = (
            Path(get_astrbot_data_path()) / "plugin_data" / self.plugin.name
        )
        if not self.data_path.exists():
            self.data_path.mkdir(parents=True)

        self.subscription_file = self.data_path / "subscription.jsonl"
        if not self.subscription_file.exists():
            self.subscription_file.touch()
        self.template_file = self.plugin_path / "template.jinja"

    async def _get_update_info(
        self, subscription: RssSubscription
    ) -> RssUpdateInfo | None:
        key = f"updateinfo_{subscription['umo']}_{subscription['url']}"
        data = await self.plugin.get_kv_data(key, None)
        if data is None:
            return None
        return json.loads(data)

    async def _set_update_info(
        self, subscription: RssSubscription, update_info: RssUpdateInfo
    ) -> None:
        key = f"updateinfo_{subscription['umo']}_{subscription['url']}"
        await self.plugin.put_kv_data(key, json.dumps(update_info, ensure_ascii=False))

    async def _delete_update_info(self, subscription: RssSubscription) -> None:
        key = f"updateinfo_{subscription['umo']}_{subscription['url']}"
        if (await self.plugin.get_kv_data(key, None)) is not None:
            await self.plugin.delete_kv_data(key)

    async def update_rss(
        self, subscription: RssSubscription, force: bool = False
    ) -> list[RssItem]:
        """获取RSS订阅在给定时间范围内的更新内容。

        使用ETag和Last-Modified进行缓存优化，只返回指定时间范围内的条目。

        Args:
            url: RSS订阅地址。
            interval: 回溯时间（分钟），默认60分钟。
            force: 是否忽略历史更新信息，强制获取最新内容。默认False。

        Returns:
            更新的条目列表，每个条目包含title, link, description, published。
        """
        headers: dict[str, str] = {}
        last_updated: datetime = datetime.fromtimestamp(0, timezone.utc)

        # 如果不忽略缓存，且存在更新信息，使用条件请求
        if not force:
            if update_info := await self._get_update_info(subscription):
                if etag := update_info["etag"]:
                    headers["If-None-Match"] = etag
                if last_modified := update_info["last_modified"]:
                    headers["If-Modified-Since"] = last_modified
                last_updated = datetime.fromisoformat(update_info["last_updated"])

        try:
            response = await self.client.get(
                subscription["url"], headers=headers, follow_redirects=True
            )

            # 304 Not Modified - 内容未更新
            if response.status_code == 304:
                return []

            response.raise_for_status()

            # 更新缓存headers
            await self._set_update_info(
                subscription,
                {
                    "etag": response.headers.get("etag", ""),
                    "last_modified": response.headers.get("last-modified", ""),
                    "last_updated": datetime.now(timezone.utc).isoformat(),
                },
            )

            # 解析RSS内容
            feed_data = feedparser.parse(response.text)

            # 过滤给定时间范围内的条目（考虑时区）
            # RSS时间通常是UTC，使用UTC进行比较
            new_entries: list[RssItem] = []

            for entry in feed_data.entries:
                # 获取发布时间（feedparser返回的是UTC时间元组）
                pub_time = None
                if "published_parsed" in entry:
                    pub_time = datetime(
                        *entry.published_parsed[:6],  # type: ignore
                        tzinfo=timezone.utc,
                    )
                if "updated_parsed" in entry:
                    pub_time = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)  # type: ignore

                # 如果在时间范围内，添加到结果
                if pub_time is not None and pub_time > last_updated:
                    # 返回本地时间格式，便于用户阅读
                    new_entries.append(
                        {
                            "title": entry.get("title", ""),  # type: ignore
                            "link": entry.get("link", ""),  # type: ignore
                            "description": entry.get("description", ""),  # type: ignore
                            "published": pub_time.astimezone(),  # type: ignore
                            "guid": entry.get("id", ""),  # type: ignore
                        }
                    )

            return new_entries

        except Exception as e:
            logger.error(f"更新RSS失败: {subscription['url']}, 错误: {e}")
            return []

    def generate_update_result(
        self, name: str, entries: list[RssItem], max_display: int = -1
    ) -> str:
        """格式化RSS检查结果为文本。

        使用Jinja模板渲染结果。

        Args:
            subscription_name: 订阅名称。
            entries: RSS条目列表。
            max_display: 最多显示的条目数，默认显示全部。

        Returns:
            格式化后的文本。
        """
        template: Template = Template(self.template_file.read_text("utf-8"))
        return template.render(
            name=name,
            entries=entries,
            max_display=len(entries) if max_display == -1 else max_display,
        )

    def add_subscription(
        self, name: str, umo: str, url: str, cron: str | None = "0 * * * *"
    ) -> RssSubscription | None:
        """添加RSS订阅。

        Args:
            name: 订阅名称，用于标识该订阅。
            umo: 订阅目标的UMO（Unified Message Origin）。
            url: RSS订阅地址。
            cron: 检查更新的间隔时间（分钟），默认60分钟；None则不自动更新

        Return:
            生成的订阅数据，若已存在同名订阅则返回None
        """
        if self.get_subscription(name, umo):
            return None

        sub: RssSubscription = {
            "name": name,
            "umo": umo,
            "url": url,
            "cron": cron,
        }
        with self.subscription_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(sub, ensure_ascii=False) + "\n")
        return sub

    async def delete_subscription(self, name: str, umo: str) -> bool:
        """删除RSS订阅。

        Args:
            name: 要删除的订阅名称。
            umo: 订阅目标的UMO，用于验证权限。

        Returns:
            删除成功返回True，未找到或不匹配返回False。
        """
        lines = []
        delete_index = -1

        with self.subscription_file.open("r", encoding="utf-8") as f:
            lines = f.readlines()

        # 查找匹配的订阅
        for i, line in enumerate(lines):
            if line.strip():
                data: RssSubscription = json.loads(line)
                if data["name"] == name and data["umo"] == umo:
                    delete_index = i
                    break

        # 未找到匹配的订阅
        if delete_index == -1:
            return False

        # 删除该行
        subscription = lines.pop(delete_index)

        # 写回文件
        with self.subscription_file.open("w", encoding="utf-8") as f:
            f.writelines(lines)

        # 删除更新记录
        await self._delete_update_info(json.loads(subscription))

        return True

    def get_subscription(self, name: str, umo: str) -> RssSubscription | None:
        """获取指定订阅信息。

        Args:
            name: 订阅名称。
            umo: 订阅目标的UMO，用于验证权限。

        Returns:
            订阅信息字典，未找到返回None。
        """
        with self.subscription_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data: RssSubscription = json.loads(line)
                    if data["name"] == name and data["umo"] == umo:
                        return data

        return None

    def list_subscriptions(self, umo: str) -> list[RssSubscription]:
        """列出指定UMO的所有订阅。

        Args:
            umo: 订阅目标的UMO。

        Returns:
            该UMO的所有订阅列表。
        """
        subscriptions: list[RssSubscription] = []

        with self.subscription_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data: RssSubscription = json.loads(line)
                    if data["umo"] == umo:
                        subscriptions.append(data)

        return subscriptions

    def list_all_subscriptions(self) -> list[RssSubscription]:
        """列出所有订阅。

        Returns:
            所有订阅的列表。
        """
        subscriptions: list[RssSubscription] = []

        with self.subscription_file.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data: RssSubscription = json.loads(line)
                    subscriptions.append(data)

        return subscriptions

    def validate_url(self, url: str) -> bool:
        parsed = urlparse(url)

        if parsed.scheme not in ["http", "https"]:
            return False

        if not parsed.hostname:
            return False

        return True
