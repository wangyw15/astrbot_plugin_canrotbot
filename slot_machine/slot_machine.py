import random
from pathlib import Path
from typing import TypedDict

from jinja2 import Environment, FileSystemLoader, Template


class Result(TypedDict):
    pattern: str
    symbol: str
    points: float


class SlotMachine:
    SYMBOLS = {
        "🍋": {"amount": 2, "weight": 194},
        "🍒": {"amount": 2, "weight": 194},
        "🍀": {"amount": 3, "weight": 149},
        "🔔": {"amount": 3, "weight": 149},
        "💎": {"amount": 5, "weight": 119},
        "🎁": {"amount": 5, "weight": 119},
        "⭐": {"amount": 7, "weight": 76},
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

        self.grid: list[list[str]] = []
        self.score_details: list[Result] = []
        self.total_score = 0.0

        self.template_path = Path(__file__).parent / "templates"
        self.jinja_env = Environment(loader=FileSystemLoader([self.template_path]))

    def spin(self):
        """生成随机老虎机结果"""
        symbols = list(self.SYMBOLS.keys())
        weights = [self.SYMBOLS[s]["weight"] for s in symbols]

        self.grid = []
        for _ in range(self.rows):
            row = random.choices(symbols, weights=weights, k=self.cols)
            self.grid.append(row)

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

    def calculate_score(self) -> tuple[float, list[Result]]:
        """计算总得分"""
        if not self.grid:
            self.spin()

        score_details: list[Result] = []
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
