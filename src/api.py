"""
API 客户端模块 - 处理周榜数据的网络请求
"""
import asyncio
from typing import Optional

import aiohttp

from astrbot.api import logger

from .constants import RANK_API_URL
from .types import RankResponse
from .cache import CacheManager


class RankAPIClient:
    """周榜 API 客户端"""

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager
        self._cached_data: Optional[RankResponse] = None

    @property
    def cached_data(self) -> Optional[RankResponse]:
        """获取内存中缓存的数据"""
        return self._cached_data

    @cached_data.setter
    def cached_data(self, value: Optional[RankResponse]) -> None:
        """设置内存中缓存的数据"""
        self._cached_data = value

    async def fetch_rank_data(self) -> Optional[RankResponse]:
        """从 API 获取最新周榜数据，失败时返回本地缓存"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(RANK_API_URL, timeout=aiohttp.ClientTimeout(total=30)) as response:
                    if response.status != 200:
                        logger.error(f"API 请求失败，状态码: {response.status}")
                        return self.cache_manager.get_latest_cache()

                    data = await response.json()

                    # 检查是否已缓存该期
                    ranknum = data.get("ranknum")
                    existing = self.cache_manager.load_cache(ranknum) if ranknum else None

                    if existing is None:
                        self.cache_manager.save_cache(data)

                    self._cached_data = RankResponse(**data)
                    return self._cached_data

        except asyncio.TimeoutError:
            logger.error("API 请求超时")
            return self.cache_manager.get_latest_cache()
        except aiohttp.ClientError as e:
            logger.error(f"网络请求错误: {e}")
            return self.cache_manager.get_latest_cache()
        except Exception as e:
            logger.error(f"获取周榜数据失败: {e}")
            return self.cache_manager.get_latest_cache()

    def load_from_cache(self) -> Optional[RankResponse]:
        """从本地缓存加载数据到内存"""
        self._cached_data = self.cache_manager.get_latest_cache()
        return self._cached_data
