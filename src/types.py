from typing import List, Optional, Union, Dict, Any
from pydantic import BaseModel, Field

# 1. 定义引用数据/基础数据指标 (referSource)
# 这些字段在 referSource 和 视频主对象中都存在
class VideoMetrics(BaseModel):
    point: Optional[int] = None      # 综合得分
    play: Optional[int] = None       # 播放量
    coin: Optional[int] = None       # 硬币数
    comment: Optional[int] = None    # 评论数
    danmaku: Optional[int] = None    # 弹幕数
    favorite: Optional[int] = None   # 收藏数
    like: Optional[int] = None       # 点赞数
    share: Optional[int] = None      # 分享数

# 2. 定义单个视频对象 (main_rank, second_rank 等列表中的元素)
class VideoItem(VideoMetrics):
    url: str
    avid: str
    coverurl: str
    title: str
    # 注意：JSON中pubdate有时是字符串，有时是列表(main_rank[0])，所以用Union
    pubdate: Union[str, List[str]] 
    
    # referSource 结构与外部指标一致，但可能是可选的
    referSource: Optional[VideoMetrics] = None
    
    # rank 在普通列表中是 int，在 super_hit 中是 string ("SuperHit")
    rank: Optional[Union[int, str]] = None
    
    # 额外排名信息，如 {"vocaloid": 1}，是个字典
    ext_rank: Optional[Dict[str, int]] = None
    
    # super_hit 特有字段
    superHit_times: Optional[int] = None

# 3. 定义统计差异对象 (statistic -> diff)
class StatisticDiff(BaseModel):
    total_play: int
    new_video_count: int
    new_in_rank_count: int
    new_in_mainrank_count: int
    new_vc_in_rank_count: int
    new_vc_in_mainrank_count: int
    vc_in_rank_count: int
    vc_in_mainrank_count: int
    new_sv_in_rank_count: int
    new_sv_in_mainrank_count: int
    sv_in_rank_count: int
    sv_in_mainrank_count: int
    new_ace_in_rank_count: int
    new_ace_in_mainrank_count: int
    ace_in_rank_count: int
    ace_in_mainrank_count: int

# 4. 定义统计概览对象 (statistic)
class Statistic(BaseModel):
    diff: StatisticDiff
    total_collect_count: int
    new_video_count: int
    new_in_rank_count: int
    new_in_mainrank_count: int
    pick_up_count: int
    oth_pick_up_count: int
    new_vc_in_rank_count: int
    new_vc_in_mainrank_count: int
    vc_in_rank_count: int
    vc_in_mainrank_count: int
    new_sv_in_rank_count: int
    new_sv_in_mainrank_count: int
    sv_in_rank_count: int
    sv_in_mainrank_count: int
    new_ace_in_rank_count: int
    new_ace_in_mainrank_count: int
    ace_in_rank_count: int
    ace_in_mainrank_count: int

# 5. 定义最外层的根对象 (Root)
class RankResponse(BaseModel):
    version: float
    ranknum: int
    url: str
    coverurl: str
    pubdate: str
    generate_time: str
    generate_timestamp: int
    collect_start_time: str
    collect_end_time: str
    collect_start_time_timestamp: int
    collect_end_time_timestamp: int
    
    # 各个榜单列表
    main_rank: List[VideoItem]
    second_rank: List[VideoItem]
    super_hit: List[VideoItem]
    pick_up: List[VideoItem]
    oth_pickup: List[VideoItem]
    Vocaloid_pick_up: List[VideoItem]
    
    # 注意：field name 中包含 '-' (history-1-year)，这在 Python 变量名中是不合法的
    # Pydantic 允许使用 alias 来映射
    history_1_year: List[VideoItem] = Field(..., alias="history-1-year")
    history_10_year: List[VideoItem] = Field(..., alias="history-10-year")
    
    ed: List[VideoItem]
    op: List[VideoItem]
    
    statistic: Statistic
    thanks_list: List[Any] # 示例中为空，暂定为 Any