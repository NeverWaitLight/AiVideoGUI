"""SQLite 数据库管理。"""

import logging
import sqlite3
from datetime import datetime

from models.data_models import Conversation, MediaFile, MediaType, Message, MessageStatus

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
