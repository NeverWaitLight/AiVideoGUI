from pathlib import Path

from loguru import logger
from PIL import Image, ImageEnhance


def to_black_and_white(image_path: str) -> str:
    """将图片转换为黑白照片风格（灰度 + 增强对比度和锐度），原地覆盖保存。"""
    path = Path(image_path)
    if not path.is_file():
        logger.warning(f"图片文件不存在，跳过黑白处理：{image_path}")
        return image_path

    try:
        img = Image.open(path)
        img = img.convert("L")
        img = ImageEnhance.Contrast(img).enhance(1.3)
        img = ImageEnhance.Sharpness(img).enhance(1.2)
        img.save(path, quality=95)
        logger.info(f"黑白处理完成：{image_path}")
    except Exception:
        logger.exception(f"黑白处理失败：{image_path}")

    return image_path
