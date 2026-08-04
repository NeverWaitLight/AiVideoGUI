# AI 请求日志记录功能 - 使用说明

## 功能概述

AI 请求日志记录功能可以记录所有 AI 调用的请求和响应详情，帮助您：
- 调试和优化 Prompt
- 追踪项目中每个模块的 AI 使用情况
- 分析 AI 调用的效果和成本

## 功能特性

1. **按项目组织**：每个项目在 `logs/` 目录下有独立的文件夹（格式：`{项目名称}_{项目ID}/`）
2. **按模块分类**：每个项目文件夹内有 4 个 Markdown 文件：
   - `outline.md` - 大纲相关的 AI 调用
   - `script.md` - 剧本相关的 AI 调用
   - `character.md` - 角色相关的 AI 调用
   - `storyboard.md` - 分镜相关的 AI 调用
3. **完整记录**：包含请求体、响应体、时间戳、操作类型等完整信息
4. **路径转换**：自动将绝对路径转换为相对路径，便于阅读和迁移
5. **Markdown 格式**：标准 Markdown 格式，易于阅读和版本控制
6. **配置开关**：可通过配置文件随时启用/禁用

## 启用方式

### 方法 1：通过配置文件

编辑 `%LOCALAPPDATA%\ai-video-gui\data\config.json`，在 `app_settings` 中添加：

```json
{
  "app_settings": {
    "enable_ai_request_logging": true
  }
}
```

### 方法 2：通过代码（未来可添加 UI 设置）

```python
config_manager.update_settings(enable_ai_request_logging=True)
```

## 日志文件位置

默认位置：`%LOCALAPPDATA%\ai-video-gui\logs\`

目录结构示例：
```
logs/
├── 我的短片_123/                      # 项目文件夹
│   ├── outline.md                     # 大纲模块日志
│   ├── script.md                      # 剧本模块日志
│   ├── character.md                   # 角色模块日志
│   └── storyboard.md                  # 分镜模块日志
└── 科幻短片_456/
    ├── outline.md
    ├── script.md
    ├── character.md
    └── storyboard.md
```

## 日志格式示例

```markdown
## 2026-08-04 14:23:45 - 大纲优化

**操作类型**: text_generation

**请求详情**:
```json
{
  "model": "qwen-max",
  "input": {
    "messages": [
      {"role": "system", "content": "你是一个专业的视频项目策划助手..."},
      {"role": "user", "content": "原始大纲：...\n\n优化要求：..."}
    ]
  },
  "parameters": {
    "result_format": "message"
  }
}
```

**响应详情**:
```json
{
  "output": {
    "choices": [
      {
        "message": {
          "role": "assistant",
          "content": "优化后的大纲内容..."
        }
      }
    ]
  },
  "usage": {
    "input_tokens": 1234,
    "output_tokens": 567
  }
}
```

**相关文件**:
- [大纲草稿](../projects/123/outline_draft.txt)

---
```

## 记录的 AI 调用类型

### 文本生成（TextModelService）
- 大纲优化 → `outline.md`
- 剧本生成 → `script.md`
- 剧本优化 → `script.md`
- 角色生成 → `character.md`
- 角色优化 → `character.md`
- 角色描述优化 → `character.md`
- 分镜生成 → `storyboard.md`
- 分镜优化 → `storyboard.md`

### 图片生成（ImageService）
- 角色设计图生成 → `character.md`
- 分镜设计图生成 → `storyboard.md`

### 视频生成（VideoService）
- 文生视频 (t2v) → `storyboard.md`
- 参考图生视频 (r2v) → `storyboard.md`

## 注意事项

1. **敏感信息保护**：日志记录器会自动移除 Authorization 头中的 API Key（显示为 `[REDACTED]`）
2. **磁盘空间**：长期运行可能产生大量日志文件，建议定期清理或归档
3. **性能影响**：日志写入是异步的，对性能影响极小
4. **文件名安全**：项目名称中的特殊字符（如 `<>:"/\|?*`）会被自动替换为下划线

## 当前限制

由于需要传递项目信息到 Service 层，部分调用点可能暂时缺少项目信息导致日志记录失败（会在应用日志中显示警告）。完整的项目信息传递将在后续版本中完成。

## 实现细节

### 核心组件

1. **AIRequestLogger** (`utils/ai_request_logger.py`)
   - 核心日志记录器
   - 处理文件管理、格式化、路径转换

2. **配置管理** (`models/app_settings.py`, `config/manager.py`)
   - `enable_ai_request_logging` 配置项

3. **依赖注入** (`di/containers.py`)
   - AIRequestLogger 注册为单例
   - 自动注入到所有 Service

4. **Service 层集成**
   - TextModelService：所有方法已集成
   - ImageService：已集成
   - VideoService：已集成

### 设计原则

- **代码解耦**：独立模块，不侵入现有业务逻辑
- **线程安全**：基于 Python 文件操作的原子性
- **性能优先**：日志记录失败不影响主流程
- **可配置**：通过配置文件控制开关

## 测试

运行测试脚本验证功能：

```bash
uv run python test_ai_logger.py
```

测试覆盖：
- 项目日志记录
- 特殊字符处理
- 日志格式验证
- 配置开关功能

## 后续扩展建议

1. **UI 集成**：在设置对话框中添加日志记录开关
2. **日志查看器**：在应用中添加日志查看面板
3. **统计分析**：统计每个项目的 AI 调用次数和 token 使用量
4. **导出功能**：导出为 PDF 或 Word 文档
5. **自动清理**：自动清理过期日志（如保留最近 30 天）
6. **日志搜索**：按时间、项目、模块搜索日志
7. **成本分析**：根据 token 使用量计算 API 调用成本
