"""UI 集成验证：MainWindow + VideoService + Mock Provider。"""

import json
import os
import sys
import tempfile
import time
from unittest.mock import MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)

from models.data_models import ProviderConfig, TaskResult, TaskStatus
from ui.main_window import MainWindow


def main():
    tmp = tempfile.mkdtemp()
    try:
        import ui.main_window as mw_mod
        mw_mod._app_data_dir = lambda: tmp

        cfg_path = os.path.join(tmp, "config.json")
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
                        "default_download_dir": os.path.join(tmp, "videos"),
                        "theme": "light",
                    },
                },
                f,
            )

        w = MainWindow()
        print("[OK] MainWindow 初始化完成")

        # 替换 provider 为 mock
        mock_provider = MagicMock()
        mock_provider.provider_name = "dashscope"
        mock_provider._config = ProviderConfig(
            provider_name="dashscope",
            api_key="fake-key",
            default_model="wan2.7-t2v",
        )
        mock_provider.submit.return_value = "mock-task-ui"

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

        fake_video_bytes = b"\x00\x00\x00\x1cftypisom" + b"\x00" * 100

        def fake_download(video_url, save_path, progress_callback=None):
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(fake_video_bytes)
            if progress_callback:
                progress_callback(len(fake_video_bytes), len(fake_video_bytes))
            return save_path

        mock_provider.download.side_effect = fake_download
        w._service._providers["dashscope"] = mock_provider

        # 覆盖轮询参数以加速测试
        w._service.poll_delay = 0.0
        w._service.poll_interval = 0.1

        # 1. 新建对话
        w.sidebar.new_conversation_clicked.emit()
        app.processEvents()
        conv_id = w._current_conversation_id
        assert conv_id, "未创建对话"
        print(f"[OK] 新建对话: id={conv_id}")

        # 2. 直接调用 _on_message_sent（等价于点击发送按钮）
        w._on_message_sent("一只猫咪骑木马")
        app.processEvents()
        time.sleep(0.2)

        # 提交后应立即有 2 条消息
        messages = w._db.list_messages(conv_id)
        print(f"[INFO] 提交后消息数: {len(messages)}")
        for m in messages:
            print(f"       role={m.role} status={m.status.value} task_id={m.task_id}")

        # 3. 等待 worker 跑完
        deadline = time.time() + 15
        while time.time() < deadline:
            app.processEvents()
            time.sleep(0.05)
            if not w._service._workers:
                break

        time.sleep(0.3)
        app.processEvents()

        # 4. 验证
        messages = w._db.list_messages(conv_id)
        print(f"[INFO] 完成后消息数: {len(messages)}")
        for m in messages:
            print(f"       role={m.role} status={m.status.value} path={m.local_path}")

        assert len(messages) == 2, f"应有 2 条消息，实际 {len(messages)}"
        user_msg = [m for m in messages if m.role == "user"][0]
        asst_msg = [m for m in messages if m.role == "assistant"][0]
        assert user_msg.content == "一只猫咪骑木马"
        assert asst_msg.status.value == "completed", f"助手消息状态: {asst_msg.status.value}"
        assert asst_msg.local_path and os.path.exists(asst_msg.local_path)
        print(f"[OK] 视频文件: {asst_msg.local_path}")

        # 5. 删除对话
        w.sidebar.conversation_deleted.emit(conv_id)
        app.processEvents()
        assert w._current_conversation_id is None
        assert w._db.list_conversations() == []
        print("[OK] 对话删除成功")

        w._service.shutdown()
        w._db.close()
        print("\n✅ UI → Service → Provider 链路完整验证通过")
    finally:
        # Windows 下 SQLite 锁可能残留，忽略清理失败
        import shutil
        try:
            shutil.rmtree(tmp, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    main()
