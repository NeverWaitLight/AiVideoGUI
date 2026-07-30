"""提示词模板系统使用演示。

演示如何使用新的模板系统构建消息并调用 LLM。
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from di.containers import ApplicationContainer


def demo_template_usage():
    """演示模板系统的使用。"""
    # 初始化容器
    container = ApplicationContainer()
    container.config.workspace_root.from_value(
        str(Path.home() / "AppData" / "Local" / "ai-video-gui")
    )
    container.config.config_path.from_value(
        str(Path.home() / "AppData" / "Local" / "ai-video-gui" / "config.json")
    )

    # 获取 TextModelService
    text_service = container.text_model_service()

    print("=" * 60)
    print("Prompt Template System Demo")
    print("=" * 60)

    # 列出所有可用模板
    templates = text_service._prompt_manager.list_templates()
    print(f"\n[OK] Loaded {len(templates)} templates:")
    for template_name in templates:
        print(f"  - {template_name}")

    # 演示 1：聊天模板
    print("\n" + "=" * 60)
    print("Demo 1: Chat Template")
    print("=" * 60)

    template = text_service._prompt_manager.get_template("chat")
    messages = template.build_messages(user_input="Hello, please introduce yourself")

    print(f"\nNumber of messages: {len(messages)}")
    print("\nSystem prompt:")
    print(messages[0]["content"][:100] + "...")
    print(f"\nUser message:")
    print(messages[-1]["content"])

    # 演示 2：大纲优化模板
    print("\n" + "=" * 60)
    print("Demo 2: Outline Optimization Template")
    print("=" * 60)

    template = text_service._prompt_manager.get_template("outline_optimization")
    messages = template.build_messages(
        original_content="This is a sci-fi story outline...",
        user_requirement="Add more suspense and plot twists",
    )

    print(f"\nNumber of messages: {len(messages)}")
    print("\nUser message (with variables filled):")
    print(messages[-1]["content"][:200] + "...")

    # 演示 3：图片提示词生成模板
    print("\n" + "=" * 60)
    print("Demo 3: Image Prompt Generation Template")
    print("=" * 60)

    template = text_service._prompt_manager.get_template("image_prompt_generation")
    messages = template.build_messages(
        visual_content="A young woman standing in the rain on the street",
        shot_size="Medium shot",
        camera_movement="Static",
        dialogue="None",
        notes="Cold tone, rim lighting",
        character_info="25 years old, long hair, wearing trench coat",
    )

    print(f"\nNumber of messages: {len(messages)}")
    print(f"\nNumber of few-shot examples: {len(template.few_shot_examples)}")
    print("\nUser message (with all parameters):")
    print(messages[-1]["content"][:300] + "...")

    # 演示 4：角色设计图提示词生成模板
    print("\n" + "=" * 60)
    print("Demo 4: Character Design Image Prompt Template")
    print("=" * 60)

    template = text_service._prompt_manager.get_template(
        "character_image_prompt_generation"
    )
    messages = template.build_messages(
        character_name="Li Ming",
        description="""[Species] Human - Asian
[Appearance] 25 years old male, square face, thick eyebrows
[Hair Style] Short hair, side part
[Hair Color] Natural black
[Eye Color] Deep brown
[Body Type] 178cm, athletic build
[Top] Dark gray suit jacket
[Pants] Black trousers
[Shoes] Black leather shoes
[Hat] None""",
    )

    print(f"\nNumber of messages: {len(messages)}")
    print(f"\nNumber of few-shot examples: {len(template.few_shot_examples)}")
    print("\nFirst few-shot example (user input):")
    print(template.few_shot_examples[0]["user"][:150] + "...")
    print("\nFirst few-shot example (assistant reply):")
    print(template.few_shot_examples[0]["assistant"][:150] + "...")

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print(
        "\nNote: In actual use, call text_service.chat(messages, model) to send to LLM."
    )


if __name__ == "__main__":
    demo_template_usage()
