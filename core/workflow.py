# -*- coding: utf-8 -*-
"""工作流编排 - 协调各模块执行"""

import asyncio
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass, field
import yaml

from .tts_engine import TTSEngine, TTSResult
from .subtitle_generator import SubtitleGenerator
from .image_processor import ImageProcessor, ImageInfo
from .video_composer import VideoComposer, VideoConfig
from utils.text_splitter import TextSplitter, TextSegment


@dataclass
class WorkflowConfig:
    """工作流配置"""
    # TTS配置
    voice: str = 'zh-CN-XiaoxiaoNeural'
    speech_rate: str = '+0%'
    speech_volume: str = '+0%'

    # 字幕配置
    subtitle_format: str = 'ass'
    font_name: str = 'Source Han Sans CN Bold'
    font_size: int = 36
    font_primary_color: str = '&H00FFFFFF'
    font_outline_color: str = '&H00000000'
    font_outline: int = 2
    font_shadow: int = 1
    margin_vertical: int = 80

    # 图片配置
    image_scale_mode: str = 'fit'
    image_background: tuple = (0, 0, 0)

    # 视频配置
    video_preset: str = 'medium'
    video_crf: int = 23

    # 文本分割
    max_segment_length: int = 50

    def get_subtitle_style(self) -> dict:
        """获取字幕样式配置"""
        return {
            'font_name': self.font_name,
            'font_size': self.font_size,
            'primary_color': self.font_primary_color,
            'outline_color': self.font_outline_color,
            'outline': self.font_outline,
            'shadow': self.font_shadow,
            'margin_vertical': self.margin_vertical,
        }

    def get_video_config(self) -> VideoConfig:
        """获取视频配置"""
        return VideoConfig(
            preset=self.video_preset,
            crf=self.video_crf
        )


@dataclass
class WorkflowResult:
    """工作流执行结果"""
    output_path: Path
    total_duration: float
    segment_count: int
    image_count: int


class VideoWorkflow:
    """视频生成工作流"""

    def __init__(self, config: Optional[WorkflowConfig] = None):
        """
        Args:
            config: 工作流配置
        """
        self.config = config or WorkflowConfig()

        # 初始化各模块
        self.text_splitter = TextSplitter(self.config.max_segment_length)
        self.tts_engine = TTSEngine(
            voice=self.config.voice,
            rate=self.config.speech_rate,
            volume=self.config.speech_volume
        )
        self.subtitle_generator = SubtitleGenerator(
            self.config.get_subtitle_style()
        )

    async def run(self,
                  text: str,
                  images: List[Path],
                  output_path: Path,
                  temp_dir: Optional[Path] = None) -> WorkflowResult:
        """
        执行完整工作流

        Args:
            text: 输入文本
            images: 图片路径列表
            output_path: 输出视频路径
            temp_dir: 临时文件目录

        Returns:
            WorkflowResult
        """
        if temp_dir is None:
            temp_dir = Path('./temp')
        temp_dir.mkdir(parents=True, exist_ok=True)

        print("=" * 60)
        print("视频生成工作流")
        print("=" * 60)

        # ============ 步骤1：文本分割 ============
        print("\n[步骤1/5] 分割文本...")
        segments = self.text_splitter.split(text)
        print(f"  共分割为 {len(segments)} 个片段")
        for seg in segments[:3]:
            print(f"    [{seg.index}] {seg.text[:30]}{'...' if len(seg.text) > 30 else ''}")
        if len(segments) > 3:
            print(f"    ... 共 {len(segments)} 个片段")

        # ============ 步骤2：生成TTS音频 ============
        print("\n[步骤2/5] 生成TTS音频...")
        audio_dir = temp_dir / "audio"
        tts_results = await self.tts_engine.batch_generate(
            [seg.text for seg in segments],
            audio_dir
        )
        total_duration = sum(r.duration for r in tts_results)
        print(f"  生成 {len(tts_results)} 个音频文件")
        print(f"  总时长: {total_duration:.2f} 秒")

        # ============ 步骤3：生成字幕 ============
        print("\n[步骤3/5] 生成字幕...")
        subtitle_path = temp_dir / "subtitle.ass"
        self.subtitle_generator.create_from_durations(
            [r.text for r in tts_results],
            [r.duration for r in tts_results],
            subtitle_path,
            format=self.config.subtitle_format
        )
        print(f"  字幕文件: {subtitle_path}")

        # ============ 步骤4：处理图片 ============
        print("\n[步骤4/5] 处理图片...")
        image_processor = ImageProcessor(temp_dir / "images")

        # 计算每张图片的显示时长
        image_durations = image_processor.calculate_durations(
            len(images),
            total_duration,
            mode='average'
        )

        processed_images = image_processor.process_batch(
            images,
            image_durations,
            background_color=self.config.image_background,
            scale_mode=self.config.image_scale_mode
        )
        print(f"  处理 {len(processed_images)} 张图片")
        for i, img in enumerate(processed_images):
            print(f"    [{i+1}] {img.path.name} -> {img.duration:.2f}s")

        # ============ 步骤5：合成视频 ============
        print("\n[步骤5/5] 合成视频...")
        video_composer = VideoComposer(temp_dir, self.config.get_video_config())

        # 检查FFmpeg
        if not video_composer.check_ffmpeg():
            raise RuntimeError("FFmpeg 不可用，请先安装 FFmpeg")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        final_video = video_composer.compose(
            images=[img.path for img in processed_images],
            audio_files=[r.audio_path for r in tts_results],
            subtitle_path=subtitle_path,
            output_path=output_path
        )

        # ============ 完成 ============
        print("\n" + "=" * 60)
        print("视频生成完成！")
        print("=" * 60)
        print(f"  输出文件: {final_video}")
        print(f"  视频时长: {total_duration:.2f} 秒")
        print(f"  字幕片段: {len(segments)} 个")
        print(f"  图片数量: {len(images)} 张")
        print("=" * 60)

        return WorkflowResult(
            output_path=final_video,
            total_duration=total_duration,
            segment_count=len(segments),
            image_count=len(images)
        )

    @classmethod
    def from_config_file(cls, config_path: Path) -> 'VideoWorkflow':
        """
        从配置文件创建工作流

        Args:
            config_path: 配置文件路径

        Returns:
            VideoWorkflow 实例
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)

        # 解析配置
        config = WorkflowConfig()

        if 'tts' in config_dict:
            tts_cfg = config_dict['tts']
            config.voice = tts_cfg.get('voice', config.voice)
            config.speech_rate = tts_cfg.get('rate', config.speech_rate)
            config.speech_volume = tts_cfg.get('volume', config.speech_volume)

        if 'text_split' in config_dict:
            config.max_segment_length = config_dict['text_split'].get(
                'max_segment_length', config.max_segment_length
            )

        if 'subtitle' in config_dict:
            sub_cfg = config_dict['subtitle']
            config.subtitle_format = sub_cfg.get('format', config.subtitle_format)
            if 'style' in sub_cfg:
                style = sub_cfg['style']
                config.font_name = style.get('font_name', config.font_name)
                config.font_size = style.get('font_size', config.font_size)

        if 'image' in config_dict:
            img_cfg = config_dict['image']
            config.image_scale_mode = img_cfg.get('scale_mode', config.image_scale_mode)

        if 'video' in config_dict:
            vid_cfg = config_dict['video']
            config.video_preset = vid_cfg.get('preset', config.video_preset)
            config.video_crf = vid_cfg.get('crf', config.video_crf)

        return cls(config)


async def test_workflow():
    """测试工作流"""
    config = WorkflowConfig(
        voice='zh-CN-XiaoxiaoNeural',
        font_name='Source Han Sans CN Bold'
    )

    workflow = VideoWorkflow(config)

    print("工作流配置:")
    print(f"  语音: {config.voice}")
    print(f"  字体: {config.font_name}")
    print(f"  视频预设: {config.video_preset}")


if __name__ == '__main__':
    asyncio.run(test_workflow())
