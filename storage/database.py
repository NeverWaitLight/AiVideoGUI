"""SQLite 数据库管理。"""

import logging
import sqlite3
from datetime import datetime

from models.data_models import Conversation, Message, MessageStatus

logger = logging.getLogger(__name__)


class DatabaseManager:
    """SQLite 对话/消息/任务持久化。"""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._init_tables()

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
            "(id, conversation_id, role, content, created_at, task_id, video_url, local_path, status) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
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
            ),
        )
        self._conn.commit()

    def list_messages(self, conversation_id: str) -> list[Message]:
        rows = self._conn.execute(
            "SELECT id, conversation_id, role, content, created_at, "
            "task_id, video_url, local_path, status "
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

    def close(self) -> None:
        self._conn.close()
