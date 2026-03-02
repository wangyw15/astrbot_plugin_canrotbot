import json
from datetime import datetime
from pathlib import Path
from typing import TypedDict

from httpx import AsyncClient

from astrbot.core.utils.astrbot_path import get_astrbot_data_path


class SigninHistory(TypedDict):
    uid: str
    title: str
    content: str
    theme: str
    time: str
    """ISO format"""


class HistoryManager:
    def __init__(self, plugin_name: str) -> None:
        self.data_path = Path(get_astrbot_data_path()) / "plugin_data" / plugin_name
        if not self.data_path.exists():
            self.data_path.mkdir(parents=True)

        self.history_file = self.data_path / "history.jsonl"
        if not self.history_file.exists():
            self.history_file.touch()

    def already_signin(self, uid: str) -> bool:
        return self.get_today_record(uid) is not None

    def add_record(
        self,
        uid: str,
        title: str,
        content: str,
        theme: str,
        time: datetime | None = None,
    ):
        if time is None:
            time = datetime.now()

        row: SigninHistory = {
            "uid": uid,
            "title": title,
            "content": content,
            "theme": theme,
            "time": time.isoformat(),
        }
        with self.history_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    def get_today_record(self, uid: str) -> SigninHistory | None:
        with self.history_file.open("r", encoding="utf8") as f:
            while line := f.readline():
                row: SigninHistory = json.loads(line)
                if row["uid"] == uid:
                    time = datetime.fromisoformat(row["time"])
                    if time.date() == datetime.now().date():
                        return row
        return None

    def set_latest_image(self, uid: str, image: bytes):
        with (self.data_path / f"{uid}.png").open("wb") as f:
            f.write(image)

    async def set_latest_image_url(self, uid: str, image: str):
        async with AsyncClient() as client:
            resp = await client.get(image)
            if resp.is_success:
                self.set_latest_image(uid, resp.content)

    def get_latest_image(self, uid: str) -> bytes | None:
        image_path = self.get_latest_image_path(uid)
        if image_path is None:
            return None

        return image_path.read_bytes()

    def get_latest_image_path(self, uid: str) -> Path | None:
        image_path = self.data_path / f"{uid}.png"
        if not image_path.exists():
            return None

        return image_path
