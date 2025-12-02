"""
定时任务模块 - 处理周榜的定时更新
"""
import asyncio
from datetime import datetime
from typing import Optional, Callable, Awaitable

from astrbot.api import logger


class SchedulerTask:
    """定时更新任务管理器"""

    def __init__(self, fetch_callback: Callable[[], Awaitable]):
        """
        初始化定时任务管理器
        
        Args:
            fetch_callback: 用于获取周榜数据的回调函数
        """
        self._fetch_callback = fetch_callback
        self._update_task: Optional[asyncio.Task] = None

    async def _update_loop(self) -> None:
        """后台定时更新任务，每周六自动更新"""
        while True:
            try:
                now = datetime.now()
                # 周六 = weekday() == 5
                if now.weekday() == 5:
                    logger.info("周六定时更新周榜数据...")
                    await self._fetch_callback()
                    # 更新完成后等待到下周六（等待约7天）
                    await asyncio.sleep(24 * 60 * 60)  # 等待1天后继续检查
                else:
                    # 非周六，每小时检查一次
                    await asyncio.sleep(60 * 60)
            except asyncio.CancelledError:
                logger.info("定时更新任务已取消")
                break
            except Exception as e:
                logger.error(f"定时更新任务异常: {e}")
                await asyncio.sleep(60 * 60)

    def start(self) -> None:
        """启动定时更新任务"""
        if self._update_task is None or self._update_task.done():
            self._update_task = asyncio.create_task(self._update_loop())
            logger.info("定时更新任务已启动")

    async def stop(self) -> None:
        """停止定时更新任务"""
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
            self._update_task = None
            logger.info("定时更新任务已停止")

    @property
    def is_running(self) -> bool:
        """检查任务是否正在运行"""
        return self._update_task is not None and not self._update_task.done()
