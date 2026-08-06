## 问题描述

在分镜卡片列表页，多选模式开启后，勾选部分卡片，点击"设计场景"按钮时：
1. 弹出空白错误提示框
2. 日志中没有异常信息
3. 不会启动场景设计逻辑
4. 但在分镜详情中单独生成设计图是正常的

## 根本原因

**QML 闭包捕获问题：** 确认对话框的回调函数直接引用了 `_selectedIds`，JavaScript 闭包捕获的是变量引用而非值的副本。如果在确认对话框打开和用户点击确认之间 `_selectedIds` 被修改或清空，回调函数会使用修改后的值。

## 修复方案

### QML 端修复（主要修复）

**文件：** `qml/pages/StoryboardPage.qml`

在按钮点击时创建 `_selectedIds` 的副本，在闭包中使用副本：

```qml
onClicked: {
    var selectedIdsCopy = _selectedIds.slice()
    confirmDialog.confirm(
        "确定要为选中的 " + selectedIdsCopy.length + " 个分镜生成设计图吗？",
        function() {
            bridge.storyboard.batch_generate_design_images(
                page.projectId,
                JSON.stringify(selectedIdsCopy)
            )
        }
    )
}
```

### Python 端增强日志（辅助诊断）

**文件：** `bridge/storyboard_bridge.py`

在 `batch_generate_design_images` 方法中添加详细的调试日志，包括：方法被调用的确认、加载的分镜总数和 ID 列表、解析后的选中 ID 列表和类型、过滤前后的分镜数量。

### 修复信号槽参数不匹配（次要修复）

**文件：** `bridge/storyboard_bridge.py`

修复 `on_progress` 回调的 emit 调用，移除字符串拼接，只传递 `message`。

## 验证步骤

1. 打开项目分镜页面，开启多选模式，勾选 2-3 个分镜卡片
2. 点击"设计场景"按钮 → 确认对话框正常弹出
3. 点击"确定" → 设计图生成任务正常启动
4. 检查应用日志确认参数传递正确

## 相关文件

- `qml/pages/StoryboardPage.qml` — 分镜列表页 UI
- `bridge/storyboard_bridge.py` — 分镜桥接层
- `bridge/workers.py` — 批量设计图生成 Worker
- `service/storyboard_service.py` — 分镜业务逻辑
