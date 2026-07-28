# DashScope 图生视频和视频续写使用示例

本文档展示如何使用 DashScope Provider 的图生视频（p2v）和视频续写（extend）功能。

## 前置条件

确保已配置 DashScope API Key 和模型：

```python
from models.provider_config import ProviderConfig
from providers.dashscope_video import DashScopeVideoProvider

config = ProviderConfig(
    provider_name="dashscope",
    api_key="your-api-key",
    base_url="https://dashscope.aliyuncs.com/api/v1",
    default_model="wan2.7-i2v-2026-04-25",
)
provider = DashScopeVideoProvider(config)
```

## 1. 图生视频（p2v）

### 1.1 首帧生视频

仅使用首帧图片生成视频：

```python
task_id, payload = provider.p2v(
    prompt="一只小猫在草地上奔跑",
    image_path="https://example.com/first_frame.jpg",
    params={
        "resolution": "720P",
        "duration": 10,
        "prompt_extend": True,
        "watermark": True,
    }
)
```

### 1.2 首尾帧生视频

使用首帧和尾帧图片生成过渡视频：

```python
task_id, payload = provider.p2v(
    prompt="小猫从坐姿变为站立姿态",
    image_path="https://example.com/first_frame.jpg",
    params={
        "resolution": "720P",
        "duration": 10,
        "last_frame_path": "https://example.com/last_frame.jpg",  # 尾帧图片
        "prompt_extend": False,
    }
)
```

### 1.3 首帧+音频生视频

使用首帧图片和驱动音频生成视频（如口型同步）：

```python
task_id, payload = provider.p2v(
    prompt="一个说唱歌手在表演",
    image_path="https://example.com/rapper.jpg",
    params={
        "resolution": "1080P",
        "duration": 15,
        "driving_audio_path": "https://example.com/rap.mp3",  # 驱动音频
        "watermark": True,
    }
)
```

### 1.4 首帧+尾帧+音频组合

同时使用首帧、尾帧和驱动音频：

```python
task_id, payload = provider.p2v(
    prompt="完整的表演场景",
    image_path="https://example.com/first_frame.jpg",
    params={
        "resolution": "1080P",
        "duration": 10,
        "last_frame_path": "https://example.com/last_frame.jpg",
        "driving_audio_path": "https://example.com/audio.mp3",
    }
)
```

## 2. 视频续写（extend）

### 2.1 基于首段视频续写

使用首段视频片段生成后续内容：

```python
task_id, payload = provider.extend(
    prompt="女孩背着书包出门",
    video_path="https://example.com/first_clip.mp4",
    params={
        "resolution": "720P",
        "duration": 15,  # 注意：这是最终输出视频的总时长（包含输入视频）
        "prompt_extend": True,
    }
)
```

**重要说明：**
- `duration` 参数表示**最终输出视频的总时长**（包含输入视频时长）
- 例如：输入视频 3 秒，duration=15，则续写 12 秒，最终输出 15 秒

### 2.2 首段视频+尾帧续写

使用首段视频和尾帧图片进行续写：

```python
task_id, payload = provider.extend(
    prompt="女孩走到门外，镜头拉远",
    video_path="https://example.com/first_clip.mp4",
    params={
        "resolution": "720P",
        "duration": 15,
        "last_frame_path": "https://example.com/last_frame.jpg",  # 尾帧图片
    }
)
```

## 3. 查询任务状态

提交任务后，使用 `check_status` 轮询查询结果：

```python
import time
from models.enums import TaskStatus

# 提交任务
task_id, payload = provider.p2v(...)

# 轮询查询状态
max_retries = 60
for i in range(max_retries):
    result = provider.check_status(task_id)
    
    if result.status == TaskStatus.SUCCEEDED:
        print(f"视频生成成功：{result.video_url}")
        break
    elif result.status == TaskStatus.FAILED:
        print(f"视频生成失败：{result.error_message}")
        break
    elif result.status in [TaskStatus.PENDING, TaskStatus.RUNNING]:
        print(f"任务进行中...（{i+1}/{max_retries}）")
        time.sleep(10)  # 等待 10 秒后重试
    else:
        print(f"未知状态：{result.status}")
        break
```

## 4. 下载视频

任务成功后，下载视频到本地：

```python
import os

# 查询任务状态获取 video_url
result = provider.check_status(task_id)

if result.status == TaskStatus.SUCCEEDED:
    save_path = os.path.join("outputs", "generated_video.mp4")
    
    # 下载视频（带进度回调）
    def progress_callback(downloaded, total):
        percent = (downloaded / total * 100) if total > 0 else 0
        print(f"下载进度：{percent:.1f}% ({downloaded}/{total} bytes)")
    
    final_path = provider.download(
        video_url=result.video_url,
        save_path=save_path,
        progress_callback=progress_callback,
    )
    print(f"视频已保存到：{final_path}")
```

## 5. 参数说明

### 通用参数（适用于 t2v/p2v/extend）

| 参数 | 类型 | 说明 | 默认值 |
|------|------|------|--------|
| `prompt` | str | 文本提示词 | 必需 |
| `resolution` | str | 分辨率档位（"720P" 或 "1080P"） | "1080P" |
| `duration` | int | 视频时长（2-15秒） | 5 |
| `prompt_extend` | bool | 智能改写提示词 | True |
| `watermark` | bool | 添加水印 | False |
| `seed` | int | 随机数种子 | 自动生成 |
| `negative_prompt` | str | 反向提示词 | 无 |

### p2v 特有参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `image_path` | str | 首帧图片路径（URL 或 base64） |
| `last_frame_path` | str | 尾帧图片路径（可选，URL 或 base64） |
| `driving_audio_path` | str | 驱动音频路径（可选，URL） |

### extend 特有参数

| 参数 | 类型 | 说明 |
|------|------|------|
| `video_path` | str | 首段视频路径（URL） |
| `last_frame_path` | str | 尾帧图片路径（可选，URL 或 base64） |

## 6. 支持的素材格式

### 图片
- **格式：** JPEG、JPG、PNG（不支持透明通道）、BMP、WEBP
- **分辨率：** 宽和高的范围为 [240, 8000] 像素
- **宽高比：** 1:8 ~ 8:1
- **文件大小：** 不超过 20MB
- **输入方式：** 公网 URL 或 Base64 编码

### 音频
- **格式：** WAV、MP3
- **时长：** 2～30秒
- **文件大小：** 不超过 15MB
- **输入方式：** 公网 URL

### 视频
- **格式：** MP4、MOV
- **时长：** 2～10秒
- **分辨率：** 宽和高的范围为 [240, 4096] 像素
- **宽高比：** 1:8 ~ 8:1
- **文件大小：** 不超过 100MB
- **输入方式：** 公网 URL

## 7. 注意事项

1. **素材 URL 有效期：** 确保传入的图片/音频/视频 URL 在任务执行期间可访问
2. **视频 URL 有效期：** API 返回的 video_url 仅保留 24 小时，请及时下载
3. **task_id 有效期：** task_id 查询有效期为 24 小时
4. **轮询间隔：** 建议每 10-15 秒查询一次任务状态，避免频繁请求
5. **素材组合限制：** 仅支持特定的素材组合（参见官方文档），非法组合会被 API 拒绝

## 8. 错误处理

```python
try:
    task_id, payload = provider.p2v(
        prompt="测试视频",
        image_path="https://example.com/image.jpg",
        params={"resolution": "720P", "duration": 10}
    )
except RuntimeError as e:
    print(f"任务提交失败：{e}")
except Exception as e:
    print(f"未知错误：{e}")
```

常见错误：
- **InvalidApiKey：** API Key 无效或未配置
- **InvalidParameter：** 参数不符合要求（如分辨率超限）
- **ResourceNotFound：** 素材 URL 无法访问
- **QuotaExceeded：** 账户余额不足或超出配额限制
