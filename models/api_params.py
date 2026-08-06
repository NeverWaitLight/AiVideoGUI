from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class BaseAPIParams(ABC):
    """所有 API 参数类的基类"""

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """转换为 API 请求所需的字典格式"""
        pass

    def _remove_none_values(self, data: dict[str, Any]) -> dict[str, Any]:
        """递归移除 None 值（保持 API 请求简洁）"""
        result = {}
        for key, value in data.items():
            if value is None:
                continue
            if isinstance(value, dict):
                nested = self._remove_none_values(value)
                if nested:
                    result[key] = nested
            elif isinstance(value, list):
                cleaned_list = []
                for item in value:
                    if isinstance(item, dict):
                        cleaned_list.append(self._remove_none_values(item))
                    elif item is not None:
                        cleaned_list.append(item)
                if cleaned_list:
                    result[key] = cleaned_list
            else:
                result[key] = value
        return result


@dataclass
class MediaItem:
    """DashScope 媒体项数据模型（用于 r2v、p2v、extend 的 media 数组）"""

    type: str                           # 媒体类型（image/video）
    url: str                            # 媒体文件 URL
    reference_voice: str | None = None  # 参考语音（可选）

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        result = {"type": self.type, "url": self.url}
        if self.reference_voice:
            result["reference_voice"] = self.reference_voice
        return result


@dataclass
class DashScopeInputSection:
    """DashScope input 部分"""

    prompt: str                              # 文本提示词
    negative_prompt: str | None = None       # 负向提示词（可选）
    audio_url: str | None = None             # 音频URL（可选）
    media: list[MediaItem] | None = None     # 媒体项列表（可选）

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        result: dict[str, Any] = {"prompt": self.prompt}

        if self.negative_prompt:
            result["negative_prompt"] = self.negative_prompt
        if self.audio_url:
            result["audio_url"] = self.audio_url
        if self.media:
            result["media"] = [item.to_dict() for item in self.media]

        return result


@dataclass
class DashScopeParametersSection:
    """DashScope parameters 部分（保存所有运行时参数）"""

    resolution: str | None = None       # 分辨率（如 720P、1080P）
    ratio: str | None = None            # 宽高比（如 16:9、9:16）
    duration: int | None = None         # 时长（秒）
    prompt_extend: bool = True          # 是否启用提示词扩展
    watermark: bool = False             # 是否添加水印
    extra: dict[str, Any] = field(default_factory=dict)  # 额外参数

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        result = {}

        if self.resolution:
            result["resolution"] = self.resolution
        if self.ratio:
            result["ratio"] = self.ratio
        if self.duration is not None:
            result["duration"] = self.duration

        result["prompt_extend"] = self.prompt_extend
        result["watermark"] = self.watermark

        result.update(self.extra)

        return result


@dataclass
class DashScopeVideoRequest(BaseAPIParams):
    """DashScope 视频生成请求（顶层结构）"""

    model: str                           # 模型名称
    input: DashScopeInputSection         # 输入部分
    parameters: DashScopeParametersSection = field(default_factory=DashScopeParametersSection)  # 参数部分

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        return {
            "model": self.model,
            "input": self.input.to_dict(),
            "parameters": self.parameters.to_dict(),
        }

    @classmethod
    def for_t2v(
        cls,
        model: str,
        prompt: str,
        negative_prompt: str | None = None,
        audio_url: str | None = None,
        resolution: str | None = None,
        ratio: str | None = None,
        duration: int | None = None,
        prompt_extend: bool = True,
        watermark: bool = False,
        **extra_params: Any,
    ) -> DashScopeVideoRequest:
        """构建文生视频请求的便捷方法"""
        return cls(
            model=model,
            input=DashScopeInputSection(
                prompt=prompt,
                negative_prompt=negative_prompt,
                audio_url=audio_url,
            ),
            parameters=DashScopeParametersSection(
                resolution=resolution,
                ratio=ratio,
                duration=duration,
                prompt_extend=prompt_extend,
                watermark=watermark,
                extra=extra_params,
            ),
        )

    @classmethod
    def for_r2v(
        cls,
        model: str,
        prompt: str,
        media: list[MediaItem],
        negative_prompt: str | None = None,
        resolution: str | None = None,
        ratio: str | None = None,
        duration: int | None = None,
        prompt_extend: bool = True,
        watermark: bool = False,
        **extra_params: Any,
    ) -> DashScopeVideoRequest:
        """构建参考生视频请求的便捷方法"""
        return cls(
            model=model,
            input=DashScopeInputSection(
                prompt=prompt,
                negative_prompt=negative_prompt,
                media=media,
            ),
            parameters=DashScopeParametersSection(
                resolution=resolution,
                ratio=ratio,
                duration=duration,
                prompt_extend=prompt_extend,
                watermark=watermark,
                extra=extra_params,
            ),
        )


@dataclass
class SeedanceModelParams:
    """Seedance model_params 嵌套对象"""

    web_search: bool | None = None      # 是否启用联网检索

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        result = {}
        if self.web_search is not None:
            result["web_search"] = self.web_search
        return result


@dataclass
class SeedanceVideoRequest(BaseAPIParams):
    """Seedance 视频生成请求"""

    model: str                          # 模型名称
    prompt: str                         # 文本提示词
    duration: int = 5                   # 时长（秒，4-30秒）
    quality: str = "720p"               # 画质（480p/720p/1080p/4k）
    aspect_ratio: str = "16:9"          # 宽高比
    generate_audio: bool = True         # 是否生成同步音频
    callback_url: str | None = None     # 回调URL（可选）
    model_params: SeedanceModelParams | None = None  # 模型参数（可选）

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式"""
        result = {
            "model": self.model,
            "prompt": self.prompt,
            "duration": self.duration,
            "quality": self.quality,
            "aspect_ratio": self.aspect_ratio,
            "generate_audio": self.generate_audio,
        }

        if self.callback_url:
            result["callback_url"] = self.callback_url

        if self.model_params:
            params_dict = self.model_params.to_dict()
            if params_dict:
                result["model_params"] = params_dict

        return result

    @classmethod
    def for_t2v(
        cls,
        model: str,
        prompt: str,
        duration: int = 5,
        quality: str = "720p",
        aspect_ratio: str = "16:9",
        generate_audio: bool = True,
        web_search: bool | None = None,
        callback_url: str | None = None,
    ) -> SeedanceVideoRequest:
        """构建文生视频请求的便捷方法"""
        model_params = None
        if web_search is not None:
            model_params = SeedanceModelParams(web_search=web_search)

        return cls(
            model=model,
            prompt=prompt,
            duration=duration,
            quality=quality,
            aspect_ratio=aspect_ratio,
            generate_audio=generate_audio,
            callback_url=callback_url,
            model_params=model_params,
        )
