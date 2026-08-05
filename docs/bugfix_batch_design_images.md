# 批量生成设计图功能修复

## 问题描述

在分镜卡片列表页，多选模式开启后，勾选部分卡片，点击"设计场景"按钮时：
1. 弹出空白错误提示框
2. 日志中没有异常信息
3. 不会启动场景设计逻辑
4. 但在分镜详情中单独生成设计图是正常的

## 问题分析

### 可能的根本原因

**QML 闭包捕获问题：**
在原始代码中，确认对话框的回调函数直接引用了 `_selectedIds`：

```qml
onClicked: {
    confirmDialog.confirm(
        "确定要为选中的 " + _selectedIds.length + " 个分镜生成设计图吗？",
        function() { 
            bridge.storyboard.batch_generate_design_images(
                page.projectId, 
                JSON.stringify(_selectedIds)  // 直接引用 _selectedIds
            ) 
        }
    )
}
```

这可能导致以下问题：
1. **闭包引用时机问题**：JavaScript 闭包捕获的是变量引用，而非值的副本。如果在确认对话框打开和用户点击确认之间，`_selectedIds` 被修改或清空，回调函数会使用修改后的值。
2. **Qt QML 引擎的特殊行为**：Qt QML 的属性绑定系统可能在某些情况下导致闭包中的变量引用失效。

### 其他可能的原因

1. **参数类型不匹配**：
   - Python Slot 声明：`@Slot(int, str)`
   - QML 传递：`JSON.stringify(_selectedIds)` 应该返回字符串
   - 但如果 `_selectedIds` 是特殊值（如 `undefined`），可能导致类型错误

2. **ID 过滤失败**：
   - Python 代码中：`shots = [s for s in shots if s.id in selected_ids]`
   - 如果 `selected_ids` 解析后的 ID 类型和数据库中的类型不匹配，会导致过滤结果为空
   - 但数据模型确认 ID 是 `int` 类型，JSON.parse 也会返回整数数组，理论上不应该有问题

## 修复方案

### 1. QML 端修复（主要修复）

**修改文件：** `qml/pages/StoryboardPage.qml`

在按钮点击时创建 `_selectedIds` 的副本，并在闭包中使用副本：

```qml
onClicked: {
    var selectedIdsCopy = _selectedIds.slice()  // 创建副本
    console.log("设计场景按钮点击，选中ID:", JSON.stringify(selectedIdsCopy))
    confirmDialog.confirm(
        "确定要为选中的 " + selectedIdsCopy.length + " 个分镜生成设计图吗？",
        function() {
            console.log("确认对话框回调执行，ID:", JSON.stringify(selectedIdsCopy))
            bridge.storyboard.batch_generate_design_images(
                page.projectId, 
                JSON.stringify(selectedIdsCopy)  // 使用副本
            )
        }
    )
}
```

**关键改进：**
1. 使用 `.slice()` 创建数组的浅拷贝
2. 闭包捕获的是独立的副本，不受后续 `_selectedIds` 变化的影响
3. 添加 `console.log` 用于调试，可以在控制台看到选中的 ID

### 2. Python 端增强日志（辅助诊断）

**修改文件：** `bridge/storyboard_bridge.py`

在 `batch_generate_design_images` 方法中添加详细的调试日志：

```python
@Slot(int, str)
def batch_generate_design_images(self, project_id: int, shot_ids_json: str) -> None:
    logger.info(f"batch_generate_design_images called: project_id={project_id}, shot_ids_json={shot_ids_json!r}")
    try:
        shots = self._storyboard_service.list_storyboards(project_id)
        logger.info(f"加载了 {len(shots)} 个分镜，ID列表：{[s.id for s in shots]}")
        if not shots:
            self.error.emit("没有分镜可以生成设计图")
            return

        if shot_ids_json and shot_ids_json != "[]":
            try:
                selected_ids = json.loads(shot_ids_json)
                logger.info(f"解析选中 ID：{selected_ids}，类型：{[type(x).__name__ for x in selected_ids]}")
            except (json.JSONDecodeError, TypeError) as e:
                logger.error(f"解析选中分镜 ID 失败：shot_ids_json={shot_ids_json!r}, error={e}")
                self.error.emit(f"参数解析失败：{shot_ids_json!r}")
                return

            logger.info(f"过滤前分镜数：{len(shots)}")
            shots = [s for s in shots if s.id in selected_ids]
            logger.info(f"过滤后分镜数：{len(shots)}，选中的分镜 ID：{[s.id for s in shots]}")
            if not shots:
                logger.error(f"未找到选中的分镜！selected_ids={selected_ids}, 可用ID={[s.id for s in self._storyboard_service.list_storyboards(project_id)]}")
                self.error.emit("未找到选中的分镜")
                return
        # ... 后续代码
```

**日志输出内容：**
1. 方法被调用的确认（包括参数值）
2. 加载的分镜总数和 ID 列表
3. 解析后的选中 ID 列表和类型
4. 过滤前后的分镜数量
5. 如果过滤后为空，输出详细的调试信息

### 3. 修复信号槽参数不匹配（次要修复）

**修改文件：** `bridge/storyboard_bridge.py`

在 `batch_generate_design_images` 方法中，修复 `on_progress` 回调的 emit 调用：

```python
def on_progress(current: int, message: str, count_info: str) -> None:
    self.batch_progress.emit(current, len(shot_list), message)  # 移除字符串拼接
```

**原因：**
- Worker 信号：`progress_update = Signal(int, str, str)` 
- Bridge 信号：`batch_progress = Signal(int, int, str)`
- 原代码错误地拼接了 `message` 和 `count_info`，应该只传递 `message`

## 验证步骤

运行应用后，按以下步骤验证修复：

1. **打开项目分镜页面**
2. **开启多选模式**（点击多选按钮）
3. **勾选 2-3 个分镜卡片**
4. **打开开发者控制台**（查看 console.log 输出）
5. **点击"设计场景"按钮**
   - 应该看到：`设计场景按钮点击，选中ID: [1, 2, 3]`
6. **点击确认对话框的"确定"按钮**
   - 应该看到：`确认对话框回调执行，ID: [1, 2, 3]`
7. **检查应用日志文件**（`%LOCALAPPDATA%\ai-video-gui\logs\app.log`）
   - 应该看到：`batch_generate_design_images called: project_id=X, shot_ids_json='[1, 2, 3]'`
   - 应该看到：`加载了 X 个分镜，ID列表：[...]`
   - 应该看到：`解析选中 ID：[1, 2, 3]，类型：['int', 'int', 'int']`
   - 应该看到：`过滤后分镜数：3，选中的分镜 ID：[1, 2, 3]`
8. **验证设计图生成任务启动**
   - 应该开始生成设计图（进度提示）
   - 不应该弹出错误提示框

## 如果问题仍然存在

如果应用修复后问题仍然存在，检查以下内容：

1. **控制台日志是否有输出？**
   - 如果没有"设计场景按钮点击"日志 → 按钮点击事件没有触发（UI 问题）
   - 如果有"设计场景按钮点击"但没有"确认对话框回调执行" → 确认对话框回调没有执行
   - 如果有"确认对话框回调执行"但没有 Python 日志 → Slot 调用失败（参数类型问题）

2. **Python 日志显示了什么？**
   - 如果显示"未找到选中的分镜" → ID 过滤失败，检查 ID 类型和值
   - 如果显示"没有分镜可以生成设计图" → 项目分镜列表为空
   - 如果显示"参数解析失败" → JSON 格式错误

3. **分镜详情页单独生成设计图是否正常？**
   - 如果正常 → 说明 `generate_design_image` 方法可用，问题在批量调用逻辑
   - 如果也失败 → 可能是 ImageService 或 Provider 配置问题

## 相关文件

- `qml/pages/StoryboardPage.qml` - 分镜列表页 UI
- `bridge/storyboard_bridge.py` - 分镜桥接层
- `bridge/workers.py` - 批量设计图生成 Worker
- `service/storyboard_service.py` - 分镜业务逻辑
- `storage/repositories/storyboard_repository.py` - 分镜数据访问

## 后续改进建议

1. **统一闭包处理**：检查项目中其他使用确认对话框的地方，确保都使用副本而非直接引用
2. **类型安全**：考虑在 QML 端添加参数类型验证
3. **错误提示优化**：空白错误提示应该显示"未知错误"而不是空字符串
4. **单元测试**：为批量操作添加单元测试，覆盖边界情况（空数组、无效 ID 等）
