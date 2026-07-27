"""
时间轴组件 - 类似专业剪辑软件的时间轴，支持多视频片段显示和预览
"""
import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple
from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal, QRect, QPoint, QTimer
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush, QFont, QPixmap, QPainterPath

logger = logging.getLogger(__name__)


@dataclass
class VideoSegment:
    """视频片段数据结构"""
    scene_number: int
    shot_number: int
    sequence: int
    start_time: int  # 在总时间轴上的起始时间（毫秒）
    duration: int    # 视频时长（毫秒）
    color: QColor    # 边框颜色
    thumbnail_path: Optional[str]  # 缩略图路径


class TimelinePreview(QWidget):
    """时间轴悬停预览窗口"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.ToolTip | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # UI 组件
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        self._thumbnail_label = QLabel()
        self._thumbnail_label.setFixedSize(160, 90)
        self._thumbnail_label.setScaledContents(True)
        self._thumbnail_label.setStyleSheet("""
            QLabel {
                background: #1E1E1E;
                border: 2px solid #3A3A3A;
                border-radius: 4px;
            }
        """)

        self._time_label = QLabel()
        self._time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._time_label.setStyleSheet("QLabel { color: white; font-weight: bold; }")

        self._info_label = QLabel()
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._info_label.setStyleSheet("QLabel { color: #AAAAAA; font-size: 11px; }")

        layout.addWidget(self._thumbnail_label)
        layout.addWidget(self._time_label)
        layout.addWidget(self._info_label)

        # 设置窗口样式
        self.setStyleSheet("""
            QWidget {
                background: #2B2B2B;
                border: 1px solid #3A3A3A;
                border-radius: 6px;
            }
        """)

    def show_preview(self, thumbnail_path: Optional[str], time_ms: int, scene: int, shot: int):
        """显示预览"""
        # 加载缩略图
        if thumbnail_path:
            pixmap = QPixmap(thumbnail_path)
            if not pixmap.isNull():
                self._thumbnail_label.setPixmap(pixmap)
            else:
                self._thumbnail_label.setText("无缩略图")
        else:
            self._thumbnail_label.setText("无缩略图")

        # 设置时间标签
        self._time_label.setText(self._format_time(time_ms))

        # 设置信息标签
        self._info_label.setText(f"场{scene}镜{shot}")

        self.adjustSize()
        self.show()

    def _format_time(self, milliseconds: int) -> str:
        """格式化时间为 MM:SS"""
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"


class TimelineWidget(QWidget):
    """专业级时间轴组件"""

    # 信号
    seekRequested = pyqtSignal(int)  # 用户拖动定位时发射（全局时间，毫秒）

    def __init__(self, parent=None):
        super().__init__(parent)

        # 数据
        self._segments: List[VideoSegment] = []
        self._total_duration: int = 0
        self._current_position: int = 0  # 当前播放位置（全局时间）

        # UI 配置
        self._timeline_height = 80  # 时间轴高度（增加以显示缩略图）
        self._ruler_height = 20     # 标尺高度
        self._border_width = 3      # 片段边框宽度
        self._corner_radius = 4     # 片段圆角半径

        # 交互状态
        self._is_dragging = False
        self._hover_position: Optional[int] = None  # 鼠标悬停位置（像素坐标）
        self._hover_segment_index: Optional[int] = None

        # 预览窗口
        self._preview = TimelinePreview(self)
        self._preview.hide()
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._show_preview)

        # 设置固定高度
        self.setFixedHeight(self._timeline_height + self._ruler_height)
        self.setMinimumWidth(400)

        # 启用鼠标追踪
        self.setMouseTracking(True)

    def set_segments(self, segments: List[VideoSegment]):
        """设置视频片段列表"""
        self._segments = segments
        self._total_duration = sum(seg.duration for seg in segments)
        logger.debug(f"时间轴加载 {len(segments)} 个片段，总时长 {self._total_duration}ms")
        self.update()

    def set_position(self, position: int):
        """更新当前播放位置（由播放器驱动）"""
        if self._current_position != position:
            self._current_position = position
            self.update()

    def paintEvent(self, event):
        """绘制时间轴"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # 绘制背景
        self._draw_background(painter)

        # 绘制视频片段
        if self._segments:
            self._draw_segments(painter)

        # 绘制时间标尺
        self._draw_ruler(painter)

        # 绘制播放指针
        if self._total_duration > 0:
            self._draw_playhead(painter)

    def _draw_background(self, painter: QPainter):
        """绘制背景"""
        # 使用深色背景
        bg_color = QColor(43, 43, 43)  # #2B2B2B
        painter.fillRect(self.rect(), bg_color)

        # 绘制分隔线
        painter.setPen(QPen(QColor(58, 58, 58), 1))
        painter.drawLine(0, self._ruler_height, self.width(), self._ruler_height)

    def _draw_segments(self, painter: QPainter):
        """绘制视频片段（类似剪辑软件轨道样式）"""
        if self._total_duration == 0:
            return

        timeline_rect = QRect(0, self._ruler_height, self.width(), self._timeline_height)

        for i, segment in enumerate(self._segments):
            if segment.duration <= 0:
                continue

            # 计算片段在时间轴上的位置
            x_start = int((segment.start_time / self._total_duration) * self.width())
            x_end = int(((segment.start_time + segment.duration) / self._total_duration) * self.width())
            width = max(x_end - x_start, 2)  # 最小宽度 2px

            segment_rect = QRect(x_start, timeline_rect.top() + 2, width, timeline_rect.height() - 4)

            # 判断是否为当前播放片段
            is_current = (segment.start_time <= self._current_position < segment.start_time + segment.duration)

            # 保存绘制状态
            painter.save()

            # 设置裁剪区域（圆角矩形）
            clip_path = QPainterPath()
            clip_path.addRoundedRect(segment_rect.x(), segment_rect.y(),
                                   segment_rect.width(), segment_rect.height(),
                                   self._corner_radius, self._corner_radius)
            painter.setClipPath(clip_path)

            # 绘制缩略图背景
            if segment.thumbnail_path and width > 20:  # 宽度足够才绘制缩略图
                self._draw_segment_thumbnails(painter, segment_rect, segment.thumbnail_path)
            else:
                # 宽度不够时使用纯色填充
                fill_color = QColor(segment.color)
                fill_color.setAlpha(100)
                painter.fillRect(segment_rect, fill_color)

            # 绘制半透明覆盖层（统一色调）
            overlay_color = QColor(segment.color)
            overlay_color.setAlpha(40)
            painter.fillRect(segment_rect, overlay_color)

            # 恢复绘制状态
            painter.restore()

            # 绘制边框
            border_width = 3 if is_current else 2
            painter.setPen(QPen(segment.color, border_width))
            painter.drawPath(clip_path)

            # 如果是当前片段，添加发光效果
            if is_current:
                glow_color = QColor(segment.color)
                glow_color.setAlpha(60)
                painter.setPen(QPen(glow_color, border_width + 2))
                painter.drawPath(clip_path)

            # 绘制场景/镜头标签（如果宽度足够）
            if width > 50:
                self._draw_segment_label(painter, segment_rect, segment, is_current)

    def _draw_segment_thumbnails(self, painter: QPainter, rect: QRect, thumbnail_path: str):
        """在片段内绘制缩略图（平铺或缩放）"""
        # 加载缩略图（带缓存）
        if not hasattr(self, '_thumbnail_cache'):
            self._thumbnail_cache = {}

        if thumbnail_path not in self._thumbnail_cache:
            pixmap = QPixmap(thumbnail_path)
            if not pixmap.isNull():
                # 缩放到轨道高度
                scaled_pixmap = pixmap.scaledToHeight(
                    rect.height(),
                    Qt.TransformationMode.SmoothTransformation
                )
                self._thumbnail_cache[thumbnail_path] = scaled_pixmap
            else:
                self._thumbnail_cache[thumbnail_path] = None

        pixmap = self._thumbnail_cache.get(thumbnail_path)
        if pixmap is None:
            # 缩略图加载失败，使用深色背景
            painter.fillRect(rect, QColor(40, 40, 40))
            return

        # 平铺绘制缩略图（类似剪辑软件的效果）
        thumb_width = pixmap.width()
        x = rect.x()
        while x < rect.right():
            # 计算需要绘制的宽度（最后一块可能被裁剪）
            draw_width = min(thumb_width, rect.right() - x)
            source_rect = QRect(0, 0, draw_width, pixmap.height())
            target_rect = QRect(x, rect.y(), draw_width, rect.height())
            painter.drawPixmap(target_rect, pixmap, source_rect)
            x += thumb_width

    def _draw_segment_label(self, painter: QPainter, rect: QRect, segment: VideoSegment, is_current: bool):
        """绘制片段标签（场X镜X）"""
        label_text = f"场{segment.scene_number}镜{segment.shot_number}"

        # 设置字体和颜色
        font = QFont("Segoe UI", 9, QFont.Weight.Bold)
        painter.setFont(font)

        # 文字颜色（白色，带阴影效果）
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(0, 0, 0, 120))  # 半透明黑色背景

        # 计算文字位置（左上角）
        text_rect = QRect(rect.x() + 4, rect.y() + 2, rect.width() - 8, 20)

        # 绘制背景矩形
        bg_rect = painter.fontMetrics().boundingRect(text_rect, Qt.AlignmentFlag.AlignLeft, label_text)
        bg_rect.adjust(-3, -1, 3, 1)
        painter.drawRoundedRect(bg_rect, 2, 2)

        # 绘制文字
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, label_text)

    def _draw_ruler(self, painter: QPainter):
        """绘制时间标尺"""
        if self._total_duration == 0:
            return

        ruler_rect = QRect(0, 0, self.width(), self._ruler_height)

        # 设置字体
        font = QFont("Segoe UI", 9)
        painter.setFont(font)
        painter.setPen(QColor(150, 150, 150))

        # 计算刻度间隔（根据总时长动态调整）
        tick_interval = self._calculate_tick_interval()

        # 绘制刻度
        current_time = 0
        while current_time <= self._total_duration:
            x = int((current_time / self._total_duration) * self.width())

            # 绘制刻度线
            tick_height = 10
            painter.drawLine(x, ruler_rect.bottom() - tick_height, x, ruler_rect.bottom())

            # 绘制时间标签
            time_text = self._format_time(current_time)
            text_rect = QRect(x - 30, ruler_rect.top(), 60, ruler_rect.height() - tick_height)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, time_text)

            current_time += tick_interval

    def _draw_playhead(self, painter: QPainter):
        """绘制播放指针"""
        if self._total_duration == 0:
            return

        x = int((self._current_position / self._total_duration) * self.width())

        # 绘制红色竖线
        pointer_color = QColor(255, 69, 58)  # Fluent 红色
        painter.setPen(QPen(pointer_color, 2))
        painter.drawLine(x, self._ruler_height, x, self.height())

        # 绘制顶部三角形指示器
        triangle = [
            QPoint(x, self._ruler_height),
            QPoint(x - 5, self._ruler_height - 8),
            QPoint(x + 5, self._ruler_height - 8),
        ]
        painter.setBrush(QBrush(pointer_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(triangle)

    def _calculate_tick_interval(self) -> int:
        """根据总时长动态计算刻度间隔（毫秒）"""
        duration_seconds = self._total_duration / 1000

        if duration_seconds <= 30:
            return 5000  # 5 秒
        elif duration_seconds <= 60:
            return 10000  # 10 秒
        elif duration_seconds <= 180:
            return 30000  # 30 秒
        else:
            return 60000  # 1 分钟

    def _format_time(self, milliseconds: int) -> str:
        """格式化时间为 MM:SS"""
        seconds = milliseconds // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"

    def mouseMoveEvent(self, event):
        """鼠标移动事件"""
        if self._is_dragging:
            # 拖动模式：更新位置但不发射信号（等待释放）
            self._hover_position = event.pos().x()
            self.update()
        else:
            # 悬停模式：显示预览
            self._hover_position = event.pos().x()
            self._hover_segment_index = self._find_segment_at_x(self._hover_position)

            # 延迟显示预览（防抖）
            self._preview_timer.stop()
            self._preview_timer.start(200)

        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        """鼠标按下事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            self._is_dragging = True
            self._hover_position = event.pos().x()
            self._preview.hide()

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        """鼠标释放事件"""
        if event.button() == Qt.MouseButton.LeftButton and self._is_dragging:
            self._is_dragging = False

            # 计算目标时间并发射信号
            if self._total_duration > 0:
                x = max(0, min(event.pos().x(), self.width()))
                target_time = int((x / self.width()) * self._total_duration)
                logger.debug(f"时间轴定位: {target_time}ms")
                self.seekRequested.emit(target_time)

        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        """鼠标离开事件"""
        self._hover_position = None
        self._hover_segment_index = None
        self._preview_timer.stop()
        self._preview.hide()
        super().leaveEvent(event)

    def _find_segment_at_x(self, x: int) -> Optional[int]:
        """根据 X 坐标查找对应的片段索引"""
        if self._total_duration == 0 or not self._segments:
            return None

        time_ms = int((x / self.width()) * self._total_duration)

        for i, segment in enumerate(self._segments):
            if segment.start_time <= time_ms < segment.start_time + segment.duration:
                return i

        return None

    def _show_preview(self):
        """显示预览窗口（由定时器触发）"""
        if self._hover_position is None or self._hover_segment_index is None:
            return

        if not (0 <= self._hover_segment_index < len(self._segments)):
            return

        segment = self._segments[self._hover_segment_index]

        # 计算悬停时间点
        time_ms = int((self._hover_position / self.width()) * self._total_duration)

        # 显示预览
        self._preview.show_preview(
            segment.thumbnail_path,
            time_ms,
            segment.scene_number,
            segment.shot_number
        )

        # 定位预览窗口
        global_pos = self.mapToGlobal(QPoint(self._hover_position, -self._preview.height() - 10))
        self._preview.move(global_pos)


def generate_segment_colors(count: int) -> List[QColor]:
    """生成 count 个视觉上易区分的颜色"""
    colors = []
    for i in range(count):
        hue = int(360 * i / count)  # 色相均匀分布 0-360°
        color = QColor.fromHsv(hue, 200, 220)  # 饱和度 200，明度 220
        colors.append(color)
    return colors
