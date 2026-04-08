from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader


class AniListMessage:
    # 初始化 Jinja2 环境
    TEMPLATE_DIR = Path(__file__).parent / "templates"
    JINJA_ENV = Environment(loader=FileSystemLoader(TEMPLATE_DIR))

    @classmethod
    def anilist_search(
        cls, data: dict[str, Any], markdown: bool = False, with_url: bool = True
    ) -> str:
        """生成 AniList 搜索结果消息

        Args:
            data: AniList API 返回的数据
            markdown: 是否使用 Markdown 格式

        Returns:
            生成的消息文本
        """
        template_name = (
            "anilist_search_md.jinja" if markdown else "anilist_search.jinja"
        )
        template = cls.JINJA_ENV.get_template(template_name)
        return template.render(data=data, with_url=with_url)
