"""
消息构建模块 - 处理榜单消息的构建和发送
"""
import asyncio
from typing import List

import astrbot.api.message_components as Comp
from astrbot.api.message_components import Nodes
from astrbot.api.event import AstrMessageEvent
from astrbot.api import logger

from .types import VideoItem
from .cache import CacheManager


class MessageBuilder:
    """消息构建器，负责构建榜单消息"""

    def __init__(self, cache_manager: CacheManager):
        self.cache_manager = cache_manager

    @staticmethod
    def format_num(n: int) -> str:
        """格式化数字显示"""
        if n >= 10000:
            return f"{n / 10000:.1f}万"
        return str(n)

    async def build_video_content(self, video: VideoItem, rank: int) -> List:
        """构建单个视频的消息内容（异步，支持封面缓存）"""
        # 格式化播放量等数据
        play = video.play if video.play else 0
        coin = video.coin if video.coin else 0
        favorite = video.favorite if video.favorite else 0
        like = video.like if video.like else 0
        point = video.point if video.point else 0

        info_text = (
            f"🏆 第{rank}名\n"
            f"📺 {video.title}\n"
            f"━━━━━━━━━━━━\n"
            f"▶️ 播放: {self.format_num(play)}\n"
            f"👍 点赞: {self.format_num(like)}\n"
            f"⭐ 收藏: {self.format_num(favorite)}\n"
            f"🪙 硬币: {self.format_num(coin)}\n"
            f"📊 综合得分: {self.format_num(point)}\n"
            f"━━━━━━━━━━━━\n"
            f"🔗 {video.url}"
        )

        # 获取缓存的封面图片路径
        cover_path = await self.cache_manager.get_cached_cover(video.coverurl)

        # 判断是本地路径还是 URL
        if cover_path.startswith("/") or cover_path.startswith("C:") or cover_path.startswith("D:"):
            # 本地文件路径
            image_comp = Comp.Image.fromFileSystem(cover_path)
        else:
            # 仍然是 URL（下载失败时）
            image_comp = Comp.Image.fromURL(cover_path)

        return [
            image_comp,
            Comp.Plain(info_text)
        ]

    async def build_forward_nodes(self, videos: List[VideoItem], bot_id: str, bot_name: str, rank_name: str) -> List:
        """构建合并转发消息节点列表（异步）"""
        nodes = []
        
        # 将 bot_id 转换为整数（QQ号需要是整数类型）
        try:
            uin = int(bot_id)
        except (ValueError, TypeError):
            uin = 10000  # 默认值

        # 添加榜单标题节点
        header_node = Comp.Node(
            uin=uin,
            name=bot_name,
            content=[Comp.Plain(f"📋 Vocaloid 周刊 - {rank_name}\n\n以下是本期 Top 10：")]
        )
        nodes.append(header_node)

        # 添加每个视频的节点
        for idx, video in enumerate(videos[:10], start=1):
            content = await self.build_video_content(video, idx)
            node = Comp.Node(
                uin=uin,
                name=bot_name,
                content=content
            )
            nodes.append(node)

        return nodes

    @staticmethod
    def is_forward_supported(event: AstrMessageEvent) -> bool:
        """检查当前平台是否支持合并转发消息"""
        try:
            # 使用 AstrBot 提供的 API 获取平台名称
            platform_name = event.get_platform_name()
            # aiocqhttp 是 OneBot v11 的平台标识，支持合并转发
            is_supported = platform_name == "aiocqhttp"
            logger.info(f"平台名称: {platform_name}, 支持合并转发: {is_supported}")
            return is_supported
        except Exception as e:
            logger.warning(f"获取平台类型失败: {e}")
            return False

    async def send_rank_result(self, event: AstrMessageEvent, videos: List[VideoItem], rank_name: str):
        """发送榜单结果，根据平台选择合并转发或多条消息"""
        use_forward = self.is_forward_supported(event)
        logger.info(f"发送榜单: {rank_name}, 使用合并转发: {use_forward}")
        
        if use_forward:
            # 支持合并转发的平台，使用 Nodes 包装所有 Node
            # 关键：必须使用 Nodes 包装多个 Node，否则每个 Node 会被单独发送
            bot_id = event.message_obj.self_id
            bot_name = "Vocaloid 周刊"
            nodes = await self.build_forward_nodes(videos, bot_id, bot_name, rank_name)
            logger.info(f"构建了 {len(nodes)} 个转发节点，准备发送合并转发消息")
            # 使用 Nodes 包装所有 Node，一次性发送合并转发
            forward_nodes = Nodes(nodes)
            yield event.chain_result([forward_nodes])
        else:
            # 不支持合并转发的平台，发送多条普通消息
            # 先发送标题
            yield event.plain_result(f"📋 Vocaloid 周刊 - {rank_name}\n\n以下是本期 Top 10：")

            # 逐条发送每个视频
            for idx, video in enumerate(videos[:10], start=1):
                content = await self.build_video_content(video, idx)
                yield event.chain_result(content)
                # 添加短暂延迟避免触发平台限流
                await asyncio.sleep(0.5)
