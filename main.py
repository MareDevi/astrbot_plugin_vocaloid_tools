"""
Vocaloid 周刊排行榜查询插件
支持查询主榜、副榜、PickUp 榜
"""
from astrbot.api.event import filter, AstrMessageEvent
from astrbot.api.star import Context, Star, register
from astrbot.api import logger

from .src import CacheManager, RankAPIClient, MessageBuilder, SchedulerTask


@register(
    "vocaloid_tools",
    "MareDevi",
    "Vocaloid 工具插件，提供 Vocaloid 周刊排行榜查询功能",
    "1.0.1",
    "https://github.com/MareDevi/astrbot_plugin_vocaloid_tools"
)
class VocaloidRankPlugin(Star):
    """Vocaloid 周刊排行榜插件"""

    def __init__(self, context: Context):
        super().__init__(context)
        
        # 初始化各模块
        self._cache_manager = CacheManager()
        self._api_client = RankAPIClient(self._cache_manager)
        self._message_builder = MessageBuilder(self._cache_manager)
        self._scheduler = SchedulerTask(self._api_client.fetch_rank_data)

    async def initialize(self):
        """插件初始化，启动定时更新任务"""
        logger.info("Vocaloid 周刊插件初始化中...")

        # 预加载本地缓存
        cached_data = self._api_client.load_from_cache()
        if cached_data:
            logger.info(f"已加载本地缓存，第 {cached_data.ranknum} 期")

        # 启动定时更新任务
        self._scheduler.start()
        logger.info("Vocaloid 周刊插件初始化完成")

    async def terminate(self):
        """插件销毁，取消定时任务"""
        await self._scheduler.stop()
        logger.info("Vocaloid 周刊插件已卸载")

    # ==================== 命令处理 ====================

    @filter.command("v周榜")
    async def cmd_main_rank(self, event: AstrMessageEvent):
        """获取 Vocaloid 周刊主榜 Top 10"""
        data = await self._api_client.fetch_rank_data()

        if not data:
            yield event.plain_result("❌ 暂无周榜数据，请稍后再试")
            return

        rank_name = f"主榜 (第{data.ranknum}期)"
        async for result in self._message_builder.send_rank_result(event, data.main_rank, rank_name):
            yield result

    @filter.command("v副榜")
    async def cmd_second_rank(self, event: AstrMessageEvent):
        """获取 Vocaloid 周刊副榜 Top 10"""
        data = await self._api_client.fetch_rank_data()

        if not data:
            yield event.plain_result("❌ 暂无周榜数据，请稍后再试")
            return

        rank_name = f"副榜 (第{data.ranknum}期)"
        async for result in self._message_builder.send_rank_result(event, data.second_rank, rank_name):
            yield result

    @filter.command("pickup榜")
    async def cmd_pickup_rank(self, event: AstrMessageEvent):
        """获取 Vocaloid 周刊 PickUp 榜 Top 10"""
        data = await self._api_client.fetch_rank_data()

        if not data:
            yield event.plain_result("❌ 暂无周榜数据，请稍后再试")
            return

        rank_name = f"PickUp 榜 (第{data.ranknum}期)"
        async for result in self._message_builder.send_rank_result(event, data.pick_up, rank_name):
            yield result
