class ImagePromptBuilder:
    """图片大模型提示词构建器（统一入口）"""

    @staticmethod
    def build_bailian_image_payload(
        prompt: str,
        size: str = "1280*1280",
        negative_prompt: str = "",
        n: int = 1,
        prompt_extend: bool = True,
        watermark: bool = False,
        seed: int | None = None,
        model: str = "wan2.6-t2i",
    ) -> dict:
        """构建阿里百炼文生图 API 请求体"""
        payload = {
            "model": model,
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [{"text": prompt}],
                    }
                ]
            },
            "parameters": {
                "size": size,
                "n": n,
                "negative_prompt": negative_prompt,
                "prompt_extend": prompt_extend,
                "watermark": watermark,
            },
        }

        if seed is not None:
            payload["parameters"]["seed"] = seed

        return payload
