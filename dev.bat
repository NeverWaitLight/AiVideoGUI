@echo off
REM 开发环境启动脚本
REM 设置 DEV_MODE=1 使应用使用项目本地的 dev_workspace/ 目录

set DEV_MODE=1
echo [DEV MODE] 使用本地开发环境: dev_workspace/
uv run main.py
