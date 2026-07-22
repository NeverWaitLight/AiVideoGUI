"""工作区目录结构迁移脚本。

将旧目录结构迁移到新的 workspace 结构：
- {app_data_dir}/ai-video-gui.db  → {root}/data/ai-video-gui.db
- {app_data_dir}/config.json      → {root}/data/config.json
- {old_download_dir}/*             → {root}/workspace/chat/
- {old_download_dir}/.thumbnails/* → {root}/workspace/chat/.thumbnails/

用法：python scripts/migrate_workspace.py [--dry-run]
"""

import argparse
import json
import os
import shutil
import sys

# 将项目根目录加入 sys.path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from utils import paths


def main() -> None:
    parser = argparse.ArgumentParser(description="迁移到新的 workspace 目录结构")
    parser.add_argument("--dry-run", action="store_true", help="仅预览变更，不实际执行")
    args = parser.parse_args()

    root = paths.workspace_root()
    data_dir = paths.data_dir(root)
    cache_dir = paths.cache_dir(root)
    ws_dir = paths.workspace_dir(root)
    chat_dir = paths.chat_dir(root)
    projects_dir = paths.projects_dir(root)

    # 旧路径
    old_data_dir = root  # 旧 DB 和 config 直接在 root 下
    old_db = os.path.join(old_data_dir, "ai-video-gui.db")
    old_config = os.path.join(old_data_dir, "config.json")

    # 从旧 config 读取 download_dir
    old_download_dir = ""
    if os.path.exists(old_config):
        try:
            with open(old_config, encoding="utf-8") as f:
                cfg = json.load(f)
            old_download_dir = cfg.get("app_settings", {}).get("default_download_dir", "")
        except (OSError, json.JSONDecodeError):
            pass

    if not old_download_dir:
        home = os.path.expanduser("~")
        old_download_dir = os.path.join(home, "Videos", "AI-Video-GUI")

    moves: list[tuple[str, str]] = []

    # 1. DB 迁移
    new_db = os.path.join(data_dir, "ai-video-gui.db")
    if os.path.exists(old_db) and not os.path.exists(new_db):
        moves.append((old_db, new_db))

    # 2. Config 迁移
    new_config = os.path.join(data_dir, "config.json")
    if os.path.exists(old_config) and not os.path.exists(new_config):
        moves.append((old_config, new_config))

    # 3. 下载目录迁移
    if os.path.isdir(old_download_dir):
        for name in os.listdir(old_download_dir):
            src = os.path.join(old_download_dir, name)
            if name == ".thumbnails":
                dest_dir = paths.thumbnail_dir(chat_dir)
                # 迁移 .thumbnails 里的所有文件
                if os.path.isdir(src):
                    for thumb_name in os.listdir(src):
                        moves.append((os.path.join(src, thumb_name), os.path.join(dest_dir, thumb_name)))
            else:
                dest = os.path.join(chat_dir, name)
                if not os.path.exists(dest):
                    moves.append((src, dest))

    if not moves:
        print("无需迁移，所有文件已在新目录结构中。")
        return

    # 打印迁移计划
    print(f"迁移计划（共 {len(moves)} 项）：")
    print(f"  目标根目录：{root}")
    print()
    for src, dest in moves:
        print(f"  {src}")
        print(f"    → {dest}")
    print()

    if args.dry_run:
        print("[DRY RUN] 未执行任何变更。")
        return

    # 创建目录
    for d in (data_dir, cache_dir, ws_dir, chat_dir, projects_dir):
        os.makedirs(d, exist_ok=True)

    # 执行迁移
    success = 0
    failed = 0
    for src, dest in moves:
        try:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.move(src, dest)
            success += 1
            print(f"  ✓ {os.path.basename(src)}")
        except OSError as e:
            failed += 1
            print(f"  ✗ {os.path.basename(src)}: {e}")

    print()
    print(f"迁移完成：成功 {success}，失败 {failed}")

    # 清理旧 config 中的 default_download_dir
    if os.path.exists(new_config):
        try:
            with open(new_config, encoding="utf-8") as f:
                cfg = json.load(f)
            if "app_settings" in cfg and "default_download_dir" in cfg["app_settings"]:
                del cfg["app_settings"]["default_download_dir"]
                with open(new_config, "w", encoding="utf-8") as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
                print("已清理旧配置中的 default_download_dir 字段")
        except (OSError, json.JSONDecodeError) as e:
            print(f"清理旧配置失败：{e}")


if __name__ == "__main__":
    main()
