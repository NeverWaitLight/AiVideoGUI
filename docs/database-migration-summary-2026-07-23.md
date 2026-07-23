# 数据库架构迁移总结

**日期：** 2026-07-23  
**目标：** 统一所有数据库表为 64 位整数自增 ID + 13 位毫秒时间戳

## 迁移方案

删除旧数据库，直接使用新的 ORM 模型初始化数据库（无数据迁移需求）。

## 核心改动

### 1. ORM 模型层 (`storage/orm/models.py`)

**修改内容：**
- 所有使用 BigInteger 主键的 Entity 类，将 `id` 字段类型从 `Mapped[int]` 改为 `Mapped[Optional[int]]`
- 所有 Entity 类的 `updated_at` 字段类型从 `Mapped[int]` 改为 `Mapped[Optional[int]]`

**影响的 Entity：**
- ProjectEntity ✓
- ConversationEntity ✓
- MessageEntity ✓
- MediaFileEntity ✓
- OutlineEntity ✓
- OutlineHistoryEntity ✓
- ScriptEntity ✓
- SceneEntity ✓
- ScriptHistoryEntity ✓
- ShotEntity ✓
- ShotHistoryEntity ✓
- CharacterHistoryEntity ✓
- ActiveTaskEntity（仅 updated_at）✓
- CharacterEntity（仅 updated_at，ID 使用 INTEGER）✓

**示例：**
```python
# 修改前
id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
updated_at: Mapped[int] = mapped_column(BigInteger, nullable=False)

# 修改后
id: Mapped[Optional[int]] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
updated_at: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=False)
```

### 2. 自动时间戳填充 (`storage/orm/base.py`)

**新增事件监听器：**
```python
@event.listens_for(Base, "before_insert", propagate=True)
def before_insert_listener(mapper, connection, target):
    """插入前自动填充 created_at 和 updated_at。"""
    from utils.time_utils import now_ms
    
    now = now_ms()
    if hasattr(target, "created_at"):
        created_at_value = getattr(target, "created_at", None)
        if created_at_value is None or created_at_value == 0:
            target.created_at = now
    if hasattr(target, "updated_at"):
        updated_at_value = getattr(target, "updated_at", None)
        if updated_at_value is None or updated_at_value == 0:
            target.updated_at = now

@event.listens_for(Base, "before_update", propagate=True)
def before_update_listener(mapper, connection, target):
    """更新前自动更新 updated_at。"""
    from utils.time_utils import now_ms
    
    if hasattr(target, "updated_at"):
        target.updated_at = now_ms()
```

**工作原理：**
- 当 Entity 的 `created_at`/`updated_at` 字段为 `None` 或 `0` 时，自动填充当前毫秒时间戳
- 更新操作时自动刷新 `updated_at` 字段

### 3. Repository 层修改

**修改内容：**

#### 3.1 基类 (`storage/repositories/base.py`)

```python
def create(self, dto: DTOType) -> DTOType:
    """创建新记录。"""
    entity = self._to_entity(dto)
    self.session.add(entity)
    self.session.flush()  # 先 flush 让数据库生成 ID 和触发事件监听器
    self.session.commit()
    return self._to_dto(entity)
```

#### 3.2 所有 Repository 的 `_to_entity()` 方法

**模式：**
```python
def _to_entity(self, dto: XXX) -> XXXEntity:
    """DTO → Entity 转换。"""
    if dto.id == 0:
        # 创建新记录：不设置 ID，时间戳字段传 None
        return XXXEntity(
            # 不设置 id
            name=dto.name,
            # ... 其他字段
            created_at=dto.created_at if dto.created_at > 0 else None,
            updated_at=dto.updated_at if dto.updated_at > 0 else None,
        )
    else:
        # 更新已有记录：包含所有字段
        return XXXEntity(
            id=dto.id,
            name=dto.name,
            # ... 其他字段
            created_at=dto.created_at,
            updated_at=dto.updated_at,
        )
```

**修改的 Repository：**
- ProjectRepository ✓
- ConversationRepository ✓
- MessageRepository ✓（特殊处理 status 枚举）
- MediaRepository ✓
- OutlineRepository ✓
- OutlineHistoryRepository ✓
- ScriptRepository ✓
- SceneRepository ✓
- ScriptHistoryRepository ✓
- ShotRepository ✓
- ShotHistoryRepository ✓
- CharacterRepository ✓
- CharacterHistoryRepository ✓
- ActiveTaskRepository ✓（使用 dict 而非 dataclass）

#### 3.3 所有 Repository 的 `_to_dto()` 方法

**确保包含 `updated_at` 字段：**
```python
def _to_dto(self, entity: XXXEntity) -> XXX:
    """Entity → DTO 转换。"""
    return XXX(
        id=entity.id,
        # ... 其他字段
        created_at=entity.created_at,
        updated_at=entity.updated_at,  # 确保包含
    )
```

### 4. 时间工具类 (`utils/time_utils.py`)

**新增工具函数：**
```python
import time
from datetime import datetime

def now_ms() -> int:
    """获取当前 13 位毫秒时间戳。"""
    return int(time.time() * 1000)

def ms_to_datetime(ms: int) -> datetime:
    """毫秒时间戳转 datetime（用于 UI 显示）。"""
    return datetime.fromtimestamp(ms / 1000.0)
```

## 测试结果

### 综合测试（2026-07-23）

测试项目：
1. ✅ Project 创建：ID 自动生成，created_at 和 updated_at 为 13 位毫秒时间戳
2. ✅ Conversation 创建：ID 自动生成，created_at 和 updated_at 为 13 位毫秒时间戳
3. ✅ Message 创建：ID 自动生成，created_at 和 updated_at 为 13 位毫秒时间戳
4. ✅ MediaFile 创建：ID 自动生成，created_at 和 updated_at 为 13 位毫秒时间戳

**结论：** 所有测试通过 ✓

## 数据库表结构

### 最终表结构

所有表（除 `active_tasks` 和 `characters` 外）：
- **主键：** `id` (BIGINT, PRIMARY KEY, AUTOINCREMENT)
- **时间戳：** `created_at` (BIGINT, NOT NULL), `updated_at` (BIGINT, NOT NULL)

特殊表：
- **active_tasks：** `task_id` (VARCHAR(100), PRIMARY KEY) - 保留业务键
- **characters：** `id` (INTEGER, PRIMARY KEY, AUTOINCREMENT) - 使用 INTEGER

### 表列表（14 张表）

1. projects
2. conversations
3. messages
4. active_tasks
5. media_files
6. outlines
7. outline_history
8. scripts
9. scenes
10. script_history
11. shots
12. shot_history
13. characters
14. character_history

## 使用指南

### 创建新记录

```python
from storage.orm.base import get_session
from storage.repositories.project import ProjectRepository
from models.data_models import Project

session = get_session()
repo = ProjectRepository(session)

# 创建项目（ID 和时间戳自动填充）
project = Project(
    id=0,  # 传 0，数据库自动分配
    name='New Project',
    resolution='1080P',
    aspect_ratio='16:9',
    created_at=0,  # 传 0，ORM 自动填充
    updated_at=0,  # 传 0，ORM 自动填充
    cover_image=''
)

result = repo.create(project)
print(f'Created project with ID: {result.id}')
print(f'Created at: {result.created_at}')  # 13 位毫秒时间戳
```

### UI 层显示时间

```python
from utils.time_utils import ms_to_datetime

# 将毫秒时间戳转换为 datetime 用于显示
dt = ms_to_datetime(project.created_at)
label.setText(dt.strftime("%Y-%m-%d %H:%M:%S"))
```

## 关键优势

1. **自动化：** 时间戳由 ORM 事件监听器自动填充，无需在 Service/Repository 层硬编码
2. **一致性：** 所有表统一使用 64 位整数 ID 和毫秒时间戳
3. **类型安全：** 使用 `Optional[int]` 类型，避免 SQLAlchemy 约束冲突
4. **解耦：** 时间戳逻辑集中在 ORM 层，符合关注点分离原则

## 注意事项

1. **旧数据库：** 本次迁移删除了旧数据库，适用于开发阶段。生产环境需保留数据时，需编写 Alembic 迁移脚本
2. **ID 传值：** 创建新记录时传 `id=0`，更新已有记录时传实际 ID
3. **时间戳传值：** 创建新记录时传 `created_at=0, updated_at=0`，让 ORM 自动填充
4. **Flush 时机：** Repository 的 `create()` 方法先 `flush()` 再 `commit()`，确保 ID 和时间戳在事务内生成

## 相关文件

- `storage/orm/base.py` - ORM 基础设施和事件监听器
- `storage/orm/models.py` - Entity 模型定义
- `storage/repositories/*.py` - Repository 层实现
- `utils/time_utils.py` - 时间工具函数
- `models/data_models.py` - DTO 数据模型（未修改，继续使用 int 类型）
