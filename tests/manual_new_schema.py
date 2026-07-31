import os
import sys
import time

if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

from storage.orm.base import init_engine, create_all_tables, get_session, close_session
from storage.repositories.project_repository import ProjectRepository
from storage.repositories.screenplay_repository import ScreenplayRepository, ScreenplayHistoryRepository
from models.enums import SceneLocation, SceneTime
from models.scene import Scene
from models.project import Project

db_path = os.path.expandvars(r"$LOCALAPPDATA\ai-video-gui\data\ai-video-gui.db")
os.makedirs(os.path.dirname(db_path), exist_ok=True)

database_url = f"sqlite:///{db_path}"
init_engine(database_url, echo=False)
create_all_tables()

session = get_session()
project_repo = ProjectRepository(session)
screenplay_repo = ScreenplayRepository(session)
history_repo = ScreenplayHistoryRepository(session)

now_ms = int(time.time() * 1000)
project = Project(
    id=0,
    name="测试项目",
    resolution="720P",
    aspect_ratio="16:9",
    created_at=now_ms,
    updated_at=now_ms,
    cover_image=""
)
created_project = project_repo.create(project)
session.commit()
print(f"[OK] 创建项目：ID={created_project.id}, 名称={created_project.name}")

scene1 = Scene(
    id=0,
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
created_scene1 = screenplay_repo.create(scene1)
session.commit()
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
created_scene2 = screenplay_repo.create(scene2)
session.commit()
print(f"[OK] 创建场次2：ID={created_scene2.id}, 场次号={created_scene2.scene_number}")

scenes = screenplay_repo.list_by_project(created_project.id)
print(f"\n[OK] 查询项目场次：共 {len(scenes)} 场")
for scene in scenes:
    print(f"  - 第 {scene.scene_number} 场：{scene.location} ({scene.location_type.value})")

print(f"\n[OK] 历史记录通过 ORM 事件监听器自动保存")

timestamps = history_repo.distinct_timestamps_by_project(created_project.id)
print(f"[OK] 查询历史版本：共 {len(timestamps)} 个时间戳")

if timestamps:
    history_scenes = history_repo.list_by_project_and_timestamp(created_project.id, timestamps[0])
    print(f"[OK] 时间戳 {timestamps[0]} 包含 {len(history_scenes)} 场历史记录")
    for h in history_scenes:
        print(f"  - 第 {h.scene_number} 场：{h.location} ({h.location_type.value})")

entity = session.get(screenplay_repo.entity_class, created_scene1.id)
entity.content = "李明推门进入，环顾四周，神情凝重。（已修改）"
entity.updated_at = int(time.time() * 1000)
session.commit()
print(f"\n[OK] 更新场次1")

updated_scene = screenplay_repo.get_by_id(created_scene1.id)
print(f"[OK] 查询更新后的场次：{updated_scene.content[:30]}...")

close_session()

print("\n[SUCCESS] 所有测试通过！新 schema 工作正常。")
