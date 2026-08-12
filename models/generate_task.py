from __future__ import annotations

from dataclasses import dataclass

from models.enums import GenerateTaskType, GenerateTaskCallerType


@dataclass
class GenerateTask:
    """视频/图片/音频/聊天生成任务数据模型"""
    id: int                         # 主键ID
    type: GenerateTaskType          # 任务类型（video/image/audio/chat）
    provider_task_id: str           # 供应商任务ID
    provider_name: str              # 供应商名称（如 dashscope、seedance）
    model_name: str                 # 模型名称
    status: str                     # 任务状态（pending/running/succeeded/failed）
    completed: bool                 # 是否已完成
    request_params: str             # 请求参数（JSON字符串）
    remote_url: str                 # 视频/图片/音频URL（供应商返回）
    local_path: str                 # 本地保存路径（相对工作目录）
    error_message: str              # 错误消息
    caller_type: GenerateTaskCallerType | None = None  # 调用者类型（storyboard/character/cover/chat）
    caller_id: str = ""             # 调用者ID（对应类型的ID或UUID）
    project_id: int | None = None   # 项目ID（关联 projects 表，可为空）
    parent_ids: str = ""            # 父任务ID列表（英文逗号分隔，如 "1,2,3"）
    created_at: int = 0             # 创建时间（毫秒时间戳）
    updated_at: int = 0             # 更新时间（毫秒时间戳）
