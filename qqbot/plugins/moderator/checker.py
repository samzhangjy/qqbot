import os
from typing import TypedDict, List


class DFAFilter(object):
    def __init__(self):
        self.keyword_chains = {}
        self.delimit = "\x00"

    def add(self, keyword):
        keyword = keyword.lower()  # 关键词英文变为小写
        chars = keyword.strip()  # 关键字去除首尾空格和换行
        if not chars:  # 如果关键词为空直接返回
            return
        level = self.keyword_chains
        # 遍历关键字的每个字
        for i in range(len(chars)):
            # 如果这个字已经存在字符链的key中就进入其子字典
            if chars[i] in level:
                level = level[chars[i]]
            else:
                if not isinstance(level, dict):
                    break
                for j in range(i, len(chars)):
                    level[chars[j]] = {}
                    last_level, last_char = level, chars[j]
                    level = level[chars[j]]
                last_level[last_char] = {self.delimit: 0}
                break
        if i == len(chars) - 1:
            level[self.delimit] = 0

    def parse(self, path):
        with open(path, encoding="utf-8") as f:
            for keyword in f:
                self.add(str(keyword).strip())

    def check(self, message: str):
        message = message.lower()
        start = 0
        is_valid = True
        while start < len(message):
            level = self.keyword_chains
            step_ins = 0
            for char in message[start:]:
                if char in level:
                    step_ins += 1
                    if self.delimit not in level[char]:
                        level = level[char]
                    else:
                        is_valid = False
                        break
                else:
                    break
            start += 1
            if not is_valid:
                break
        return is_valid

    def filter(self, message, repl="*"):
        message = message.lower()
        ret = []
        start = 0
        while start < len(message):
            level = self.keyword_chains
            step_ins = 0
            for char in message[start:]:
                if char in level:
                    step_ins += 1
                    if self.delimit not in level[char]:
                        level = level[char]
                    else:
                        ret.append(repl * step_ins)
                        start += step_ins - 1
                        break
                else:
                    ret.append(message[start])
                    break
            else:
                ret.append(message[start])
            start += 1

        return "".join(ret)


class FilterType(TypedDict):
    name: str
    id: str
    checker: DFAFilter


class Checker:
    WORDLIST_PATH = os.path.join(os.path.dirname(__file__), "wordlist")

    def __init__(self) -> None:
        self.filters: List[FilterType] = [
            {"name": "advertisement", "id": "ad"},
            {"name": "guns", "id": "guns"},
            {"name": "politics", "id": "politics"},
            {"name": "adult content", "id": "adult"},
            {"name": "offensive (English)", "id": "offensive-en"},
            {"name": "offensive (Chinese)", "id": "offensive-zh"},
        ]
        for i, _ in enumerate(self.filters):
            self.filters[i]["checker"] = DFAFilter()
            self.filters[i]["checker"].parse(
                os.path.join(self.WORDLIST_PATH, f"{self.filters[i]['id']}.txt")
            )

    def check(self, text: str) -> bool:
        disqualified = []
        for filter_ in self.filters:
            if not filter_["checker"].check(text):
                disqualified.append(filter_["name"])
        return disqualified


if __name__ == "__main__":
    checker = Checker()
