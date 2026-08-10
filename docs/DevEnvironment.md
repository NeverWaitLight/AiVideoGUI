# 开发环境说明

## 环境隔离

项目支持两种运行模式：

### 1. 生产模式（默认）
```bash
uv run main.py
```
- 数据存储在系统目录：`%LOCALAPPDATA%\ai-video-gui\`
- 用于正式打包和安装后的运行

### 2. 开发模式
```bash
# Windows
dev.bat

# Linux/macOS
./dev.sh
```
- 数据存储在项目目录：`./dev_workspace/`
- 所有生成的文件（数据库、日志、缓存、素材等）都在本地
- 与已安装的生产版本完全隔离，可以同时运行

## 开发模式目录结构

```
ai-video-gui/
├── dev_workspace/          # 开发环境数据目录（已加入 .gitignore）
│   ├── data/              # 数据库和配置
│   │   ├── ai-video-gui.db
│   │   └── config.json
│   ├── logs/              # 日志文件
│   │   ├── app.log
│   │   └── error.log
│   ├── cache/             # 缓存目录
│   ├── projects/          # 项目文件
│   └── resources/         # 资源文件（自动复制）
├── dev.bat                # Windows 开发启动脚本
└── dev.sh                 # Linux/macOS 开发启动脚本
```

## 实现原理

通过环境变量 `DEV_MODE=1` 控制路径切换：

- `utils/paths.py` 中的 `workspace_root()` 检测环境变量
- 开发模式：返回 `项目目录/dev_workspace/`
- 生产模式：返回 `%LOCALAPPDATA%/ai-video-gui/`

## 使用场景

1. **并行开发**：在已安装版本运行的同时开发新功能
2. **测试隔离**：测试数据不会污染生产环境
3. **快速迭代**：无需重新打包安装即可测试新版本
4. **团队协作**：每个开发者独立的本地环境
