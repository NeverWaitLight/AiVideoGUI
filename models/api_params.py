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
    """DashScope 媒体项（用于 r2v、p2v、extend 的 media 数组）"""

    type: str
    url: str
    reference_voice: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {"type": self.type, "url": self.url}
        if self.reference_voice:
            result["reference_voice"] = self.reference_voice
        return result


@dataclass
class DashScopeInputSection:
    """DashScope input 部分"""

    prompt: str
    negative_prompt: str | None = None
    audio_url: str | None = None
    media: list[MediaItem] | None = None

    def to_dict(self) -> dict[str, Any]:
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

    resolution: str | None = None
    ratio: str | None = None
    duration: int | None = None
    prompt_extend: bool = True
    watermark: bool = False
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
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

    model: str
    input: DashScopeInputSection
    parameters: DashScopeParametersSection = field(default_factory=DashScopeParametersSection)

    def to_dict(self) -> dict[str, Any]:
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

    web_search: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {}
        if self.web_search is not None:
            result["web_search"] = self.web_search
        return result


@dataclass
class SeedanceVideoRequest(BaseAPIParams):
    """Seedance 视频生成请求"""

    model: str
    prompt: str
    duration: int = 5
    quality: str = "720p"
    aspect_ratio: str = "16:9"
    generate_audio: bool = True
    callback_url: str | None = None
    model_params: SeedanceModelParams | None = None

    def to_dict(self) -> dict[str, Any]:
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
