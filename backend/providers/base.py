# -*- coding: utf-8 -*-
"""SearchProvider 抽象基类：换源只需实现 search()。"""

from abc import ABC, abstractmethod
from typing import List


class SearchProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def search(self, query: str, max_results: int = 8) -> List[dict]:
        """执行一次搜索，返回 [{title, url, snippet}, ...]。

        实现方需自行处理超时与异常——抛出异常由编排层捕获降级。
        """
        raise NotImplementedError
