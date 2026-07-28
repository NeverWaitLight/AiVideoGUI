# 主题切换功能说明

## 功能概述

应用支持三种主题模式：
- **亮色** - 固定使用亮色主题
- **暗色** - 固定使用暗色主题
- **跟随系统**（默认）- 自动适应 Windows 系统主题设置

## 系统主题检测实现

### Windows 平台
使用 Windows 注册表检测系统主题：
```
HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize
- AppsUseLightTheme: 0 = 暗色, 1 = 亮色
```

应用会每 3 秒轮询注册表，检测系统主题变化并自动切换。

### 其他平台
使用 Qt 的 QPalette 分析窗口背景色亮度判断主题。

## 使用方式

1. 打开设置对话框（点击左侧标签栏的设置按钮）
2. 切换到"外观"标签页
3. 选择主题模式：
   - 亮色 - 固定亮色
   - 暗色 - 固定暗色
   - 跟随系统 - 自动跟随 Windows 系统设置
4. 点击"保存"应用更改

## 技术细节

### 颜色方案

**亮色主题：**
- 背景：白色 (#FFFFFF)
- 侧边栏：浅灰 (#F5F5F5)
- 文字：深灰 (#333333)
- 边框：浅灰 (#E0E0E0)

**暗色主题：**
- 背景：深灰 (#2D2D2D)
- 侧边栏：极深灰 (#1E1E1E)
- 文字：浅灰 (#E0E0E0)
- 边框：深灰 (#404040)

### 实现文件

- `bridge/theme.py` - Theme 类，管理主题状态和颜色
- `bridge/settings_bridge.py` - 主题设置的读写方法
- `qml/dialogs/SettingsDialog.qml` - 设置对话框 UI
- `models/app_settings.py` - 应用设置数据模型
- `main.py` - 启动时加载保存的主题

### 配置存储

主题设置保存在 `%LOCALAPPDATA%\ai-video-gui\data\config.json` 的 `app_settings.theme` 字段。
