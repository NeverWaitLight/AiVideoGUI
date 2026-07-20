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
        self._migrate()

    def _migrate(self) -> None:
        """增量迁移：为已有表补充缺失列。"""
        cols = {row["name"] for row in self._conn.execute("PRAGMA table_info(messages)").fetchall()}
        if "error_message" not in cols:
            self._conn.execute(
                "ALTER TABLE messages ADD COLUMN error_message TEXT NOT NULL DEFAULT ''"
            )
            self._conn.commit()
            logger.info("迁移：messages 表新增 error_message 列")

    def _init_tables(self) -> None:
        cur = self._conn.cursor()
        cur.executescript(
            """
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
            "INSERT INTO conversations (id, title, created_at, model_name, provider_name) "
            "VALUES (?, ?, ?, ?, ?)",
            (conv.id, conv.title, conv.created_at.isoformat(), conv.model_name, conv.provider_name),
        )
        self._conn.commit()

    def list_conversations(self) -> list[Conversation]:
        rows = self._conn.execute(
            "SELECT id, title, created_at, model_name, provider_name "
            "FROM conversations ORDER BY created_at DESC"
        ).fetchall()
        return [
            Conversation(
                id=r["id"],
                title=r["title"],
                created_at=datetime.fromisoformat(r["created_at"]),
                model_name=r["model_name"],
                provider_name=r["provider_name"],
            )
            for r in rows
        ]

    def delete_conversation(self, conversation_id: str) -> None:
        self._conn.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
        self._conn.execute("DELETE FROM messages WHERE conversation_id = ?", (conversation_id,))
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
            "SELECT task_id, message_id, provider_name, model_name, video_url, status "
            "FROM active_tasks"
        ).fetchall()
        return [dict(r) for r in rows]

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
            "conversation_id, message_id, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
            ),
        )
        self._conn.commit()

    def list_media_files(
        self,
        media_type: str | None = None,
        keyword: str | None = None,
    ) -> list[MediaFile]:
        query = (
            "SELECT id, filename, media_type, local_path, file_size, source, "
            "conversation_id, message_id, created_at "
            "FROM media_files WHERE 1=1"
        )
        params: list = []
        if media_type:
            query += " AND media_type = ?"
            params.append(media_type)
        if keyword:
            query += " AND filename LIKE ?"
            params.append(f"%{keyword}%")
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
            )
            for r in rows
        ]

    def delete_media_file(self, media_id: str) -> MediaFile | None:
        row = self._conn.execute(
            "SELECT id, filename, media_type, local_path, file_size, source, "
            "conversation_id, message_id, created_at "
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

    def close(self) -> None:
        self._conn.close()
