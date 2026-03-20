import random
from collections import namedtuple


class RandomSelect:
    Item = namedtuple("Item", ["name", "weight"])

    def parse_items(self, raw_items: str) -> list[list[Item]]:
        """
        解析项目列表

        :param raw_items: 项目列表，同一个列表中的项目以逗号分隔，不同列表以分号分割

        :return: 项目列表
        """
        raw_items_set = raw_items.replace("；", ";").split(";")
        result: list[list[RandomSelect.Item]] = []

        # 处理权重
        for raw_items in raw_items_set:
            current_raw_items = raw_items.replace("，", ",").split(",")
            current_items: list[RandomSelect.Item] = []
            for raw_item in current_raw_items:
                raw_item = raw_item.strip()
                if not raw_item:
                    continue

                raw_item = raw_item.replace("：", ":")
                weight = 1
                if ":" in raw_item:
                    raw_item, weight = raw_item.split(":", 1)
                    weight = float(weight)
                current_items.append(RandomSelect.Item(raw_item, weight))
            result.append(current_items)

        return result

    def dump_items(self, items_set: list[list[Item]]) -> str:
        """
        将项目列表转换为字符串

        :param items_set: 项目列表

        :return: 字符串
        """
        return ";".join(
            (",".join(f"{item.name}:{item.weight}" for item in items))
            for items in items_set
        )

    def select(self, items_set: list[list[Item]]) -> list[str]:
        """
        从多个列表中，对每一个列表随机选择一个项目

        :param items_set: 项目列表

        :return: 选择的项目
        """
        if not items_set:
            raise ValueError("Empty items set")
        for items in items_set:
            if not items:
                raise ValueError("Empty items")

        selected_items: list[str] = []

        for items in items_set:
            # 计算权重总和
            total_weight = sum(item.weight for item in items)

            if total_weight == 0:
                raise ValueError("Total weight is 0")

            # 随机选择
            random_num = random.uniform(0, total_weight)
            for item in items:
                random_num -= item.weight
                if random_num <= 0:
                    break
            else:
                raise ValueError("Random select failed")
            selected_items.append(item.name)

        return selected_items

    def __call__(self, items: str | list[list[Item]]) -> list[str]:
        if isinstance(items, str):
            items = self.parse_items(items)

        return self.select(items)
