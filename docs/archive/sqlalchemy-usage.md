# SQLAlchemy 2.X ORM 使用指南

## 快速开始

### 1. 运行应用

```bash
uv run python main.py
```

应用已成功迁移到 SQLAlchemy 2.X ORM，所有功能保持不变。

## 开发指南

### 添加新表

**步骤 1：定义 ORM 模型**

在 `storage/orm/` 中创建新的 entity 文件（如 `new_entity.py`）：

```python
class NewEntity(Base):
    """新表描述。"""
    
    __tablename__ = "new_table"
    
    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    
    # 关系定义
    parent_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("parent_table.id", ondelete="CASCADE"), nullable=False
    )
    parent: Mapped["ParentEntity"] = relationship(back_populates="children")
    
    # 索引
    __table_args__ = (
        Index("idx_new_table_parent", "parent_id"),
    )
```

**步骤 2：创建对应的 dataclass**

在 `models/data_models.py` 中添加 DTO：

```python
@dataclass
class NewModel:
    id: str
    name: str
    created_at: datetime
```

**步骤 3：创建 Repository**

在 `storage/repositories/` 中创建新文件：

```python
from storage.repositories.base import BaseRepository
from storage.orm.new_entity import NewEntity
from models.new_model import NewModel

class NewRepository(BaseRepository[NewEntity, NewModel]):
    def __init__(self, session: Session):
        super().__init__(session, NewEntity)
    
    def _to_dto(self, entity: NewEntity) -> NewModel:
        return NewModel(
            id=entity.id,
            name=entity.name,
            created_at=entity.created_at,
        )
    
    def _to_entity(self, dto: NewModel) -> NewEntity:
        return NewEntity(
            id=dto.id,
            name=dto.name,
            created_at=dto.created_at,
        )
```

**步骤 4：在 DatabaseManager 中添加方法**

在 `storage/database.py` 中添加：

```python
def create_new_record(self, model: NewModel) -> None:
    with self._lock:
        session = self._get_session()
        repo = NewRepository(session)
        repo.create(model)

def list_new_records(self) -> list[NewModel]:
    session = self._get_session()
    repo = NewRepository(session)
    return repo.list_all()
```

**步骤 5：生成数据库迁移**

```bash
uv run alembic revision --autogenerate -m "Add new_table"
uv run alembic upgrade head
```

### 修改现有表

**步骤 1：修改 ORM 模型**

在相应的 entity 文件（如 `storage/orm/existing_entity.py`）中修改实体定义：

```python
class ExistingEntity(Base):
    # 添加新列
    new_column: Mapped[str] = mapped_column(String(100), nullable=False, default="")
```

**步骤 2：修改对应的 dataclass**

在 `models/data_models.py` 中更新：

```python
@dataclass
class ExistingModel:
    # 添加新字段
    new_field: str = ""
```

**步骤 3：更新 Repository 的转换方法**

```python
def _to_dto(self, entity: ExistingEntity) -> ExistingModel:
    return ExistingModel(
        # ... 其他字段
        new_field=entity.new_column,
    )
```

**步骤 4：生成并应用迁移**

```bash
uv run alembic revision --autogenerate -m "Add new_column to existing_table"
uv run alembic upgrade head
```

## 常见操作示例

### 1. 简单查询

```python
# 在 Repository 中
def get_by_name(self, name: str) -> Optional[DTOType]:
    stmt = select(self.entity_class).where(self.entity_class.name == name)
    entity = self.session.execute(stmt).scalar_one_or_none()
    return self._to_dto(entity) if entity else None
```

### 2. 复杂查询（JOIN）

```python
def list_with_parent(self, parent_id: str) -> List[DTOType]:
    stmt = (
        select(ChildEntity)
        .join(ParentEntity, ChildEntity.parent_id == ParentEntity.id)
        .where(ParentEntity.id == parent_id)
        .order_by(ChildEntity.created_at.desc())
    )
    entities = self.session.execute(stmt).scalars().all()
    return [self._to_dto(e) for e in entities]
```

### 3. 预加载关联数据（避免 N+1）

```python
from sqlalchemy.orm import joinedload

stmt = (
    select(ParentEntity)
    .options(joinedload(ParentEntity.children))
    .where(ParentEntity.id == parent_id)
)
entity = self.session.execute(stmt).scalar_one_or_none()
```

### 4. 批量操作

```python
def batch_create(self, dtos: List[DTOType]) -> None:
    entities = [self._to_entity(dto) for dto in dtos]
    self.session.bulk_save_objects(entities)
    self.session.commit()
```

### 5. 事务处理

```python
def complex_operation(self):
    try:
        # 操作 1
        self.session.add(entity1)
        
        # 操作 2
        self.session.add(entity2)
        
        # 提交事务
        self.session.commit()
    except Exception as e:
        # 回滚事务
        self.session.rollback()
        raise
```

## 数据库迁移管理

### 查看迁移历史

```bash
uv run alembic history
```

### 查看当前版本

```bash
uv run alembic current
```

### 升级到最新版本

```bash
uv run alembic upgrade head
```

### 回滚到上一个版本

```bash
uv run alembic downgrade -1
```

### 回滚到特定版本

```bash
uv run alembic downgrade <revision_id>
```

## 性能优化技巧

### 1. 使用 joinedload 预加载

```python
# 避免 N+1 查询
stmt = (
    select(ProjectEntity)
    .options(
        joinedload(ProjectEntity.conversations),
        joinedload(ProjectEntity.scripts)
    )
)
```

### 2. 使用 selectinload 处理大量关联

```python
from sqlalchemy.orm import selectinload

# 适用于一对多关系且数据量大的情况
stmt = (
    select(ProjectEntity)
    .options(selectinload(ProjectEntity.conversations))
)
```

### 3. 只查询需要的列

```python
# 不加载整个对象，只查询特定列
stmt = select(ConversationEntity.id, ConversationEntity.title)
results = self.session.execute(stmt).all()
```

### 4. 批量操作使用 bulk_*

```python
# 批量插入（跳过 ORM 事件，速度更快）
self.session.bulk_insert_mappings(Entity, [
    {"id": "1", "name": "A"},
    {"id": "2", "name": "B"},
])
```

## 调试技巧

### 1. 打印生成的 SQL

```python
# 在 init_engine 时启用 echo
init_engine(database_url, echo=True)
```

### 2. 查看 Session 状态

```python
# 查看待提交的对象
print(session.new)
print(session.dirty)
print(session.deleted)
```

### 3. 使用 SQL 日志

```python
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

## 常见问题

### Q1: 如何处理现有数据库？

A: SQLAlchemy 会自动使用现有表。第一次运行时，ORM 会验证表结构是否与模型定义匹配。如果不匹配，使用 Alembic 生成迁移脚本。

### Q2: 如何处理多线程？

A: 已配置 `scoped_session`，每个线程自动获取独立 Session。在线程结束时调用 `close_session()` 释放资源。

### Q3: 如何回滚到旧的 sqlite3 实现？

A: 将 `storage/database_old.py` 重命名为 `storage/database.py` 即可回滚。

### Q4: 性能是否受影响？

A: ORM 有轻微开销，但可以通过以下方式优化：
- 使用 `joinedload` 避免 N+1 查询
- 使用 `bulk_*` 方法进行批量操作
- 合理使用索引

### Q5: 如何处理日期时间？

A: SQLAlchemy 自动处理 `datetime` 对象，无需手动转换。数据库中的 ISO 字符串会自动转换为 Python `datetime` 对象。

## 最佳实践

1. **始终使用 Repository 层** - 不要在服务层直接使用 ORM 实体
2. **保持 DTO 和 Entity 分离** - dataclass 用于业务逻辑，Entity 用于数据库操作
3. **使用类型提示** - 利用 `Mapped[类型]` 提供编译时检查
4. **合理使用事务** - 复杂操作使用显式事务控制
5. **定期清理 Session** - 避免内存泄漏
6. **测试迁移脚本** - 在测试环境验证后再应用到生产环境

## 相关资源

- [SQLAlchemy 2.0 文档](https://docs.sqlalchemy.org/en/20/)
- [Alembic 文档](https://alembic.sqlalchemy.org/)
- 项目迁移文档：`SQLALCHEMY_MIGRATION.md`
