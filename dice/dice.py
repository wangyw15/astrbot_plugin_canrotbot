import random
import re


class Dice:
    PATTERN = r"(?:(\d+)?[Dd](\d+))"

    @classmethod
    def eval(cls, expr: str) -> int:
        """计算骰子表达式，如1d10，2d6，d100"""
        if not re.fullmatch(cls.PATTERN, expr):
            raise ValueError("无效的骰子表达式: " + expr)

        expr = expr.lower()
        if expr.isdigit():
            return int(expr)

        # 不指定骰子个数
        if expr.startswith("d"):
            return random.randint(1, int(expr[1:]))

        # 指定骰子个数
        nums = [int(x) for x in expr.split("d")]
        return sum(random.randint(1, nums[1]) for _ in range(nums[0]))

    @classmethod
    def complex_dice_expression(cls, expr: str) -> tuple[int, str]:
        """
        复杂骰子表达式，如d10+1+2d6

        Args:
            expr: 骰子表达式

        Return:
            计算结果, 计算后的表达式
        """
        expr = expr.lower()
        expr_arr = list(expr)
        simple_seg: list[tuple[tuple[int, int], str]] = []  # 简单骰子表达式的位置和内容

        # 找出所有骰子表达式
        for i in re.finditer(r"((\d+)?[Dd](\d+)|\d+)", expr):
            simple_seg.append((i.span(), i.group()))
        simple_seg.reverse()  # 从后往前替换，避免替换后索引变化

        # 替换骰子表达式为数字
        for i in simple_seg:
            expr_arr[i[0][0] : i[0][1]] = [str(cls.eval(i[1]))]
        calculated_expr = "".join(expr_arr)  # 计算后的表达式
        return eval(calculated_expr), calculated_expr
