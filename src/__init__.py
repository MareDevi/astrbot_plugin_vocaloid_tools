"""
src 模块初始化
导出所有公共类和常量
"""
from .types import RankResponse, VideoItem, VideoMetrics, Statistic, StatisticDiff
from .constants import (
    FORWARD_SUPPORTED_PLATFORMS,
    RANK_API_URL,
    MAX_CACHE_COUNT,
    CACHE_DIR_NAME,
    COVER_CACHE_DIR_NAME,
)
from .cache import CacheManager
from .api import RankAPIClient
from .message import MessageBuilder
from .scheduler import SchedulerTask

__all__ = [
    # Types
    "RankResponse",
    "VideoItem",
    "VideoMetrics",
    "Statistic",
    "StatisticDiff",
    # Constants
    "FORWARD_SUPPORTED_PLATFORMS",
    "RANK_API_URL",
    "MAX_CACHE_COUNT",
    "CACHE_DIR_NAME",
    "COVER_CACHE_DIR_NAME",
    # Classes
    "CacheManager",
    "RankAPIClient",
    "MessageBuilder",
    "SchedulerTask",
]
