# Material Icons 使用规则

本项目使用 Google Material Icons SVG 资源，包含 5 种视觉风格的图标。本文档定义了各种风格的使用场景和规范。

## 可用的图标风格

项目中包含以下 5 种 Material Icon 风格目录（位于 `resources/icons/material/`）：

| 风格目录 | 含义 | 视觉特点 | 适合场景 |
|---------|------|----------|----------|
| `filled` | 实心 | 图形内部填充，视觉重量高 | 默认、强调按钮、主要操作 |
| `outlined` | 线框 | 主要使用轮廓线，轻量化 | 设置、工具栏、侧边栏 |
| `round` | 圆角 | 线条和拐角更圆润 | 现代、友好的 UI |
| `sharp` | 锐角 | 边角更加硬朗 | 工业、专业、硬朗风格 |
| `two-tone` | 双色调 | 使用两种透明度/层次表现 | Dashboard、卡片、数据展示 |

**注意：** 同一个图标（如 `settings`、`play_arrow`、`delete`）在这 5 个目录中都有对应的文件，只是视觉风格不同。

## 本项目的图标使用策略

为保持 UI 风格统一，遵循 Material Design 设计规范，本项目采用以下图标使用策略：

### 核心原则

**80% `outlined` + 20% `filled`**

- **默认使用 `outlined`** - 适用于大部分 UI 场景
- **强调使用 `filled`** - 仅用于主要操作和状态强调
- **避免混用多种风格** - 保持视觉一致性

### 具体使用场景

#### 1. `outlined` - 主力风格（⭐⭐⭐⭐⭐）

**适用场景：**
- 侧边栏导航图标
- Toolbar 工具栏按钮
- 设置面板
- 文件/项目管理
- 工作流相关操作
- 素材库操作
- 一般性功能按钮

**示例：**
```text
⚙️  设置             → outlined/settings.svg
📁  项目             → outlined/folder.svg
🎬  视频             → outlined/video_library.svg
🖼️  图片             → outlined/image.svg
📝  脚本编辑          → outlined/edit_note.svg
🔍  搜索             → outlined/search.svg
```

#### 2. `filled` - 强调风格（⭐⭐⭐⭐⭐）

**适用场景：**
- 主要操作按钮（生成、开始、停止）
- 播放/暂停控制
- 删除操作
- 添加/创建操作
- 收藏/点赞
- 当前选中状态（导航高亮）

**示例：**
```text
▶️  开始生成          → filled/play_arrow.svg
⏹️  停止任务          → filled/stop.svg
🗑️  删除             → filled/delete.svg
➕  创建项目          → filled/add_circle.svg
💾  保存             → filled/save.svg
⭐  收藏             → filled/star.svg
```

#### 3. `round` - 可选风格（⭐⭐⭐⭐）

**适用场景：**
- 如果整体 UI 风格偏现代、柔和，可替代 `outlined` 作为主力
- 移动端风格的桌面应用
- 友好、轻松的用户体验场景

**当前项目建议：** 不作为主力使用，但可在特定场景（如欢迎页面、引导流程）中使用。

#### 4. `sharp` - 特殊风格（⭐⭐）

**适用场景：**
- 工业软件风格
- 专业生产工具
- 数据分析面板
- 工程类软件

**当前项目建议：** 不推荐使用（与 Material Design 柔和风格不符）。

#### 5. `two-tone` - 装饰风格（⭐⭐）

**适用场景：**
- Dashboard 首页
- 功能卡片
- 数据展示
- 大型功能入口

**不适用场景：**
- Toolbar
- 普通按钮
- 侧边栏（会导致视觉复杂）

**当前项目建议：** 可在项目首页卡片、功能入口使用，但不作为主力。

## 具体页面的图标使用建议

### 主窗口 (`MainWindow`)

```text
侧边栏导航（Sidebar）
├── 聊天      → outlined/chat_bubble.svg
├── 项目      → outlined/folder.svg
├── 素材库    → outlined/video_library.svg
├── 角色管理  → outlined/person.svg
└── 设置      → outlined/settings.svg

选中状态
└── 使用 filled 版本 + 主题色高亮
```

### 聊天页面 (`ChatArea`)

```text
输入框工具栏
├── 发送      → filled/send.svg（主要操作）
├── 附件      → outlined/attach_file.svg
├── 清空      → outlined/delete_sweep.svg
└── 参数设置  → outlined/tune.svg

视频卡片操作
├── 播放      → filled/play_circle.svg（主要操作）
├── 下载      → outlined/download.svg
├── 删除      → outlined/delete.svg
└── 更多      → outlined/more_vert.svg
```

### 项目页面 (`ProjectPage` / `ProjectDetailPage`)

```text
项目网格页
├── 创建项目  → filled/add_circle.svg（主要操作）
├── 搜索      → outlined/search.svg
├── 排序      → outlined/sort.svg
└── 视图切换  → outlined/view_module.svg

项目卡片操作
├── 打开      → outlined/folder_open.svg
├── 编辑      → outlined/edit.svg
├── 删除      → outlined/delete.svg
└── 更多      → outlined/more_vert.svg

项目详情页标签
├── 大纲      → outlined/article.svg
├── 剧本      → outlined/movie.svg
└── 分镜      → outlined/video_camera_back.svg
```

### 大纲编辑器 (`OutlineEditor`)

```text
工具栏
├── AI 生成   → filled/auto_awesome.svg（主要操作）
├── 保存      → outlined/save.svg
├── 撤销      → outlined/undo.svg
├── 重做      → outlined/redo.svg
└── 历史版本  → outlined/history.svg
```

### 剧本编辑器 (`ScriptEditor`)

```text
工具栏
├── AI 生成   → filled/auto_awesome.svg（主要操作）
├── 添加场次  → filled/add.svg（主要操作）
├── 保存      → outlined/save.svg
└── 历史版本  → outlined/history.svg

场次列表
├── 编辑      → outlined/edit.svg
├── 删除      → outlined/delete.svg
├── 上移      → outlined/arrow_upward.svg
└── 下移      → outlined/arrow_downward.svg
```

### 分镜编辑器 (`ShotEditor`)

```text
工具栏
├── 批量生成  → filled/play_arrow.svg（主要操作）
├── 添加分镜  → filled/add.svg（主要操作）
├── 保存      → outlined/save.svg
└── 历史版本  → outlined/history.svg

分镜列表
├── 生成视频  → filled/play_circle.svg（主要操作）
├── 编辑      → outlined/edit.svg
├── 删除      → outlined/delete.svg
├── 上移      → outlined/arrow_upward.svg
└── 下移      → outlined/arrow_downward.svg
```

### 素材库 (`MediaLibrary`)

```text
工具栏
├── 导入素材  → filled/upload.svg（主要操作）
├── 搜索      → outlined/search.svg
├── 筛选      → outlined/filter_list.svg
└── 视图切换  → outlined/view_list.svg

素材卡片操作
├── 播放      → filled/play_circle.svg（主要操作）
├── 定位文件  → outlined/folder.svg
├── 删除      → outlined/delete.svg
└── 信息      → outlined/info.svg
```

### 角色管理 (`CharacterPage`)

```text
工具栏
├── 添加角色  → filled/person_add.svg（主要操作）
├── AI 提取   → filled/auto_awesome.svg（主要操作）
├── 搜索      → outlined/search.svg
└── 排序      → outlined/sort.svg

角色卡片操作
├── 编辑      → outlined/edit.svg
├── 删除      → outlined/delete.svg
└── 生成设计图 → filled/image.svg（主要操作）
```

### 设置对话框 (`SettingsDialog`)

```text
设置分类
├── 通用      → outlined/settings.svg
├── Provider  → outlined/api.svg
├── 外观      → outlined/palette.svg
└── 关于      → outlined/info.svg
```

## 代码中的图标引用

### QML 中使用图标

```qml
import QtQuick.Controls.Material

Button {
    icon.source: "qrc:/icons/material/outlined/settings.svg"
    icon.color: Material.foreground  // 自动适配主题色
}
```

### Python 中使用图标（PyQt6-Fluent-Widgets）

对于需要从 Python 代码设置图标的场景：

```python
from qfluentwidgets import PrimaryPushButton, PushButton
from PyQt6.QtGui import QIcon

# 主要操作 - 使用 filled
btn_generate = PrimaryPushButton("生成视频")
btn_generate.setIcon(QIcon(":/icons/material/filled/play_arrow.svg"))

# 普通操作 - 使用 outlined
btn_settings = PushButton("设置")
btn_settings.setIcon(QIcon(":/icons/material/outlined/settings.svg"))
```

## 图标命名规范

Material Icons 使用 **snake_case** 命名规范，示例：

```text
✅ play_arrow.svg
✅ settings.svg
✅ video_library.svg
✅ person_add.svg
✅ arrow_upward.svg

❌ PlayArrow.svg
❌ Settings.svg
❌ videoLibrary.svg
```

## 图标尺寸建议

Material Icons 是矢量图标（SVG），可自由缩放，但建议使用以下标准尺寸以保持视觉一致性：

| 场景 | 推荐尺寸 | 说明 |
|------|---------|------|
| 侧边栏导航 | 24dp | Material Design 标准 |
| Toolbar 按钮 | 24dp | Material Design 标准 |
| 主要操作按钮 | 24dp | 与文字大小协调 |
| 卡片图标 | 32dp - 48dp | 较大的功能入口 |
| 列表项图标 | 20dp - 24dp | 紧凑布局 |
| 对话框图标 | 24dp | 标准尺寸 |

**注意：** dp（Density-independent Pixels）在桌面应用中通常直接对应像素（px）。

## 图标颜色处理

### 自动适配主题

Material Icons SVG 文件默认颜色为黑色（`#000000`），Qt Quick Controls Material 会自动根据主题（Light/Dark）调整图标颜色：

```qml
// 图标会自动适配主题前景色
Button {
    icon.source: "qrc:/icons/material/outlined/settings.svg"
    icon.color: Material.foreground  // Light: 深色, Dark: 浅色
}
```

### 自定义颜色

如需自定义图标颜色（如强调色、警告色）：

```qml
Button {
    icon.source: "qrc:/icons/material/filled/delete.svg"
    icon.color: Material.color(Material.Red)  // 删除操作使用红色
}
```

### 常见颜色场景

| 操作类型 | 推荐颜色 | Material 颜色 |
|---------|---------|--------------|
| 默认操作 | 主题前景色 | `Material.foreground` |
| 主要操作 | 主题色 | `Material.accent` |
| 删除操作 | 红色 | `Material.color(Material.Red)` |
| 成功状态 | 绿色 | `Material.color(Material.Green)` |
| 警告状态 | 橙色 | `Material.color(Material.Orange)` |
| 禁用状态 | 灰色 | `Material.color(Material.Grey)` |

## 添加新图标

如需添加项目中尚未包含的 Material Icons：

1. 访问 [Google Fonts - Material Icons](https://fonts.google.com/icons)
2. 搜索并下载所需图标的 SVG 文件
3. 下载对应的 5 种风格（filled, outlined, round, sharp, two-tone）
4. 放入对应的目录：`resources/icons/material/<风格>/`
5. 确保文件名为 **snake_case**
6. 在 `resources.qrc` 中添加引用：
   ```xml
   <file>icons/material/outlined/new_icon.svg</file>
   <file>icons/material/filled/new_icon.svg</file>
   ```
7. 重新编译资源文件：`pyside6-rcc resources.qrc -o resources_rc.py`

## 图标资源管理

### 资源文件结构

```text
resources/
├── icons/
│   └── material/
│       ├── filled/       # 实心风格
│       ├── outlined/     # 线框风格
│       ├── round/        # 圆角风格
│       ├── sharp/        # 锐角风格
│       └── two-tone/     # 双色调风格
└── resources.qrc         # Qt 资源配置文件
```

### 资源文件引用

在 QML 中使用 `qrc:/` 前缀引用资源：

```qml
icon.source: "qrc:/icons/material/outlined/settings.svg"
```

## 参考资料

- [Google Fonts - Material Icons](https://fonts.google.com/icons)
- [Material Design - Iconography](https://material.io/design/iconography/system-icons.html)
- [Qt Quick Controls - Material Style](https://doc.qt.io/qt-6/qtquickcontrols-material.html)
- [PyQt6-Fluent-Widgets Documentation](https://qfluentwidgets.com/)

## 更新日志

- 2026-07-29: 初始版本，定义 Material Icons 5 种风格的使用规范
