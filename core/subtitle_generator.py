# -*- coding: utf-8 -*-
"""字幕生成器 - 生成ASS/SRT格式字幕"""

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class SubtitleEntry:
    """字幕条目"""
    index: int
    start_time: float  # 秒
    end_time: float    # 秒
    text: str


class SubtitleGenerator:
    """字幕生成器 - 生成SRT/ASS格式字幕"""

    def __init__(self, style_config: Optional[dict] = None):
        """
        Args:
            style_config: 字幕样式配置
                - font_name: 字体名称
                - font_size: 字体大小
                - primary_color: 主要颜色（ASS格式）
                - outline_color: 描边颜色
                - outline: 描边宽度
                - shadow: 阴影深度
                - margin_vertical: 底部边距
                - alignment: 对齐方式（2=底部居中）
        """
        self.style_config = style_config or self._default_style()

    def _default_style(self) -> dict:
        """默认字幕样式"""
        return {
            'font_name': 'Source Han Sans CN Bold',
            'font_size': 36,
            'primary_color': '&H00FFFFFF',    # 白色
            'outline_color': '&H00000000',    # 黑色
            'outline': 2,
            'shadow': 1,
            'margin_vertical': 80,
            'alignment': 2,  # 底部居中
        }

    def generate_srt(self, entries: List[SubtitleEntry], output_path: Path) -> Path:
        """
        生成SRT字幕文件

        Args:
            entries: 字幕条目列表
            output_path: 输出路径

        Returns:
            生成的文件路径
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            for entry in entries:
                start = self._seconds_to_srt_time(entry.start_time)
                end = self._seconds_to_srt_time(entry.end_time)

                f.write(f"{entry.index}\n")
                f.write(f"{start} --> {end}\n")
                f.write(f"{entry.text}\n\n")

        return output_path

    def generate_ass(self,
                     entries: List[SubtitleEntry],
                     output_path: Path,
                     video_width: int = 1080,
                     video_height: int = 1920) -> Path:
        """
        生成ASS字幕文件

        Args:
            entries: 字幕条目列表
            output_path: 输出路径
            video_width: 视频宽度
            video_height: 视频高度

        Returns:
            生成的文件路径
        """
        content = self._build_ass_header(video_width, video_height)
        content += self._build_ass_style()
        content += self._build_ass_events(entries)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return output_path

    def create_from_durations(self,
                              texts: List[str],
                              durations: List[float],
                              output_path: Path,
                              format: str = 'ass') -> Path:
        """
        从文本和时长列表生成字幕

        Args:
            texts: 文本列表
            durations: 每段时长列表（秒）
            output_path: 输出路径
            format: 'srt' 或 'ass'
        """
        entries = []
        current_time = 0.0

        for i, (text, duration) in enumerate(zip(texts, durations)):
            entry = SubtitleEntry(
                index=i + 1,
                start_time=current_time,
                end_time=current_time + duration,
                text=text
            )
            entries.append(entry)
            current_time += duration

        if format == 'ass':
            return self.generate_ass(entries, output_path)
        else:
            return self.generate_srt(entries, output_path)

    def _build_ass_header(self, width: int, height: int) -> str:
        """构建ASS文件头"""
        return f"""[Script Info]
Title: Video Generator Subtitle
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: {width}
PlayResY: {height}

"""

    def _build_ass_style(self) -> str:
        """构建ASS样式"""
        style = self.style_config

        return f"""[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,{style.get('font_name', 'Source Han Sans CN Bold')},{style.get('font_size', 36)},{style.get('primary_color', '&H00FFFFFF')},&H0000FFFF,{style.get('outline_color', '&H00000000')},&H80000000,0,0,0,0,100,100,0,0,1,{style.get('outline', 2)},{style.get('shadow', 1)},{style.get('alignment', 2)},60,60,{style.get('margin_vertical', 80)},1

"""

    def _build_ass_events(self, entries: List[SubtitleEntry]) -> str:
        """构建ASS事件"""
        lines = ["[Events]\n", "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"]

        for entry in entries:
            start = self._seconds_to_ass_time(entry.start_time)
            end = self._seconds_to_ass_time(entry.end_time)
            lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{entry.text}\n")

        return "".join(lines)

    @staticmethod
    def _seconds_to_srt_time(seconds: float) -> str:
        """
        将秒数转换为SRT时间格式

        Args:
            seconds: 秒数

        Returns:
            格式: 00:00:00,000
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)

        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

    @staticmethod
    def _seconds_to_ass_time(seconds: float) -> str:
        """
        将秒数转换为ASS时间格式

        Args:
            seconds: 秒数

        Returns:
            格式: 0:00:00.00
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60

        return f"{hours}:{minutes:02d}:{secs:05.2f}"


def main():
    """测试字幕生成"""
    generator = SubtitleGenerator()

    # 测试数据
    entries = [
        SubtitleEntry(1, 0.0, 3.5, "这是第一句话。"),
        SubtitleEntry(2, 3.5, 7.2, "这是第二句话！"),
        SubtitleEntry(3, 7.2, 11.0, "这是第三句话？"),
    ]

    print("=" * 50)
    print("字幕生��测试")
    print("=" * 50)

    # 生成ASS
    output_path = Path("./temp/test_subtitle.ass")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    generator.generate_ass(entries, output_path)
    print(f"\nASS字幕已生成: {output_path}")

    # 生成SRT
    srt_path = Path("./temp/test_subtitle.srt")
    generator.generate_srt(entries, srt_path)
    print(f"SRT字幕已生成: {srt_path}")

    # 显示内容
    print("\nASS内容:")
    print("-" * 30)
    print(output_path.read_text(encoding='utf-8'))


if __name__ == '__main__':
    main()
