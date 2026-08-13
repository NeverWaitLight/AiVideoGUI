# AiVideoGUI

一款运行在本地的 AI 视频创作工具，提供完整的视频项目创作流程，从故事构思到批量生成视频。

## ✨ 主要功能

### 📝 完整的视频创作工作流
适合制作系列视频或长视频项目：
1. **项目管理** - 创建和管理多个视频项目
2. **大纲编辑** - AI 辅助优化故事大纲
3. **剧本分场** - 自动将大纲扩展为分场剧本
4. **角色管理** - 定义角色形象，生成设计图
5. **分镜设计** - AI 生成分镜脚本和设计图
6. **批量生成** - 一键批量生成所有分镜视频
7. **素材库** - 统一管理生成的视频素材

### 🎨 核心特性
- **阿里云全家桶** - 统一使用阿里云 DashScope 服务（视频生成、文本对话、图片生成）
- **参考图片功能** - 支持为分镜添加参考图片（角色设计图、分镜设计图）
- **智能提示词构建** - 自动整合场景上下文、角色描述、镜头参数等信息
- **现代化界面** - Material Design 风格，支持亮色/暗色主题
- **本地优先** - 所有数据存储在本地，保护隐私

## 🚀 快速开始

### 方式一：使用安装包（推荐）
1. 从 [Releases](https://github.com/yourusername/ai-video-gui/releases) 页面下载最新的 `.exe` 安装包
2. 双击安装包，按提示完成安装
3. 首次启动时，在设置中配置 API Key

### 方式二：从源码运行
1. 确保已安装 Python 3.14+ 和 [uv](https://github.com/astral-sh/uv) 包管理器
2. 克隆仓库并安装依赖：
   ```bash
   git clone https://github.com/yourusername/ai-video-gui.git
   cd ai-video-gui
   uv sync
   ```
3. 启动应用：
   ```bash
   uv run main.py
   ```

## ⚙️ 配置说明

### 视频生成服务
应用当前支持：

- **阿里万象** (DashScope)
  - 模型：wan2.7-t2v
  - 支持分辨率：720P、1080P
  - 支持宽高比：16:9、9:16、1:1、4:3、3:4
  - 获取 API Key：https://dashscope.console.aliyun.com/

### 文本模型（AI 对话和辅助功能）
应用当前支持：

- **阿里云 DashScope** - 通义千问系列
  - 支持模型：qwen-max、qwen-plus、qwen-turbo、qwen-vl-max、qwen-vl-plus
  - 获取 API Key：https://dashscope.console.aliyun.com/

### 图片生成服务
应用当前支持：

- **阿里百炼万相** - 文生图服务
  - 模型：wan2.6-t2i
  - 用于生成角色设计图和分镜设计图
  - 获取 API Key：https://dashscope.console.aliyun.com/

**提示：** 视频、文本、图片生成服务使用同一个 DashScope API Key。

### 首次使用
1. 打开应用后，点击左下角"设置"按钮
2. 填入阿里云 DashScope API Key（用于视频生成、文本对话、图片生成）
3. （可选）在"应用设置"中自定义视频下载目录

**获取 API Key：** 访问 https://dashscope.console.aliyun.com/ 注册并获取 API Key

## 📖 使用方法

1. 点击"创建项目"，填写项目信息
2. 按照工作流顺序完成各个步骤：
   - 编写或优化故事大纲
   - 生成剧本分场
   - 定义角色形象（可生成角色设计图）
   - 生成分镜脚本和设计图
   - 批量生成视频
3. 在素材库中查看和管理生成的视频

## 🛠️ 技术栈

- **界面框架** - PySide6 + Qt Quick (QML)
- **编程语言** - Python 3.14
- **数据库** - SQLite + SQLAlchemy 2.0
- **AI 集成** - DashScope API（阿里云通义千问）、自定义 Provider（视频模型）
- **依赖管理** - uv
- **设计风格** - Material Design

## 📁 数据存储

应用数据存储在以下位置：

- **配置和数据库** - `%LOCALAPPDATA%\ai-video-gui\data\`
- **视频文件** - `%USERPROFILE%\Videos\AI-Video-GUI\`（可自定义）
- **日志文件** - `%LOCALAPPDATA%\ai-video-gui\logs\`

## 📝 开发者文档

如果你想参与开发或了解技术细节：

- [CLAUDE.md](CLAUDE.md) - 完整的架构设计和开发约定
- [打包指南](docs/PackagingGuide.md) - 如何打包 Windows 安装程序
- [开发环境说明](docs/DevEnvironment.md) - 开发/生产环境隔离

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 许可证

本项目采用 [GNU General Public License v3.0](LICENSE) 开源许可证。

## 📞 联系方式

如有问题或建议，欢迎通过 GitHub Issues 反馈。
