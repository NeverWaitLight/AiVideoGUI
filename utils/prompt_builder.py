"""视频生成提示词组装工具。"""


def inject_shot_context(prompt: str, prev_ctx: str, next_ctx: str) -> str:
    """将前后镜头参考插入到已增强的提示词中。

    插入位置在 [角色形象] 行之后、[画面] 行之前。
    若提示词中无 [画面] 标记，则追加到末尾。

    Args:
        prompt: 已经过角色增强的提示词
        prev_ctx: 前一镜头参考文本（可为空）
        next_ctx: 后一镜头参考文本（可为空）

    Returns:
        插入上下文后的完整提示词
    """
    context_lines = [line for line in (prev_ctx, next_ctx) if line]
    if not context_lines:
        return prompt

    context_block = "\n".join(context_lines)

    if "[画面]" in prompt:
        return prompt.replace("[画面]", f"{context_block}\n[画面]", 1)

    return f"{prompt}\n{context_block}"
