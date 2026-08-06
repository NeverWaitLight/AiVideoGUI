from __future__ import annotations

from dataclasses import dataclass


@dataclass
class GenerateTask:
    """视频生成任务数据模型"""
    id: int                     # 主键ID
    provider_task_id: str       # 供应商任务ID
    provider_name: str          # 供应商名称（如 dashscope、seedance）
    model_name: str             # 模型名称
    status: str                 # 任务状态（pending/running/succeeded/failed）
    completed: bool             # 是否已完成
    request_params: str         # 请求参数（JSON字符串）
    video_url: str              # 视频URL（供应商返回）
    save_path: str              # 本地保存路径
    error_message: str          # 错误消息
    storyboard_id: int          # 关联的分镜ID
    created_at: int = 0         # 创建时间（毫秒时间戳）
    updated_at: int = 0         # 更新时间（毫秒时间戳）
