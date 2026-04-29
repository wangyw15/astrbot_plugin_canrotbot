import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict, cast

from jinja2 import Environment, FileSystemLoader, Template

from astrbot.core.utils.astrbot_path import get_astrbot_data_path

T_SpinGrid = list[list[str]]


class ResultDetail(TypedDict):
    pattern: str
    symbol: str
    points: float


class SpinRecord(TypedDict):
    time: str
    grid: T_SpinGrid
    total_score: float
    details: list[ResultDetail]


class UserRecord(TypedDict):
    total_score: float
    total_spin: int
    total_zero_spin: int
    longest_zero_streak: int
    current_zero_streak: int
    symbol_score: dict[str, float]
    symbol_count: dict[str, int]
    best: SpinRecord | None


class ScoreManager:
    def __init__(self, plugin_name: str = "slot_machine") -> None:
        self.template_path = Path(__file__).parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader([self.template_path]))

        self.data_path = Path(get_astrbot_data_path()) / "plugin_data" / plugin_name
        if not self.data_path.exists():
            self.data_path.mkdir(parents=True)

        self.record_path = self.data_path / "records"
        if not self.record_path.exists():
            self.record_path.mkdir(parents=True)

        self.spin_path = self.data_path / "spins"
        if not self.spin_path.exists():
            self.spin_path.mkdir(parents=True)

    def _rebuild_record_from_spins(self, uid: str) -> UserRecord:
        spins = self.get_spins(uid)

        longest_zero_streak = 0
        best: SpinRecord | None = None
        total_score = 0.0
        total_zero_spin = 0
        symbol_score: dict[str, float] = {}
        symbol_count: dict[str, int] = {}

        temp_streak = 0
        for spin in spins:
            score = spin["total_score"]
            total_score += score

            if best is None or score > best["total_score"]:
                best = spin

            if score == 0:
                total_zero_spin += 1
                temp_streak += 1
                longest_zero_streak = max(longest_zero_streak, temp_streak)
            else:
                temp_streak = 0

            for detail in spin["details"]:
                symbol = detail["symbol"]
                symbol_score[symbol] = symbol_score.get(symbol, 0.0) + detail["points"]
                symbol_count[symbol] = symbol_count.get(symbol, 0) + 1

        current_zero_streak = 0
        for spin in reversed(spins):
            if spin["total_score"] == 0:
                current_zero_streak += 1
            else:
                break

        return {
            "total_score": total_score,
            "total_spin": len(spins),
            "total_zero_spin": total_zero_spin,
            "longest_zero_streak": longest_zero_streak,
            "current_zero_streak": current_zero_streak,
            "symbol_score": symbol_score,
            "symbol_count": symbol_count,
            "best": best,
        }

    def get_record(self, uid: str) -> UserRecord:
        record: UserRecord | dict[str, Any] = {}

        record_file = self.record_path / f"{uid}.json"
        if record_file.exists():
            with record_file.open("r", encoding="utf-8") as f:
                record = json.load(f)

        expected_keys = set(UserRecord.__annotations__.keys())
        if not expected_keys.issubset(record.keys()):
            record = self._rebuild_record_from_spins(uid)
            with record_file.open("w", encoding="utf-8") as f:
                json.dump(record, f, ensure_ascii=False)

        return cast(UserRecord, record)

    def add_spin(
        self,
        uid: str,
        grid: T_SpinGrid,
        total_score: float,
        details: list[ResultDetail],
    ):
        spin: SpinRecord = {
            "time": datetime.now().astimezone(timezone.utc).isoformat(),
            "grid": grid,
            "total_score": total_score,
            "details": details,
        }

        spin_file = self.spin_path / f"{uid}.jsonl"
        if not spin_file.exists():
            spin_file.touch()
        with spin_file.open("a", encoding="utf-8") as f:
            f.write(json.dumps(spin, ensure_ascii=False) + "\n")

        record: UserRecord = self.get_record(uid)
        record["total_score"] += total_score
        record["total_spin"] += 1
        if record["best"] is None or total_score > record["best"]["total_score"]:
            record["best"] = spin

        for detail in details:
            symbol = detail["symbol"]
            record["symbol_score"][symbol] = (
                record["symbol_score"].get(symbol, 0.0) + detail["points"]
            )
            record["symbol_count"][symbol] = record["symbol_count"].get(symbol, 0) + 1

        if total_score == 0:
            record["total_zero_spin"] += 1
            record["current_zero_streak"] += 1
            record["longest_zero_streak"] = max(
                record["longest_zero_streak"], record["current_zero_streak"]
            )
        else:
            record["current_zero_streak"] = 0

        record_file = self.record_path / f"{uid}.json"
        with record_file.open("w", encoding="utf-8") as f:
            json.dump(record, f, ensure_ascii=False)

    def get_record_text(self, uid: str) -> str:
        def _convert_time(time: str) -> str:
            return (
                datetime.fromisoformat(time).astimezone().strftime("%Y-%m-%d %H:%M:%S")
            )

        record = self.get_record(uid)
        if record is None:
            return "暂无老虎机记录"
        template: Template = self.jinja_env.get_template("record.jinja")
        return template.render(record=record, convert_time=_convert_time)

    def get_spins(self, uid: str) -> list[SpinRecord]:
        spin_file = self.spin_path / f"{uid}.jsonl"
        if not spin_file.exists():
            return []

        spins: list[SpinRecord] = []
        with spin_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                spin: SpinRecord = json.loads(line)
                spins.append(spin)
        return spins


class SlotMachine:
    SYMBOLS = {
        "🍋": {"amount": 2, "weight": 194},
        "🍒": {"amount": 2, "weight": 194},
        "🍀": {"amount": 3, "weight": 149},
        "🔔": {"amount": 3, "weight": 149},
        "💎": {"amount": 5, "weight": 119},
        "🎁": {"amount": 5, "weight": 119},
        "7️⃣": {"amount": 7, "weight": 76},
    }

    PATTERN = {
        "横": {"multiplier": 1.0},
        "竖": {"multiplier": 1.0},
        "斜": {"multiplier": 1.0},
        "长横": {"multiplier": 2.0},
        "超长横": {"multiplier": 3.0},
        "上折线": {"multiplier": 4.0},
        "下折线": {"multiplier": 4.0},
        "上": {"multiplier": 7.0},
        "下": {"multiplier": 7.0},
        "眼": {"multiplier": 8.0},
        "大奖": {"multiplier": 10.0},
    }

    def __init__(self):
        self.rows = 3
        self.cols = 5

        self.grid: T_SpinGrid = []
        self.score_details: list[ResultDetail] = []
        self.total_score = 0.0

        self.template_path = Path(__file__).parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader([self.template_path]))

    def _fisher_yates(self, arr: list):
        for i in range(len(arr) - 1, 0, -1):
            j = random.randint(0, i)
            arr[i], arr[j] = arr[j], arr[i]
        return arr

    def spin(self, luck: int = 0) -> T_SpinGrid:
        """生成随机老虎机结果"""
        symbols = list(self.SYMBOLS.keys())
        weights = [self.SYMBOLS[s]["weight"] for s in symbols]
        flat_grid = random.choices(symbols, weights=weights, k=self.rows * self.cols)

        # 幸运值机制
        positions = list(range(self.rows * self.cols))
        self._fisher_yates(positions)
        replace_symbol = random.choices(symbols, weights=weights, k=1)[0]
        for i in positions[:luck]:
            flat_grid[i] = replace_symbol

        self.grid = [
            flat_grid[row * self.cols : (row + 1) * self.cols]
            for row in range(self.rows)
        ]
        return self.grid

    def get_symbol_amount(self, symbol: str) -> float:
        """获取符号的基础分值"""
        return self.SYMBOLS.get(symbol, {}).get("amount", 0)

    def get_pattern_multiplier(self, pattern: str) -> float:
        return self.PATTERN.get(pattern, {}).get("multiplier", 0)

    def check_pattern(self, positions: list[tuple[int, int]]) -> str | None:
        """检查指定位置是否都是同一个符号，返回该符号或None"""
        if not positions:
            return None

        symbols = [self.grid[row][col] for row, col in positions]
        first_symbol = symbols[0]

        for symbol in symbols:
            if symbol != first_symbol:
                return None

        return first_symbol

    def check_row(self, row: int, length: int) -> str | None:
        """检查横"""
        for start_col in range(self.cols - length + 1):
            if symbol := self.check_pattern(
                [(row, col) for col in range(start_col, start_col + length)]
            ):
                return symbol
        return None

    def calculate_score(self) -> tuple[float, list[ResultDetail]]:
        """计算总得分"""
        if not self.grid:
            self.spin()

        score_details: list[ResultDetail] = []
        total_score = 0

        # 记录已使用计分的行
        checked_row = set()

        # 超长横
        for row in range(self.rows):
            if symbol := self.check_row(row, 5):
                points = self.get_symbol_amount(symbol) * self.get_pattern_multiplier(
                    "超长横"
                )
                total_score += points
                checked_row.add(row)
                score_details.append(
                    {
                        "pattern": "超长横",
                        "symbol": symbol,
                        "points": points,
                    }
                )

        # 长横
        for row in range(self.rows):
            if row in checked_row:
                continue

            if symbol := self.check_row(row, 4):
                points = self.get_symbol_amount(symbol) * self.get_pattern_multiplier(
                    "长横"
                )
                total_score += points
                checked_row.add(row)
                score_details.append(
                    {
                        "pattern": "长横",
                        "symbol": symbol,
                        "points": points,
                    }
                )

        # 横
        for row in range(self.rows):
            if row in checked_row:
                continue

            if symbol := self.check_row(row, 3):
                points = self.get_symbol_amount(symbol) * self.get_pattern_multiplier(
                    "横"
                )
                total_score += points
                checked_row.add(row)
                score_details.append(
                    {
                        "pattern": "横",
                        "symbol": symbol,
                        "points": points,
                    }
                )

        # 竖
        for col in range(self.cols):
            positions = [(row, col) for row in range(self.rows)]
            if symbol := self.check_pattern(positions):
                points = self.get_symbol_amount(symbol) * self.get_pattern_multiplier(
                    "竖"
                )
                total_score += points
                score_details.append(
                    {
                        "pattern": "竖",
                        "symbol": symbol,
                        "points": points,
                    }
                )

        # 斜 左上到右下
        for start_col in range(self.cols - 2):
            positions = [(row, start_col + row) for row in range(self.rows)]
            if symbol := self.check_pattern(positions):
                points = self.get_symbol_amount(symbol) * self.get_pattern_multiplier(
                    "斜"
                )
                total_score += points
                score_details.append(
                    {
                        "pattern": "斜",
                        "symbol": symbol,
                        "points": points,
                    }
                )

        # 斜 右上到左下
        for start_col in range(2, self.cols):
            positions = [(row, start_col - row) for row in range(self.rows)]
            if symbol := self.check_pattern(positions):
                points = self.get_symbol_amount(symbol) * self.get_pattern_multiplier(
                    "斜"
                )
                total_score += points
                score_details.append(
                    {
                        "pattern": "斜",
                        "symbol": symbol,
                        "points": points,
                    }
                )

        # 上
        upper_found = False
        upper = [(2, 0), (1, 1), (0, 2), (1, 3), (2, 4), (2, 1), (2, 2), (2, 3)]
        if symbol := self.check_pattern(upper):
            points = self.get_symbol_amount(symbol) * self.get_pattern_multiplier("上")
            total_score += points
            upper_found = True
            score_details.append(
                {
                    "pattern": "上",
                    "symbol": symbol,
                    "points": points,
                }
            )

        # 下
        lower_found = False
        lower = [(0, 0), (1, 1), (2, 2), (1, 3), (0, 4), (0, 1), (0, 2), (0, 3)]
        if symbol := self.check_pattern(lower):
            points = self.get_symbol_amount(symbol) * self.get_pattern_multiplier("下")
            total_score += points
            lower_found = True
            score_details.append(
                {
                    "pattern": "下",
                    "symbol": symbol,
                    "points": points,
                }
            )

        # 上折线
        if not upper_found:
            upper_zigzag = [(2, 0), (1, 1), (0, 2), (1, 3), (2, 4)]
            if symbol := self.check_pattern(upper_zigzag):
                points = self.get_symbol_amount(symbol) * self.get_pattern_multiplier(
                    "上折线"
                )
                total_score += points
                score_details.append(
                    {
                        "pattern": "上折线",
                        "symbol": symbol,
                        "points": points,
                    }
                )

        # 下折线
        if not lower_found:
            lower_zigzag = [(0, 0), (1, 1), (2, 2), (1, 3), (0, 4)]
            if symbol := self.check_pattern(lower_zigzag):
                points = self.get_symbol_amount(symbol) * self.get_pattern_multiplier(
                    "下折线"
                )
                total_score += points
                score_details.append(
                    {
                        "pattern": "下折线",
                        "symbol": symbol,
                        "points": points,
                    }
                )

        # 眼
        eye = [
            (0, 1),
            (0, 2),
            (0, 3),
            (1, 0),
            (1, 1),
            (1, 3),
            (1, 4),
            (2, 1),
            (2, 2),
            (2, 3),
        ]
        if symbol := self.check_pattern(eye):
            points = self.get_symbol_amount(symbol) * self.get_pattern_multiplier("眼")
            total_score += points
            score_details.append(
                {
                    "pattern": "眼",
                    "symbol": symbol,
                    "points": points,
                }
            )

        # 大奖
        big_prize = True
        symbol = self.grid[0][0]
        for row in range(self.rows):
            for col in range(self.cols):
                if self.grid[row][col] != symbol:
                    big_prize = False
        if big_prize:
            points = self.get_symbol_amount(symbol) * self.get_pattern_multiplier(
                "大奖"
            )
            total_score += points
            score_details.append(
                {
                    "pattern": "大奖",
                    "symbol": symbol,
                    "points": points,
                }
            )

        self.total_score = total_score
        self.score_details = score_details
        return total_score, score_details

    def generate_result(self):
        """生成得分详情"""
        if not self.grid:
            self.spin()

        if not self.score_details:
            self.calculate_score()

        template: Template = self.jinja_env.get_template("result.jinja")
        return template.render(
            grid=self.grid,
            details=self.score_details,
            total_score=self.total_score,
        )
