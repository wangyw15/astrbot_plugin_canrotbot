import json
import uuid
from pathlib import Path
from typing import TypedDict

from jinja2 import Environment, FileSystemLoader, Template, TemplateNotFound

from astrbot.core.utils.astrbot_path import get_astrbot_data_path


class WebhookPushToken(TypedDict):
    umo: str
    token: str


class WebhookPushManager:
    def __init__(self, plugin_name: str) -> None:
        self.data_path = Path(get_astrbot_data_path()) / "plugin_data" / plugin_name
        if not self.data_path.exists():
            self.data_path.mkdir(parents=True)

        self.history_file = self.data_path / "tokens.jsonl"
        if not self.history_file.exists():
            self.history_file.touch()

        self.builtin_template_path = Path(__file__).parent / "templates"
        self.user_template_path = self.data_path / "templates"

        # 初始化 Jinja2 环境，优先查找用户模板，然后是内置模板
        self.jinja_env = Environment(
            loader=FileSystemLoader(
                [self.user_template_path, self.builtin_template_path]
            )
        )

    def get_token(self, umo: str) -> str:
        with self.history_file.open("r", encoding="utf-8") as f:
            while line := f.readline():
                data: WebhookPushToken = json.loads(line)
                if data["umo"] == umo:
                    return data["token"]

        data: WebhookPushToken = {
            "token": uuid.uuid4().hex,
            "umo": umo,
        }
        with self.history_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

        return data["token"]

    def get_umo(self, token: str) -> str | None:
        with self.history_file.open("r", encoding="utf-8") as f:
            while line := f.readline():
                data: WebhookPushToken = json.loads(line)
                if data["token"] == token:
                    return data["umo"]

        return None

    def get_template(
        self, name: str = "default", fallback: bool = True
    ) -> Template | None:
        """
        获取模板内容

        Args:
            name: 模板文件名
            fallback: 未找到对应模板时是否返回默认模板
        """
        template_name = f"{name}.jinja"
        try:
            return self.jinja_env.get_template(template_name)
        except TemplateNotFound:
            if fallback:
                return self.jinja_env.get_template("default.jinja")
            return None
