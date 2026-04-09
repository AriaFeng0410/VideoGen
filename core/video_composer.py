# -*- coding: utf-8 -*-
"""视频合成器 - FFmpeg命令封装"""

import subprocess
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class VideoConfig:
    """视频配置"""
    width: int = 1080
    height: int = 1920
    fps: int = 30
    codec: str = 'libx264'
    preset: str = 'medium'
    crf: int = 23
    audio_codec: str = 'aac'
    audio_bitrate: str = '192k'


class VideoComposer:
    """视频合成核心 - FFmpeg命令封装"""

    def __init__(self, temp_dir: Path, config: Optional[VideoConfig] = None):
        """
        Args:
            temp_dir: 临时文件目录
            config: 视频配置
        """
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.config = config or VideoConfig()

    def compose(self,
                images: List[Path],
                audio_files: List[Path],
                subtitle_path: Path,
                output_path: Path) -> Path:
        """
        合成最终视频

        Args:
            images: 图片路径列表
            audio_files: 音频文件路径列表
            subtitle_path: 字幕文件路径
            output_path: 输出视频路径

        Returns:
            输出视频路径
        """
        # 步骤1：合并音频
        merged_audio = self._merge_audio_files(audio_files)

        # 步骤2：获取音频总时长
        total_duration = self._get_audio_duration(merged_audio)

        # 步骤3：计算每张图片的时长
        durations = [total_duration / len(images)] * len(images)

        # 步骤4：创建图片序列视频
        image_video = self._create_image_sequence_video(images, durations)

        # 步骤5：合成最终视频（添加音频和字幕）
        final_video = self._compose_final_video(
            image_video,
            merged_audio,
            subtitle_path,
            output_path
        )

        return final_video

    def compose_simple(self,
                       image_paths: List[Path],
                       audio_paths: List[Path],
                       subtitle_path: Path,
                       output_path: Path) -> Path:
        """
        简化版合成（一步完成，效率更高）

        直接用FFmpeg滤镜链完成所有操作

        Args:
            image_paths: 图片路径列表
            audio_paths: 音频路径列表
            subtitle_path: 字幕路径
            output_path: 输出路径

        Returns:
            输出视频路径
        """
        # 第一步：合并音频获取总时长
        merged_audio = self._merge_audio_files(audio_paths)
        total_duration = self._get_audio_duration(merged_audio)

        # 第二步：创建图片序列视频
        durations = [total_duration / len(image_paths)] * len(image_paths)
        image_video = self._create_image_sequence_video(image_paths, durations)

        # 第三步：合成最终视频
        return self._compose_final_video(
            image_video,
            merged_audio,
            subtitle_path,
            output_path
        )

    def _create_image_sequence_video(self,
                                      images: List[Path],
                                      durations: List[float]) -> Path:
        """
        创建图片序列视频

        Args:
            images: 图片路径列表
            durations: 每张图片的时长列表

        Returns:
            生成的视频路径
        """
        output_path = self.temp_dir / "image_sequence.mp4"

        # 创建concat文件
        concat_file = self.temp_dir / "concat.txt"
        with open(concat_file, 'w', encoding='utf-8') as f:
            for img, duration in zip(images, durations):
                # 使用绝对路径
                abs_path = img.absolute()
                f.write(f"file '{abs_path}'\n")
                f.write(f"duration {duration}\n")
            # FFmpeg要求最后一张图片再写一次
            f.write(f"file '{images[-1].absolute()}'\n")

        # FFmpeg命令
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
            '-vsync', 'vfr',
            '-pix_fmt', 'yuv420p',
            '-c:v', self.config.codec,
            '-preset', self.config.preset,
            '-crf', str(self.config.crf),
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg错误: {result.stderr}")

        return output_path

    def _merge_audio_files(self, audio_files: List[Path]) -> Path:
        """
        合并多个音频文件

        Args:
            audio_files: 音频文件列表

        Returns:
            合并后的音频路径
        """
        output_path = self.temp_dir / "merged_audio.mp3"

        # 创建concat文件
        concat_file = self.temp_dir / "audio_concat.txt"
        with open(concat_file, 'w', encoding='utf-8') as f:
            for audio in audio_files:
                f.write(f"file '{audio.absolute()}'\n")

        # FFmpeg命令（无损合并）
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', str(concat_file),
            '-c', 'copy',
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg音频合并错误: {result.stderr}")

        return output_path

    def _compose_final_video(self,
                             image_video: Path,
                             audio: Path,
                             subtitle_path: Path,
                             output_path: Path) -> Path:
        """
        合成最终视频（添加音频和字幕）

        使用软字幕方式，将字幕作为独立轨道嵌入视频容器

        Args:
            image_video: 图片序列视频
            audio: 音频文件
            subtitle_path: 字幕文件
            output_path: 输出路径

        Returns:
            输出视频路径
        """
        # FFmpeg命令 - 使用软字幕（嵌入字幕轨道，不硬编码到画面）
        # 优势：不需要 libass 支持，字幕可选择开启/关闭
        # -map 参数：明确指定要使用的输入流
        #   -map 0:v  使用第1个输入的视频流
        #   -map 1:a  使用第2个输入的音频流
        #   -map 2:s  使用第3个输入的字幕流
        cmd = [
            'ffmpeg', '-y',
            '-i', str(image_video),
            '-i', str(audio),
            '-i', str(subtitle_path),
            '-map', '0:v',
            '-map', '1:a',
            '-map', '2:s',
            '-c:v', self.config.codec,
            '-preset', self.config.preset,
            '-crf', str(self.config.crf),
            '-c:a', self.config.audio_codec,
            '-b:a', self.config.audio_bitrate,
            '-c:s', 'mov_text',  # 使用 mov_text 编码器（MP4容器支持）
            '-metadata:s:s:0', 'language=chi',  # 设置字幕语言为中文
            '-shortest',
            str(output_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"FFmpeg最终合成错误: {result.stderr}")

        return output_path

    def _get_audio_duration(self, audio_path: Path) -> float:
        """
        获取音频时长

        Args:
            audio_path: 音频路径

        Returns:
            时长（秒）
        """
        cmd = [
            'ffprobe',
            '-v', 'error',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            str(audio_path)
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffprobe错误: {result.stderr}")

        return float(result.stdout.strip())

    def check_ffmpeg(self) -> bool:
        """检查FFmpeg是否可用"""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True)
            subprocess.run(['ffprobe', '-version'], capture_output=True)
            return True
        except FileNotFoundError:
            return False


def main():
    """测试视频合成器"""
    composer = VideoComposer(Path("./temp"))

    print("=" * 50)
    print("视频合成器测试")
    print("=" * 50)

    # 检查FFmpeg
    if composer.check_ffmpeg():
        print("✓ FFmpeg 可用")
    else:
        print("✗ FFmpeg 不可用，请先安装")


if __name__ == '__main__':
    main()
