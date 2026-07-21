"""SQLite 数据库管理。"""

import logging
import sqlite3
from datetime import datetime

from models.data_models import (
    Conversation,
    MediaFile,
    MediaType,
    Message,
    MessageStatus,
    Outline,
    OutlineHistory,
    Script,
    ScriptHistory,
    Scene,
    SceneLocation,
    SceneTime,
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    """SQLite 对话/消息/任务持久化。"""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_tables()
        self._migrate_schema()

    def _migrate_schema(self) -> None:
        """增量迁移：为已有表补充缺失列。"""
        self._migrate_messages()
        self._migrate_media_files()
        self._migrate_conversations()
        self._migrate_projects()
        self._migrate_outlines()
        self._migrate_scripts()

    def _migrate_messages(self) -> None:
        """迁移 messages 表。"""
        cols = {row["name"] for row in self._conn.execute("PRAGMA table_info(messages)").fetchall()}
        if "error_message" not in cols:
            self._conn.execute(
                "ALTER TABLE messages ADD COLUMN error_message TEXT NOT NULL DEFAULT ''"
            )
            self._conn.commit()
            logger.info("迁移：messages 表新增 error_message 列")

    def _migrate_media_files(self) -> None:
        """迁移 media_files 表：添加视频元数据列。"""
        media_cols = {
            row["name"] for row in self._conn.execute("PRAGMA table_info(media_files)").fetchall()
        }
        migrations = []
        if "thumbnail_path" not in media_cols:
            migrations.append("ALTER TABLE media_files ADD COLUMN thumbnail_path TEXT NOT NULL DEFAULT ''")
        if "duration" not in media_cols:
            migrations.append("ALTER TABLE media_files ADD COLUMN duration REAL NOT NULL DEFAULT 0.0")
        if "width" not in media_cols:
            migrations.append("ALTER TABLE media_files ADD COLUMN width INTEGER NOT NULL DEFAULT 0")
        if "height" not in media_cols:
            migrations.append("ALTER TABLE media_files ADD COLUMN height INTEGER NOT NULL DEFAULT 0")

        if migrations:
            for sql in migrations:
                self._conn.execute(sql)
            self._conn.commit()
            logger.info("迁移：media_files 表新增视频元数据列（thumbnail_path, duration, width, height）")

    def _migrate_conversations(self) -> None:
        """迁移 conversations 表：添加 project_id 列。"""
        conv_cols = {row["name"] for row in self._conn.execute("PRAGMA table_info(conversations)").fetchall()}
        if "project_id" not in conv_cols:
            self._conn.execute(
                "ALTER TABLE conversations ADD COLUMN project_id TEXT NOT NULL DEFAULT ''"
            )
            self._conn.commit()
            logger.info("迁移：conversations 表新增 project_id 列")

        # 创建索引（在列存在后）
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_conversations_project ON conversations(project_id)"
        )
        self._conn.commit()

    def _migrate_projects(self) -> None:
        """迁移 projects 表：添加 cover_image 列。"""
        project_cols = {row["name"] for row in self._conn.execute("PRAGMA table_info(projects)").fetchall()}
        if "cover_image" not in project_cols:
            self._conn.execute(
                "ALTER TABLE projects ADD COLUMN cover_image TEXT NOT NULL DEFAULT ''"
            )
            self._conn.commit()
            logger.info("迁移：projects 表新增 cover_image 列")

    def _migrate_outlines(self) -> None:
        """迁移 outlines 表：确保表存在。"""
        # 检查表是否存在
        result = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='outlines'"
        ).fetchone()
        if not result:
            # 表不存在，通过 _init_tables 创建（此时表应该已由 _init_tables 创建）
            logger.info("outlines 表已由初始化创建")

        # 检查 outline_history 表
        result = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='outline_history'"
        ).fetchone()
        if not result:
            logger.info("outline_history 表已由初始化创建")

    def _migrate_scripts(self) -> None:
        """迁移 scripts 表：新增 title 列和 scenes 表。"""
        result = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='scripts'"
        ).fetchone()
        if not result:
            logger.info("scripts 表已由初始化创建")
            return

        # 检查 scripts 表是否有 title 列
        script_cols = {row["name"] for row in self._conn.execute("PRAGMA table_info(scripts)").fetchall()}
        if "title" not in script_cols:
            # 旧表结构，需要迁移
            logger.info("开始迁移 scripts 表结构")

            # 1. 重命名旧表
            self._conn.execute("ALTER TABLE scripts RENAME TO scripts_old")

            # 2. 创建新的 scripts 表和 scenes 表
            self._conn.executescript("""
                CREATE TABLE scripts (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    title TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_script_project ON scripts(project_id);

                CREATE TABLE scenes (
                    id TEXT PRIMARY KEY,
                    script_id TEXT NOT NULL,
                    scene_number INTEGER NOT NULL,
                    location_type TEXT NOT NULL,
                    location TEXT NOT NULL,
                    time_type TEXT NOT NULL,
                    time_detail TEXT NOT NULL DEFAULT '',
                    content TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_scene_script ON scenes(script_id, scene_number);
            """)

            # 3. 迁移数据：将旧的 content 放入第一个场次
            old_scripts = self._conn.execute(
                "SELECT id, project_id, content, created_at, updated_at FROM scripts_old"
            ).fetchall()

            for old_script in old_scripts:
                # 插入新 script 记录
                self._conn.execute(
                    "INSERT INTO scripts (id, project_id, title, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (old_script["id"], old_script["project_id"], "",
                     old_script["created_at"], old_script["updated_at"])
                )

                # 如果有内容，创建一个默认场次
                if old_script["content"]:
                    import uuid
                    scene_id = str(uuid.uuid4())
                    self._conn.execute(
                        "INSERT INTO scenes (id, script_id, scene_number, location_type, "
                        "location, time_type, time_detail, content, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                        (scene_id, old_script["id"], 1, "interior", "未指定", "day", "",
                         old_script["content"], old_script["created_at"], old_script["updated_at"])
                    )

            # 4. 删除旧表
            self._conn.execute("DROP TABLE scripts_old")

            self._conn.commit()
            logger.info("scripts 表迁移完成")

        # 5. 迁移 script_history 表（独立于 scripts 表迁移）
        history_result = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='script_history'"
        ).fetchone()

        if history_result:
            history_cols = {row["name"] for row in self._conn.execute("PRAGMA table_info(script_history)").fetchall()}
            if "content" in history_cols and "scenes_snapshot" not in history_cols:
                # 旧历史表结构，需要迁移
                logger.info("开始迁移 script_history 表结构")
                self._conn.execute("ALTER TABLE script_history RENAME TO script_history_old")
                self._conn.executescript("""
                    CREATE TABLE script_history (
                        id TEXT PRIMARY KEY,
                        script_id TEXT NOT NULL,
                        title TEXT NOT NULL DEFAULT '',
                        scenes_snapshot TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE CASCADE
                    );
                    CREATE INDEX IF NOT EXISTS idx_history_script ON script_history(script_id, created_at DESC);
                """)

                # 迁移历史数据：将 content 包装成 JSON 快照
                import json
                old_histories = self._conn.execute(
                    "SELECT id, script_id, content, created_at FROM script_history_old"
                ).fetchall()

                for old_history in old_histories:
                    # 将旧的 content 包装成一个场次的 JSON 数组
                    scenes_data = [{
                        "scene_number": 1,
                        "location_type": "interior",
                        "location": "未指定",
                        "time_type": "day",
                        "time_detail": "",
                        "content": old_history["content"]
                    }]
                    self._conn.execute(
                        "INSERT INTO script_history (id, script_id, title, scenes_snapshot, created_at) "
                        "VALUES (?, ?, ?, ?, ?)",
                        (old_history["id"], old_history["script_id"], "",
                         json.dumps(scenes_data, ensure_ascii=False), old_history["created_at"])
                    )

                self._conn.execute("DROP TABLE script_history_old")
                self._conn.commit()
                logger.info("script_history 表迁移完成")

        # 确保 scenes 表存在
        result = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='scenes'"
        ).fetchone()
        if not result:
            logger.info("scenes 表已由初始化创建")

    def _init_tables(self) -> None:
        cur = self._conn.cursor()
        cur.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                resolution TEXT NOT NULL DEFAULT '1280x720',
                aspect_ratio TEXT NOT NULL DEFAULT '16:9',
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS conversations (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                created_at TEXT NOT NULL,
                model_name TEXT NOT NULL DEFAULT '',
                provider_name TEXT NOT NULL DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                task_id TEXT NOT NULL DEFAULT '',
                video_url TEXT NOT NULL DEFAULT '',
                local_path TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'generating',
                error_message TEXT NOT NULL DEFAULT '',
                FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_messages_conversation
                ON messages(conversation_id, created_at);
            CREATE TABLE IF NOT EXISTS active_tasks (
                task_id TEXT PRIMARY KEY,
                message_id TEXT NOT NULL,
                provider_name TEXT NOT NULL,
                model_name TEXT NOT NULL DEFAULT '',
                video_url TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TEXT NOT NULL,
                FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
            );
            CREATE TABLE IF NOT EXISTS media_files (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                media_type TEXT NOT NULL,
                local_path TEXT NOT NULL,
                file_size INTEGER NOT NULL DEFAULT 0,
                source TEXT NOT NULL DEFAULT 'task',
                conversation_id TEXT NOT NULL DEFAULT '',
                message_id TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_media_type ON media_files(media_type);
            CREATE INDEX IF NOT EXISTS idx_media_created ON media_files(created_at DESC);
            CREATE TABLE IF NOT EXISTS outlines (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                content TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_outline_project ON outlines(project_id);
            CREATE TABLE IF NOT EXISTS outline_history (
                id TEXT PRIMARY KEY,
                outline_id TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (outline_id) REFERENCES outlines(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_history_outline ON outline_history(outline_id, created_at DESC);
            CREATE TABLE IF NOT EXISTS scripts (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_script_project ON scripts(project_id);
            CREATE TABLE IF NOT EXISTS scenes (
                id TEXT PRIMARY KEY,
                script_id TEXT NOT NULL,
                scene_number INTEGER NOT NULL,
                location_type TEXT NOT NULL,
                location TEXT NOT NULL,
                time_type TEXT NOT NULL,
                time_detail TEXT NOT NULL DEFAULT '',
                content TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_scene_script ON scenes(script_id, scene_number);
            CREATE TABLE IF NOT EXISTS script_history (
                id TEXT PRIMARY KEY,
                script_id TEXT NOT NULL,
                title TEXT NOT NULL DEFAULT '',
                scenes_snapshot TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (script_id) REFERENCES scripts(id) ON DELETE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_history_script ON script_history(script_id, created_at DESC);
            """
        )
        self._conn.commit()
        logger.info("数据库初始化完成：%s", self._db_path)

    # ---------- conversation ----------

    def create_conversation(self, conv: Conversation) -> None:
        self._conn.execute(
            "INSERT INTO conversations (id, title, created_at, model_name, provider_name, project_id) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (conv.id, conv.title, conv.created_at.isoformat(), conv.model_name, conv.provider_name, conv.project_id),
        )
        self._conn.commit()

    def list_conversations(self) -> list[Conversation]:
        rows = self._conn.execute(
            "SELECT id, title, created_at, model_name, provider_name, project_id "
            "FROM conversations ORDER BY created_at DESC"
        ).fetchall()
        return [
            Conversation(
                id=r["id"],
                title=r["title"],
                created_at=datetime.fromisoformat(r["created_at"]),
                model_name=r["model_name"],
                provider_name=r["provider_name"],
                project_id=r["project_id"],
            )
            for r in rows
        ]

    def delete_conversation(self, conversation_id: str) -> None:
        # 清除素材库中与该会话的关联，保留视频文件和记录
        self._conn.execute(
            "UPDATE media_files SET conversation_id = '', message_id = '' "
            "WHERE conversation_id = ?",
            (conversation_id,),
        )
        self._conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
        self._conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        self._conn.commit()

    def update_conversation_title(self, conversation_id: str, title: str) -> None:
        self._conn.execute(
            "UPDATE conversations SET title = ? WHERE id = ?", (title, conversation_id)
        )
        self._conn.commit()

    # ---------- message ----------

    def add_message(self, msg: Message) -> None:
        self._conn.execute(
            "INSERT INTO messages "
            "(id, conversation_id, role, content, created_at, task_id, video_url, "
            "local_path, status, error_message) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                msg.id,
                msg.conversation_id,
                msg.role,
                msg.content,
                msg.created_at.isoformat(),
                msg.task_id,
                msg.video_url,
                msg.local_path,
                msg.status.value,
                msg.error_message,
            ),
        )
        self._conn.commit()

    def get_message(self, message_id: str) -> Message | None:
        row = self._conn.execute(
            "SELECT id, conversation_id, role, content, created_at, "
            "task_id, video_url, local_path, status, error_message "
            "FROM messages WHERE id = ?",
            (message_id,),
        ).fetchone()
        if not row:
            return None
        return Message(
            id=row["id"],
            conversation_id=row["conversation_id"],
            role=row["role"],
            content=row["content"],
            created_at=datetime.fromisoformat(row["created_at"]),
            task_id=row["task_id"],
            video_url=row["video_url"],
            local_path=row["local_path"],
            status=MessageStatus(row["status"]),
            error_message=row["error_message"],
        )

    def list_messages(self, conversation_id: str) -> list[Message]:
        rows = self._conn.execute(
            "SELECT id, conversation_id, role, content, created_at, "
            "task_id, video_url, local_path, status, error_message "
            "FROM messages WHERE conversation_id = ? ORDER BY created_at",
            (conversation_id,),
        ).fetchall()
        return [
            Message(
                id=r["id"],
                conversation_id=r["conversation_id"],
                role=r["role"],
                content=r["content"],
                created_at=datetime.fromisoformat(r["created_at"]),
                task_id=r["task_id"],
                video_url=r["video_url"],
                local_path=r["local_path"],
                status=MessageStatus(r["status"]),
                error_message=r["error_message"],
            )
            for r in rows
        ]

    def update_message_status(
        self,
        message_id: str,
        status: MessageStatus,
        *,
        task_id: str = "",
        video_url: str = "",
        local_path: str = "",
        error_message: str | None = None,
    ) -> None:
        sets = ["status = ?"]
        vals: list = [status.value]
        if task_id:
            sets.append("task_id = ?")
            vals.append(task_id)
        if video_url:
            sets.append("video_url = ?")
            vals.append(video_url)
        if local_path:
            sets.append("local_path = ?")
            vals.append(local_path)
        if error_message is not None:
            sets.append("error_message = ?")
            vals.append(error_message)
        vals.append(message_id)
        self._conn.execute(
            f"UPDATE messages SET {', '.join(sets)} WHERE id = ?", vals
        )
        self._conn.commit()

    # ---------- active_tasks ----------

    def add_active_task(
        self, task_id: str, message_id: str, provider_name: str, model_name: str
    ) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO active_tasks "
            "(task_id, message_id, provider_name, model_name, status, created_at) "
            "VALUES (?, ?, ?, ?, 'pending', ?)",
            (task_id, message_id, provider_name, model_name, datetime.now().isoformat()),
        )
        self._conn.commit()

    def list_active_tasks(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT task_id, message_id, provider_name, model_name, video_url, status, created_at "
            "FROM active_tasks"
        ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            # 将 created_at 从 ISO 字符串转换为 datetime 对象
            d["created_at"] = datetime.fromisoformat(r["created_at"])
            result.append(d)
        return result

    def update_active_task(self, task_id: str, status: str, video_url: str = "") -> None:
        if video_url:
            self._conn.execute(
                "UPDATE active_tasks SET status = ?, video_url = ? WHERE task_id = ?",
                (status, video_url, task_id),
            )
        else:
            self._conn.execute(
                "UPDATE active_tasks SET status = ? WHERE task_id = ?", (status, task_id)
            )
        self._conn.commit()

    def remove_active_task(self, task_id: str) -> None:
        self._conn.execute("DELETE FROM active_tasks WHERE task_id = ?", (task_id,))
        self._conn.commit()

    # ---------- media_files ----------

    def add_media_file(self, media: MediaFile) -> None:
        self._conn.execute(
            "INSERT INTO media_files "
            "(id, filename, media_type, local_path, file_size, source, "
            "conversation_id, message_id, created_at, thumbnail_path, duration, width, height) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                media.id,
                media.filename,
                media.media_type.value,
                media.local_path,
                media.file_size,
                media.source,
                media.conversation_id,
                media.message_id,
                media.created_at.isoformat(),
                media.thumbnail_path,
                media.duration,
                media.width,
                media.height,
            ),
        )
        self._conn.commit()

    def list_media_files(
        self,
        media_type: str | None = None,
        keyword: str | None = None,
        project_id: str | None = None,
    ) -> list[MediaFile]:
        query = (
            "SELECT id, filename, media_type, local_path, file_size, source, "
            "conversation_id, message_id, created_at, thumbnail_path, duration, width, height "
            "FROM media_files WHERE 1=1"
        )
        params: list = []
        if media_type:
            query += " AND media_type = ?"
            params.append(media_type)
        if keyword:
            query += " AND filename LIKE ?"
            params.append(f"%{keyword}%")
        if project_id:
            # 通过 conversation_id 关联到项目
            query += """ AND conversation_id IN (
                SELECT id FROM conversations WHERE project_id = ?
            )"""
            params.append(project_id)
        query += " ORDER BY created_at DESC"
        rows = self._conn.execute(query, params).fetchall()
        return [
            MediaFile(
                id=r["id"],
                filename=r["filename"],
                media_type=MediaType(r["media_type"]),
                local_path=r["local_path"],
                file_size=r["file_size"],
                source=r["source"],
                conversation_id=r["conversation_id"],
                message_id=r["message_id"],
                created_at=datetime.fromisoformat(r["created_at"]),
                thumbnail_path=r["thumbnail_path"],
                duration=r["duration"],
                width=r["width"],
                height=r["height"],
            )
            for r in rows
        ]

    def delete_media_file(self, media_id: str) -> MediaFile | None:
        row = self._conn.execute(
            "SELECT id, filename, media_type, local_path, file_size, source, "
            "conversation_id, message_id, created_at, thumbnail_path, duration, width, height "
            "FROM media_files WHERE id = ?",
            (media_id,),
        ).fetchone()
        if not row:
            return None
        media = MediaFile(
            id=row["id"],
            filename=row["filename"],
            media_type=MediaType(row["media_type"]),
            local_path=row["local_path"],
            file_size=row["file_size"],
            source=row["source"],
            conversation_id=row["conversation_id"],
            message_id=row["message_id"],
            created_at=datetime.fromisoformat(row["created_at"]),
            thumbnail_path=row["thumbnail_path"],
            duration=row["duration"],
            width=row["width"],
            height=row["height"],
        )
        self._conn.execute("DELETE FROM media_files WHERE id = ?", (media_id,))
        self._conn.commit()
        return media

    def get_media_file_by_message(self, message_id: str) -> MediaFile | None:
        row = self._conn.execute(
            "SELECT id FROM media_files WHERE message_id = ?",
            (message_id,),
        ).fetchone()
        if not row:
            return None
        return MediaFile(
            id=row["id"],
            filename="",
            media_type=MediaType.VIDEO,
            local_path="",
        )

    def get_video_metadata_by_message(self, message_id: str) -> dict | None:
        """查询视频素材的元数据（缩略图路径、时长、分辨率）。"""
        row = self._conn.execute(
            "SELECT thumbnail_path, duration, width, height "
            "FROM media_files WHERE message_id = ?",
            (message_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "thumbnail_path": row["thumbnail_path"],
            "duration": row["duration"],
            "width": row["width"],
            "height": row["height"],
        }

    def close(self) -> None:
        self._conn.close()

    # ---------- projects ----------

    def create_project(self, project_id: str, name: str, resolution: str, aspect_ratio: str, cover_image: str = "") -> None:
        self._conn.execute(
            "INSERT INTO projects (id, name, resolution, aspect_ratio, created_at, cover_image) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (project_id, name, resolution, aspect_ratio, datetime.now().isoformat(), cover_image),
        )
        self._conn.commit()

    def list_projects(self) -> list[dict]:
        rows = self._conn.execute(
            "SELECT id, name, resolution, aspect_ratio, created_at, cover_image FROM projects ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]

    def get_project(self, project_id: str) -> dict | None:
        row = self._conn.execute(
            "SELECT id, name, resolution, aspect_ratio, created_at, cover_image FROM projects WHERE id = ?",
            (project_id,),
        ).fetchone()
        return dict(row) if row else None

    def update_project(self, project_id: str, name: str, resolution: str, aspect_ratio: str, cover_image: str = "") -> None:
        self._conn.execute(
            "UPDATE projects SET name = ?, resolution = ?, aspect_ratio = ?, cover_image = ? WHERE id = ?",
            (name, resolution, aspect_ratio, cover_image, project_id),
        )
        self._conn.commit()

    def delete_project(self, project_id: str) -> None:
        # 清除项目关联的对话的 project_id
        self._conn.execute(
            "UPDATE conversations SET project_id = '' WHERE project_id = ?",
            (project_id,),
        )
        self._conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
        self._conn.commit()

    def list_project_conversations(self, project_id: str) -> list[Conversation]:
        rows = self._conn.execute(
            "SELECT id, title, created_at, model_name, provider_name, project_id "
            "FROM conversations WHERE project_id = ? ORDER BY created_at DESC",
            (project_id,),
        ).fetchall()
        return [
            Conversation(
                id=r["id"],
                title=r["title"],
                created_at=datetime.fromisoformat(r["created_at"]),
                model_name=r["model_name"],
                provider_name=r["provider_name"],
                project_id=r["project_id"],
            )
            for r in rows
        ]

    # ---------- outlines ----------

    def get_outline(self, project_id: str) -> Outline | None:
        """获取项目的大纲（一个项目只有一个大纲）。"""
        row = self._conn.execute(
            "SELECT id, project_id, content, created_at, updated_at "
            "FROM outlines WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        if not row:
            return None
        return Outline(
            id=row["id"],
            project_id=row["project_id"],
            content=row["content"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def create_outline(self, outline: Outline) -> None:
        """创建大纲。"""
        self._conn.execute(
            "INSERT INTO outlines (id, project_id, content, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                outline.id,
                outline.project_id,
                outline.content,
                outline.created_at.isoformat(),
                outline.updated_at.isoformat(),
            ),
        )
        self._conn.commit()

    def update_outline(self, outline_id: str, content: str) -> None:
        """更新大纲内容，并自动保存历史版本。"""
        # 获取旧内容保存到历史
        old_row = self._conn.execute(
            "SELECT content FROM outlines WHERE id = ?", (outline_id,)
        ).fetchone()
        if old_row and old_row["content"]:
            # 生成历史记录 ID
            import uuid
            history_id = str(uuid.uuid4())
            self._conn.execute(
                "INSERT INTO outline_history (id, outline_id, content, created_at) "
                "VALUES (?, ?, ?, ?)",
                (history_id, outline_id, old_row["content"], datetime.now().isoformat()),
            )

        # 更新大纲
        self._conn.execute(
            "UPDATE outlines SET content = ?, updated_at = ? WHERE id = ?",
            (content, datetime.now().isoformat(), outline_id),
        )
        self._conn.commit()

    def list_outline_history(self, outline_id: str) -> list[OutlineHistory]:
        """获取大纲的历史版本列表。"""
        rows = self._conn.execute(
            "SELECT id, outline_id, content, created_at "
            "FROM outline_history WHERE outline_id = ? ORDER BY created_at DESC",
            (outline_id,),
        ).fetchall()
        return [
            OutlineHistory(
                id=r["id"],
                outline_id=r["outline_id"],
                content=r["content"],
                created_at=datetime.fromisoformat(r["created_at"]),
            )
            for r in rows
        ]

    def restore_outline_from_history(self, outline_id: str, history_id: str) -> None:
        """从历史版本恢复大纲。"""
        # 获取历史版本内容
        history_row = self._conn.execute(
            "SELECT content FROM outline_history WHERE id = ?", (history_id,)
        ).fetchone()
        if not history_row:
            return

        # 先保存当前版本到历史
        current_row = self._conn.execute(
            "SELECT content FROM outlines WHERE id = ?", (outline_id,)
        ).fetchone()
        if current_row:
            import uuid
            new_history_id = str(uuid.uuid4())
            self._conn.execute(
                "INSERT INTO outline_history (id, outline_id, content, created_at) "
                "VALUES (?, ?, ?, ?)",
                (new_history_id, outline_id, current_row["content"], datetime.now().isoformat()),
            )

        # 恢复历史版本
        self._conn.execute(
            "UPDATE outlines SET content = ?, updated_at = ? WHERE id = ?",
            (history_row["content"], datetime.now().isoformat(), outline_id),
        )
        self._conn.commit()

    # ---------- scripts ----------

    def get_script(self, project_id: str) -> Script | None:
        """获取项目的剧本（一个项目只有一个剧本）。"""
        row = self._conn.execute(
            "SELECT id, project_id, title, created_at, updated_at "
            "FROM scripts WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        if not row:
            return None
        return Script(
            id=row["id"],
            project_id=row["project_id"],
            title=row["title"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def create_script(self, script: Script) -> None:
        """创建剧本。"""
        self._conn.execute(
            "INSERT INTO scripts (id, project_id, title, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                script.id,
                script.project_id,
                script.title,
                script.created_at.isoformat(),
                script.updated_at.isoformat(),
            ),
        )
        self._conn.commit()

    def update_script(self, script_id: str, title: str) -> None:
        """更新剧本标题。"""
        self._conn.execute(
            "UPDATE scripts SET title = ?, updated_at = ? WHERE id = ?",
            (title, datetime.now().isoformat(), script_id),
        )
        self._conn.commit()

    # ---------- scenes ----------

    def list_scenes(self, script_id: str) -> list[Scene]:
        """获取剧本的所有场次，按场次号排序。"""
        rows = self._conn.execute(
            "SELECT id, script_id, scene_number, location_type, location, time_type, "
            "time_detail, content, created_at, updated_at "
            "FROM scenes WHERE script_id = ? ORDER BY scene_number",
            (script_id,),
        ).fetchall()
        return [
            Scene(
                id=r["id"],
                script_id=r["script_id"],
                scene_number=r["scene_number"],
                location_type=SceneLocation(r["location_type"]),
                location=r["location"],
                time_type=SceneTime(r["time_type"]),
                time_detail=r["time_detail"],
                content=r["content"],
                created_at=datetime.fromisoformat(r["created_at"]),
                updated_at=datetime.fromisoformat(r["updated_at"]),
            )
            for r in rows
        ]

    def get_scene(self, scene_id: str) -> Scene | None:
        """获取单个场次。"""
        row = self._conn.execute(
            "SELECT id, script_id, scene_number, location_type, location, time_type, "
            "time_detail, content, created_at, updated_at "
            "FROM scenes WHERE id = ?",
            (scene_id,),
        ).fetchone()
        if not row:
            return None
        return Scene(
            id=row["id"],
            script_id=row["script_id"],
            scene_number=row["scene_number"],
            location_type=SceneLocation(row["location_type"]),
            location=row["location"],
            time_type=SceneTime(row["time_type"]),
            time_detail=row["time_detail"],
            content=row["content"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def create_scene(self, scene: Scene) -> None:
        """创建场次。"""
        self._conn.execute(
            "INSERT INTO scenes (id, script_id, scene_number, location_type, location, "
            "time_type, time_detail, content, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                scene.id,
                scene.script_id,
                scene.scene_number,
                scene.location_type.value,
                scene.location,
                scene.time_type.value,
                scene.time_detail,
                scene.content,
                scene.created_at.isoformat(),
                scene.updated_at.isoformat(),
            ),
        )
        self._conn.commit()

    def update_scene(
        self,
        scene_id: str,
        location_type: SceneLocation | None = None,
        location: str | None = None,
        time_type: SceneTime | None = None,
        time_detail: str | None = None,
        content: str | None = None,
    ) -> None:
        """更新场次信息。"""
        updates = []
        params = []

        if location_type is not None:
            updates.append("location_type = ?")
            params.append(location_type.value)
        if location is not None:
            updates.append("location = ?")
            params.append(location)
        if time_type is not None:
            updates.append("time_type = ?")
            params.append(time_type.value)
        if time_detail is not None:
            updates.append("time_detail = ?")
            params.append(time_detail)
        if content is not None:
            updates.append("content = ?")
            params.append(content)

        if not updates:
            return

        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(scene_id)

        sql = f"UPDATE scenes SET {', '.join(updates)} WHERE id = ?"
        self._conn.execute(sql, params)
        self._conn.commit()

    def delete_scene(self, scene_id: str) -> None:
        """删除场次。"""
        self._conn.execute("DELETE FROM scenes WHERE id = ?", (scene_id,))
        self._conn.commit()

    def create_script_history(self, script_id: str, title: str, scenes: list[Scene]) -> None:
        """创建剧本历史快照（包含所有场次数据）。"""
        import json
        import uuid

        # 将场次列表序列化为 JSON
        scenes_data = [
            {
                "scene_number": s.scene_number,
                "location_type": s.location_type.value,
                "location": s.location,
                "time_type": s.time_type.value,
                "time_detail": s.time_detail,
                "content": s.content,
            }
            for s in scenes
        ]

        history_id = str(uuid.uuid4())
        self._conn.execute(
            "INSERT INTO script_history (id, script_id, title, scenes_snapshot, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                history_id,
                script_id,
                title,
                json.dumps(scenes_data, ensure_ascii=False),
                datetime.now().isoformat(),
            ),
        )
        self._conn.commit()

    def list_script_history(self, script_id: str) -> list[ScriptHistory]:
        """获取剧本的历史版本列表。"""
        rows = self._conn.execute(
            "SELECT id, script_id, title, scenes_snapshot, created_at "
            "FROM script_history WHERE script_id = ? ORDER BY created_at DESC",
            (script_id,),
        ).fetchall()
        return [
            ScriptHistory(
                id=r["id"],
                script_id=r["script_id"],
                title=r["title"],
                scenes_snapshot=r["scenes_snapshot"],
                created_at=datetime.fromisoformat(r["created_at"]),
            )
            for r in rows
        ]

    def restore_script_from_history(self, script_id: str, history_id: str) -> None:
        """从历史版本恢复剧本（包括所有场次）。"""
        import json
        import uuid

        # 获取历史版本数据
        history_row = self._conn.execute(
            "SELECT title, scenes_snapshot FROM script_history WHERE id = ?", (history_id,)
        ).fetchone()
        if not history_row:
            return

        # 先保存当前版本到历史
        current_script = self._conn.execute(
            "SELECT title FROM scripts WHERE id = ?", (script_id,)
        ).fetchone()
        current_scenes = self.list_scenes(script_id)
        if current_script:
            self.create_script_history(script_id, current_script["title"], current_scenes)

        # 恢复标题
        self._conn.execute(
            "UPDATE scripts SET title = ?, updated_at = ? WHERE id = ?",
            (history_row["title"], datetime.now().isoformat(), script_id),
        )

        # 删除当前所有场次
        self._conn.execute("DELETE FROM scenes WHERE script_id = ?", (script_id,))

        # 恢复历史场次
        scenes_data = json.loads(history_row["scenes_snapshot"])
        now = datetime.now().isoformat()
        for scene_data in scenes_data:
            scene_id = str(uuid.uuid4())
            self._conn.execute(
                "INSERT INTO scenes (id, script_id, scene_number, location_type, location, "
                "time_type, time_detail, content, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    scene_id,
                    script_id,
                    scene_data["scene_number"],
                    scene_data["location_type"],
                    scene_data["location"],
                    scene_data["time_type"],
                    scene_data.get("time_detail", ""),
                    scene_data["content"],
                    now,
                    now,
                ),
            )

        self._conn.commit()
