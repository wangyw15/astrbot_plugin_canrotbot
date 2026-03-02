import random
from abc import ABC, abstractmethod
from pathlib import Path

from astrbot.api import logger

ASSET_PATH = Path(__file__).parent.parent / "assets"


class SigninTheme(ABC):
    """
    签到主题抽象基类。

    所有签到主题类都必须继承自此类并实现其抽象属性和方法。
    该类定义了签到主题的基本接口，包括主题名称、别名和 HTML 内容生成方法。
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """主题的唯一名称。"""
        pass

    @property
    @abstractmethod
    def aliases(self) -> list[str]:
        """主题的别名列表，用于支持多种查找方式。"""
        pass

    @abstractmethod
    async def generate(self, title: str, content: str) -> str:
        """生成签到卡片的 HTML 内容。

        根据提供的标题和内容，结合主题的模板和样式，生成完整的 HTML 字符串。

        Args:
            title: 签到卡片的标题
            content: 签到卡片的内容

        Returns:
            完整的签到卡片 HTML 字符串
        """
        pass


_themes: list[SigninTheme] = []
"""已注册的签到主题列表，用于存储所有通过 register_theme 函数注册的主题实例。"""


def register_theme(theme: SigninTheme):
    """
    注册一个签到主题实例。

    将主题实例添加到全局主题列表中，以便后续可以通过名称或别名查找和使用。

    Args:
        theme: 要注册的主题实例，必须是 SigninTheme 抽象基类的子类实例，
               确保实现了 name、aliases 和 generate 方法。
    """
    _themes.append(theme)
    logger.info(f"已加载主题 {theme.name}")


def get_themes() -> list[SigninTheme]:
    """
    获取所有已注册的签到主题实例列表。

    Returns:
        包含所有已注册主题实例的列表，列表顺序与注册顺序一致。
    """
    return _themes


def get_theme(name: str) -> SigninTheme | None:
    """
    根据名称或别名查找并返回签到主题实例。

    支持以下查找方式：
    1. 精确匹配主题名称
    2. 匹配主题的别名
    3. 支持 "random" 特殊值，随机返回一个主题实例

    如果名称同时匹配多个主题的别名，则返回最后一个匹配的主题。

    Args:
        name: 要查找的主题名称、别名，或 "random" 用于随机选择。

    Returns:
        匹配到的主题实例，如果未找到任何匹配项则返回 None。
    """
    if name == "random":
        return random.choice(get_themes())

    alias_match_theme: SigninTheme | None = None
    for theme in get_themes():
        if theme.name == name:
            return theme
        if name in theme.aliases:
            alias_match_theme = theme

    return alias_match_theme
