AI 请求日志记录功能可以记录所有 AI 调用的请求和响应详情，用于调试和优化 Prompt、追踪项目中每个模块的 AI 使用情况、分析 AI 调用的效果和成本。

## 功能特性

- **按项目组织**：每个项目在 `logs/` 目录下有独立的文件夹（格式：`{项目名称}_{项目ID}/`）
- **按模块分类**：每个项目文件夹内有 4 个 Markdown 文件：
  - `outline.md` — 大纲相关的 AI 调用
  - `script.md` — 剧本相关的 AI 调用
  - `character.md` — 角色相关的 AI 调用
  - `storyboard.md` — 分镜相关的 AI 调用
- **完整记录**：包含请求体、响应体、时间戳、操作类型等完整信息
- **路径转换**：自动将绝对路径转换为相对路径，便于阅读和迁移
- **配置开关**：可通过配置文件随时启用/禁用

## 启用方式

编辑 `%LOCALAPPDATA%\ai-video-gui\data\settings.json`，在 `app_settings` 中添加：

```json
{
  "app_settings": {
    "enable_ai_request_logging": true
  }
}
```

## 日志文件位置

默认位置：`%LOCALAPPDATA%\ai-video-gui\logs\`

```
logs/
├── 我的短片_123/
│   ├── outline.md
│   ├── script.md
│   ├── character.md
│   └── storyboard.md
└── 科幻短片_456/
    ├── outline.md
    ├── script.md
    ├── character.md
    └── storyboard.md
```

## 记录的 AI 调用类型

**文本生成（TextModelService）**
- 大纲优化 → `outline.md`
- 剧本生成/优化 → `script.md`
- 角色生成/优化/描述优化 → `character.md`
- 分镜生成/优化 → `storyboard.md`

**图片生成（ImageService）**
- 角色设计图生成 → `character.md`
- 分镜设计图生成 → `storyboard.md`

**视频生成（VideoService）**
- 文生视频 (t2v) / 参考图生视频 (r2v) → `storyboard.md`

## 注意事项

- **敏感信息保护**：自动移除 Authorization 头中的 API Key（显示为 `[REDACTED]`）
- **磁盘空间**：长期运行可能产生大量日志文件，建议定期清理或归档
- **性能影响**：日志写入是异步的，对性能影响极小
- **文件名安全**：项目名称中的特殊字符会被自动替换为下划线

## 实现细节

**核心组件**
- **AIRequestLogger** (`utils/ai_request_logger.py`) — 核心日志记录器
- **配置管理** (`models/app_settings.py`, `config/manager.py`) — `enable_ai_request_logging` 配置项
- **依赖注入** (`di/containers.py`) — AIRequestLogger 注册为单例，自动注入到所有 Service

**设计原则**
- 独立模块，不侵入现有业务逻辑
- 日志记录失败不影响主流程
- 通过配置文件控制开关
