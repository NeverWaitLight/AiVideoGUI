"""端到端验证：submit → poll → download 完整链路（mock Provider）。"""

import json
import os
import sys
import tempfile
import time
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)

from config.manager import ConfigManager
from models.data_models import (
    MessageStatus,
    ProviderConfig,
    TaskResult,
    TaskStatus,
)
from service.video_service import VideoService, _PROVIDER_REGISTRY
from storage.database import DatabaseManager


def main():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = os.path.join(tmp, "test.db")
        cfg_path = os.path.join(tmp, "config.json")
        download_dir = os.path.join(tmp, "videos")
        temp_dir = os.path.join(tmp, "tmp")

        # 写入配置
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "providers": [
                        {
                            "provider_name": "dashscope",
                            "api_key": "fake-key",
                            "base_url": "",
                            "default_model": "wan2.7-t2v",
                            "default_params": {},
                        }
                    ],
                    "app_settings": {
                        "default_provider": "dashscope",
                        "default_download_dir": download_dir,
                        "theme": "light",
                    },
                },
                f,
            )

        db = DatabaseManager(db_path)
        cfg = ConfigManager(cfg_path)
        svc = VideoService(db, cfg, download_dir=download_dir, temp_dir=temp_dir)

        # Mock Provider
        mock_provider = MagicMock()
        mock_provider.provider_name = "dashscope"
        mock_provider._config = ProviderConfig(
            provider_name="dashscope",
            api_key="fake-key",
            default_model="wan2.7-t2v",
        )
        mock_provider.submit.return_value = "mock-task-123"

        poll_count = {"n": 0}

        def fake_check_status(task_id):
            poll_count["n"] += 1
            if poll_count["n"] < 2:
                return TaskResult(status=TaskStatus.RUNNING)
            return TaskResult(
                status=TaskStatus.SUCCEEDED,
                video_url="https://example.com/video.mp4",
            )

        mock_provider.check_status.side_effect = fake_check_status

        # 伪造视频字节
        fake_video_bytes = b"\x00\x00\x00\x1cftypisom" + b"\x00" * 100

        def fake_download(video_url, save_path, progress_callback=None):
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(fake_video_bytes)
            if progress_callback:
                progress_callback(len(fake_video_bytes), len(fake_video_bytes))
            return save_path

        mock_provider.download.side_effect = fake_download

        svc._providers["dashscope"] = mock_provider

        # 收集信号
        events = []
        svc.status_changed.connect(lambda mid, s: events.append(("status", mid, s)))
        svc.download_progress.connect(lambda mid, d, t: events.append(("progress", mid, d, t)))
        svc.task_finished.connect(lambda mid, p: events.append(("finished", mid, p)))
        svc.task_failed.connect(lambda mid, e: events.append(("failed", mid, e)))

        # 1. 创建对话
        conv = svc.create_conversation("dashscope", "wan2.7-t2v", "测试对话")
        assert conv.id
        print(f"[OK] 创建对话: id={conv.id}")

        # 2. 添加用户消息
        user_msg = svc.add_user_message(conv.id, "来一段猫咪视频")
        assert user_msg.role == "user"
        print(f"[OK] 用户消息: id={user_msg.id}")

        # 3. 提交任务
        assistant_msg = svc.submit_task(conv.id, "猫咪骑木马", "dashscope")
        assert assistant_msg.status == MessageStatus.GENERATING
        assert assistant_msg.task_id == "mock-task-123"
        print(f"[OK] 提交任务: message={assistant_msg.id} task={assistant_msg.task_id}")

        # 4. 等待 worker 完成（最多 10 秒）
        deadline = time.time() + 10
        while time.time() < deadline:
            app.processEvents()
            if any(e[0] in ("finished", "failed") for e in events):
                break
            time.sleep(0.05)

        print(f"[OK] 事件序列: {events}")

        # 验证
        finished_events = [e for e in events if e[0] == "finished"]
        assert finished_events, f"未收到 finished 事件，events={events}"
        local_path = finished_events[0][2]
        assert os.path.exists(local_path), f"视频文件未生成: {local_path}"
        print(f"[OK] 视频已下载: {local_path}")

        # 5. 验证 DB 状态
        messages = db.list_messages(conv.id)
        assert len(messages) == 2
        assistant_from_db = [m for m in messages if m.role == "assistant"][0]
        assert assistant_from_db.status == MessageStatus.COMPLETED
        assert assistant_from_db.local_path == local_path
        print(f"[OK] DB 状态正确: status={assistant_from_db.status.value}, path={assistant_from_db.local_path}")

        # 清理
        svc.shutdown()
        db.close()
        print("\n✅ 端到端链路验证通过：submit → poll → download → 持久化 全部 OK")


if __name__ == "__main__":
    main()
