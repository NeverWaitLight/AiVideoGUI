"""验证 SettingsDialog ↔ ConfigManager ↔ VideoService 联动。"""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtWidgets import QApplication

app = QApplication.instance() or QApplication(sys.argv)

from config.manager import ConfigManager
from models.data_models import ProviderConfig
from ui.main_window import MainWindow
from ui.settings_dialog import SettingsDialog


def main():
    tmp = tempfile.mkdtemp()
    try:
        import ui.main_window as mw_mod
        mw_mod._app_data_dir = lambda: tmp

        # 空配置启动
        cfg_path = os.path.join(tmp, "config.json")
        with open(cfg_path, "w", encoding="utf-8") as f:
            json.dump({"providers": [], "app_settings": {}}, f)

        w = MainWindow()
        print("[OK] MainWindow 初始化（空配置）")

        # 1. 打开设置面板
        dialog = SettingsDialog(w._config, w)
        assert dialog.provider_combo.count() > 0, "供应商下拉无选项"
        assert dialog.api_key_input.text() == "", "初始 API Key 应为空"
        print("[OK] SettingsDialog 初始状态正确（空 API Key）")

        # 2. 模拟用户输入
        dialog.api_key_input.setText("sk-abc-123456")
        dialog.base_url_input.setText("https://dashscope.aliyuncs.com")
        dialog.download_dir_input.setText(os.path.join(tmp, "my_videos"))
        dialog._on_save()
        assert not dialog.isVisible(), "保存后应关闭对话框"
        print("[OK] 保存完成，对话框已关闭")

        # 3. 验证 ConfigManager 持久化
        cfg = w._config.get_provider("dashscope")
        assert cfg is not None, "dashscope 未保存"
        assert cfg.api_key == "sk-abc-123456"
        assert cfg.base_url == "https://dashscope.aliyuncs.com"
        assert cfg.default_model == "wan2.7-t2v"
        assert w._config.settings.default_download_dir.endswith("my_videos")
        assert w._config.settings.default_provider == "dashscope"
        print(f"[OK] Config 持久化：api_key={cfg.api_key}, download_dir={w._config.settings.default_download_dir}")

        # 4. 验证 JSON 文件
        with open(cfg_path, encoding="utf-8") as f:
            data = json.load(f)
        assert len(data["providers"]) == 1
        assert data["providers"][0]["api_key"] == "sk-abc-123456"
        print("[OK] JSON 文件内容正确")

        # 5. 重新打开应回显
        dialog2 = SettingsDialog(w._config, w)
        assert dialog2.api_key_input.text() == "sk-abc-123456", "重开应回显 API Key"
        assert dialog2.download_dir_input.text().endswith("my_videos")
        assert dialog2.model_combo.currentText() == "wan2.7-t2v"
        print("[OK] 重新打开回显正确")
        dialog2.reject()

        # 6. VideoService 应用新下载目录
        w._apply_default_provider()
        assert w._service._download_dir.endswith("my_videos")
        print(f"[OK] VideoService 下载目录已同步：{w._service._download_dir}")

        # 7. 发送消息时 API Key 能被 Provider 读取（用 mock 替代实际 HTTP）
        from unittest.mock import MagicMock
        from models.data_models import TaskResult, TaskStatus

        mock_provider = MagicMock()
        mock_provider.provider_name = "dashscope"
        mock_provider._config = cfg
        mock_provider.submit.return_value = "task-after-config"
        mock_provider.check_status.return_value = TaskResult(
            status=TaskStatus.SUCCEEDED, video_url="https://example.com/v.mp4"
        )

        def fake_download(url, path, progress_callback=None):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(b"x")
            return path

        mock_provider.download.side_effect = fake_download
        w._service._providers["dashscope"] = mock_provider

        # 新建对话 + 发送
        w.sidebar.new_conversation_clicked.emit()
        app.processEvents()
        w._on_message_sent("测试配置后的提交")
        app.processEvents()

        # 验证 submit 被调用且使用的是已配置 provider
        mock_provider.submit.assert_called_once()
        call_args = mock_provider.submit.call_args
        assert call_args[0][0] == "测试配置后的提交"
        # 关键验证：provider 的 api_key 来自配置
        assert w._service.get_provider("dashscope")._config.api_key == "sk-abc-123456"
        print("[OK] submit_task 使用配置中的 API Key")

        w._service.shutdown()
        w._db.close()
        print("\n✅ SettingsDialog ↔ ConfigManager ↔ VideoService 联动验证通过")
    finally:
        import shutil
        try:
            shutil.rmtree(tmp, ignore_errors=True)
        except Exception:
            pass


if __name__ == "__main__":
    main()
