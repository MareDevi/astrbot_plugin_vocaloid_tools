"""
缓存管理模块 - 处理周榜数据和封面图片的本地缓存
"""
import json
import hashlib
from pathlib import Path
from typing import Optional

import aiohttp

from astrbot.api import logger

from .constants import CACHE_DIR_NAME, COVER_CACHE_DIR_NAME, MAX_CACHE_COUNT
from .types import RankResponse


class CacheManager:
    """缓存管理器，负责周榜数据和封面图片的本地缓存"""

    def __init__(self):
        self._ensure_cache_dirs()

    def _ensure_cache_dirs(self) -> None:
        """确保缓存目录存在"""
        self.get_cache_dir()
        self.get_cover_cache_dir()

    # ==================== 周榜数据缓存 ====================

    def get_cache_dir(self) -> Path:
        """获取缓存目录路径，存储在 data/ 目录下"""
        cache_dir = Path("data") / CACHE_DIR_NAME
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def load_cache(self, ranknum: int) -> Optional[RankResponse]:
        """按期号加载本地缓存"""
        cache_file = self.get_cache_dir() / f"rank_{ranknum}.json"
        if not cache_file.exists():
            return None
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return RankResponse(**data)
        except Exception as e:
            logger.error(f"加载缓存失败: {e}")
            return None

    def save_cache(self, data: dict) -> None:
        """保存周榜数据到本地缓存"""
        try:
            ranknum = data.get("ranknum")
            if not ranknum:
                logger.error("周榜数据缺少 ranknum 字段")
                return

            cache_file = self.get_cache_dir() / f"rank_{ranknum}.json"
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"已缓存第 {ranknum} 期周榜")
            self.cleanup_old_caches()
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")

    def cleanup_old_caches(self) -> None:
        """清理超过 MAX_CACHE_COUNT 期的旧缓存（包括对应的封面图片）"""
        cache_dir = self.get_cache_dir()
        cache_files = sorted(cache_dir.glob("rank_*.json"), key=lambda f: f.stat().st_mtime)

        while len(cache_files) > MAX_CACHE_COUNT:
            oldest = cache_files.pop(0)
            # 先提取该期周榜中的所有封面 URL，然后删除对应的图片缓存
            self._delete_covers_for_rank_file(oldest)
            oldest.unlink()
            logger.info(f"已删除旧缓存: {oldest.name}")

    def get_latest_cache(self) -> Optional[RankResponse]:
        """获取最新一期的本地缓存"""
        cache_dir = self.get_cache_dir()
        cache_files = sorted(cache_dir.glob("rank_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)

        if not cache_files:
            return None

        try:
            with open(cache_files[0], "r", encoding="utf-8") as f:
                data = json.load(f)
            return RankResponse(**data)
        except Exception as e:
            logger.error(f"加载最新缓存失败: {e}")
            return None

    # ==================== 封面图片缓存 ====================

    def get_cover_cache_dir(self) -> Path:
        """获取封面图片缓存目录"""
        cover_dir = self.get_cache_dir() / COVER_CACHE_DIR_NAME
        cover_dir.mkdir(parents=True, exist_ok=True)
        return cover_dir

    def get_cover_cache_path(self, url: str) -> Path:
        """根据 URL 生成封面图片缓存路径"""
        # 使用 URL 的 MD5 哈希作为文件名
        url_hash = hashlib.md5(url.encode()).hexdigest()
        # 从 URL 提取扩展名，默认 .jpg
        ext = ".jpg"
        if ".png" in url.lower():
            ext = ".png"
        elif ".webp" in url.lower():
            ext = ".webp"
        return self.get_cover_cache_dir() / f"{url_hash}{ext}"

    async def get_cached_cover(self, url: str) -> str:
        """获取封面图片，优先使用本地缓存，无缓存则下载并保存"""
        cache_path = self.get_cover_cache_path(url)

        # 如果缓存存在，直接返回本地路径
        if cache_path.exists():
            return str(cache_path.absolute())

        # 下载并缓存图片
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status == 200:
                        content = await response.read()
                        with open(cache_path, "wb") as f:
                            f.write(content)
                        logger.debug(f"已缓存封面图片: {cache_path.name}")
                        return str(cache_path.absolute())
                    else:
                        logger.warning(f"下载封面失败，状态码: {response.status}，使用原始 URL")
                        return url
        except Exception as e:
            logger.warning(f"下载封面图片失败: {e}，使用原始 URL")
            return url

    # ==================== 封面清理辅助方法 ====================

    def _extract_cover_urls_from_rank(self, rank_data: dict) -> set:
        """从周榜数据中提取所有封面图片 URL"""
        cover_urls = set()
        # 所有包含视频列表的字段
        video_list_fields = [
            "main_rank", "second_rank", "super_hit", "pick_up",
            "oth_pickup", "Vocaloid_pick_up", "history-1-year",
            "history-10-year", "ed", "op"
        ]
        for field in video_list_fields:
            videos = rank_data.get(field, [])
            if isinstance(videos, list):
                for video in videos:
                    if isinstance(video, dict) and "coverurl" in video:
                        cover_urls.add(video["coverurl"])
        return cover_urls

    def _delete_covers_for_rank_file(self, rank_file: Path) -> None:
        """删除指定周榜文件对应的所有封面图片缓存"""
        try:
            with open(rank_file, "r", encoding="utf-8") as f:
                rank_data = json.load(f)

            cover_urls = self._extract_cover_urls_from_rank(rank_data)
            deleted_count = 0

            for url in cover_urls:
                cover_path = self.get_cover_cache_path(url)
                if cover_path.exists():
                    cover_path.unlink()
                    deleted_count += 1

            if deleted_count > 0:
                logger.info(f"已删除 {deleted_count} 张封面图片缓存 (关联: {rank_file.name})")
        except Exception as e:
            logger.warning(f"清理封面图片缓存失败: {e}")

    def cleanup_orphan_covers(self) -> None:
        """清理不属于任何缓存周榜的孤立封面图片"""
        try:
            # 收集所有缓存周榜中的封面 URL 哈希
            valid_cover_hashes = set()
            cache_dir = self.get_cache_dir()

            for cache_file in cache_dir.glob("rank_*.json"):
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        rank_data = json.load(f)
                    cover_urls = self._extract_cover_urls_from_rank(rank_data)
                    for url in cover_urls:
                        url_hash = hashlib.md5(url.encode()).hexdigest()
                        valid_cover_hashes.add(url_hash)
                except Exception:
                    continue

            # 删除不在有效列表中的封面图片
            cover_dir = self.get_cover_cache_dir()
            deleted_count = 0

            for cover_file in cover_dir.glob("*"):
                # 提取文件名中的哈希部分
                file_hash = cover_file.stem
                if file_hash not in valid_cover_hashes:
                    cover_file.unlink()
                    deleted_count += 1

            if deleted_count > 0:
                logger.info(f"已清理 {deleted_count} 张孤立封面图片缓存")
        except Exception as e:
            logger.warning(f"清理孤立封面图片失败: {e}")
