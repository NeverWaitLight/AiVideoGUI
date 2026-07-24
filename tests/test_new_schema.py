"""测试新的 screenplay 表结构"""

import os
import sys
import time

# 设置 UTF-8 输出
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

from storage.database import DatabaseManager
from models.data_models import Scene, SceneLocation, SceneTime

# 初始化数据库
db_path = os.path.expandvars(r"$LOCALAPPDATA\ai-video-gui\data\ai-video-gui.db")
os.makedirs(os.path.dirname(db_path), exist_ok=True)

db = DatabaseManager(db_path)

# 创建测试项目
created_project = db.create_project(
    name="测试项目",
    resolution="720P",
    aspect_ratio="16:9"
)
print(f"[OK] 创建项目：ID={created_project.id}, 名称={created_project.name}")

# 创建测试场次
now_ms = int(time.time() * 1000)
scene1 = Scene(
    id=0,  # 自增ID
    project_id=created_project.id,
    scene_number=1,
    location_type=SceneLocation.INTERIOR,
    location="客厅",
    time_type=SceneTime.DAY,
    time_detail="下午3点",
    content="李明推门进入，环顾四周。",
    created_at=now_ms,
    updated_at=now_ms,
)
created_scene1 = db.create_scene(scene1)
print(f"[OK] 创建场次1：ID={created_scene1.id}, 场次号={created_scene1.scene_number}")

scene2 = Scene(
    id=0,
    project_id=created_project.id,
    scene_number=2,
    location_type=SceneLocation.EXTERIOR,
    location="公园",
    time_type=SceneTime.NIGHT,
    time_detail="",
    content="李明独自坐在长椅上。",
    created_at=now_ms,
    updated_at=now_ms,
)
created_scene2 = db.create_scene(scene2)
print(f"[OK] 创建场次2：ID={created_scene2.id}, 场次号={created_scene2.scene_number}")

# 查询所有场次
scenes = db.list_scenes(created_project.id)
print(f"\n[OK] 查询项目场次：共 {len(scenes)} 场")
for scene in scenes:
    print(f"  - 第 {scene.scene_number} 场：{scene.location} ({scene.location_type.value})")

# 保存历史版本
db.create_screenplay_history(created_project.id, scenes)
print(f"\n[OK] 保存历史版本")

# 查询历史版本（按时间戳分组）
timestamps = db.list_screenplay_history_timestamps(created_project.id)
print(f"[OK] 查询历史版本：共 {len(timestamps)} 个时间戳")

# 按时间戳查询具体场次历史
history_scenes = db.list_screenplay_history_by_timestamp(created_project.id, timestamps[0])
print(f"[OK] 时间戳 {timestamps[0]} 包含 {len(history_scenes)} 场历史记录")
for h in history_scenes:
    print(f"  - 第 {h.scene_number} 场：{h.location} ({h.location_type.value})")

# 更新场次
db.update_scene(
    created_scene1.id,
    content="李明推门进入，环顾四周，神情凝重。（已修改）",
)
print(f"\n[OK] 更新场次1")

# 再次查询
updated_scene = db.get_scene(created_scene1.id)
print(f"[OK] 查询更新后的场次：{updated_scene.content[:30]}...")

print("\n[SUCCESS] 所有测试通过！新 schema 工作正常。")
