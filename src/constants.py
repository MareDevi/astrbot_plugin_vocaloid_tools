"""
常量配置模块
"""
from astrbot.api.event.filter import PlatformAdapterType

# 支持合并转发的平台
FORWARD_SUPPORTED_PLATFORMS = {PlatformAdapterType.AIOCQHTTP}

# API 地址
RANK_API_URL = "https://www.evocalrank.com/data/info/latest.json"

# 最大缓存周数
MAX_CACHE_COUNT = 10

# 缓存目录名
CACHE_DIR_NAME = "vocaloid_cache"

# 封面图片缓存子目录
COVER_CACHE_DIR_NAME = "covers"
