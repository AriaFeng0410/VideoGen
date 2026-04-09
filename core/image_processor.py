# -*- coding: utf-8 -*-
"""图片处理器 - 适配竖屏格式"""

from pathlib import Path
from typing import List, Tuple, Optional
from dataclasses import dataclass

try:
    from PIL import Image
except ImportError:
    raise ImportError("请安装 Pillow: pip install Pillow")


@dataclass
class ImageInfo:
    """图片信息"""
    path: Path
    width: int
    height: int
    duration: float  # 显示时长（秒）


class ImageProcessor:
    """图片处理器 - 适配竖屏格式"""

    # 视频号目标规格
    TARGET_WIDTH = 1080
    TARGET_HEIGHT = 1920
    TARGET_RATIO = 9 / 16

    def __init__(self, output_dir: Path):
        """
        Args:
            output_dir: 处理后图片输出目录
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def process_image(self,
                      image_path: Path,
                      duration: float,
                      background_color: Tuple[int, int, int] = (0, 0, 0),
                      scale_mode: str = 'fit') -> ImageInfo:
        """
        处理单张图片，适配竖屏格式

        Args:
            image_path: ���片路径
            duration: 显示时长（秒）
            background_color: 背景颜色 (R, G, B)
            scale_mode: 缩放模式
                - 'fit': 保持比例，居中放置（推荐）
                - 'fill': 填充画布，裁剪超出部分
                - 'stretch': 拉伸填充（不推荐）

        Returns:
            ImageInfo 对象
        """
        # 读取原图
        img = Image.open(image_path)

        # 转换为RGB模式（处理PNG透明通道）
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, background_color)
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # 根据模式处理
        if scale_mode == 'fit':
            processed = self._scale_fit(img, background_color)
        elif scale_mode == 'fill':
            processed = self._scale_fill(img)
        else:
            processed = self._scale_stretch(img)

        # 保存处理后的图片
        output_path = self.output_dir / f"processed_{image_path.stem}.jpg"
        processed.save(output_path, 'JPEG', quality=95)

        return ImageInfo(
            path=output_path,
            width=self.TARGET_WIDTH,
            height=self.TARGET_HEIGHT,
            duration=duration
        )

    def _scale_fit(self,
                   img: Image.Image,
                   bg_color: Tuple[int, int, int]) -> Image.Image:
        """
        保持比例缩放，居中放置

        Args:
            img: 原图
            bg_color: 背景颜色

        Returns:
            处理后的图片
        """
        # 创建画布
        canvas = Image.new('RGB', (self.TARGET_WIDTH, self.TARGET_HEIGHT), bg_color)

        # 计算缩放比例
        orig_width, orig_height = img.size
        scale = min(
            self.TARGET_WIDTH / orig_width,
            self.TARGET_HEIGHT / orig_height
        )

        new_width = int(orig_width * scale)
        new_height = int(orig_height * scale)

        # 缩放图片
        resized = img.resize((new_width, new_height), Image.LANCZOS)

        # 计算居中位置
        x = (self.TARGET_WIDTH - new_width) // 2
        y = (self.TARGET_HEIGHT - new_height) // 2

        # 粘贴到画布
        canvas.paste(resized, (x, y))

        return canvas

    def _scale_fill(self, img: Image.Image) -> Image.Image:
        """
        填充模式：缩放并裁剪

        Args:
            img: 原图

        Returns:
            处理后的图片
        """
        orig_width, orig_height = img.size

        # 计算缩放比例（覆盖整个画布）
        scale = max(
            self.TARGET_WIDTH / orig_width,
            self.TARGET_HEIGHT / orig_height
        )

        new_width = int(orig_width * scale)
        new_height = int(orig_height * scale)

        # 缩放
        resized = img.resize((new_width, new_height), Image.LANCZOS)

        # 计算裁剪位置（居中裁剪）
        left = (new_width - self.TARGET_WIDTH) // 2
        top = (new_height - self.TARGET_HEIGHT) // 2
        right = left + self.TARGET_WIDTH
        bottom = top + self.TARGET_HEIGHT

        # 裁剪
        cropped = resized.crop((left, top, right, bottom))

        return cropped

    def _scale_stretch(self, img: Image.Image) -> Image.Image:
        """
        拉伸模式：直接拉伸到目标尺寸

        Args:
            img: 原图

        Returns:
            处理后的图片
        """
        return img.resize((self.TARGET_WIDTH, self.TARGET_HEIGHT), Image.LANCZOS)

    def calculate_durations(self,
                            image_count: int,
                            total_audio_duration: float,
                            mode: str = 'average',
                            custom_durations: Optional[List[float]] = None) -> List[float]:
        """
        计算每张图片的显示时长

        Args:
            image_count: 图片数量
            total_audio_duration: 总音频时长（秒）
            mode: 分配模式
                - 'average': 平均分配
                - 'custom': 自定义
            custom_durations: 自定义时长列表

        Returns:
            每张图片的时长列表
        """
        if mode == 'custom' and custom_durations:
            return custom_durations[:image_count]

        # 平均分配
        duration_per_image = total_audio_duration / image_count
        return [duration_per_image] * image_count

    def process_batch(self,
                      image_paths: List[Path],
                      durations: List[float],
                      background_color: Tuple[int, int, int] = (0, 0, 0),
                      scale_mode: str = 'fit') -> List[ImageInfo]:
        """
        批量处理图片

        Args:
            image_paths: 图片路径列表
            durations: 每张图片的时长列表
            background_color: 背景颜色
            scale_mode: 缩放模式

        Returns:
            ImageInfo列表
        """
        results = []
        for i, (img_path, duration) in enumerate(zip(image_paths, durations)):
            info = self.process_image(
                img_path,
                duration,
                background_color=background_color,
                scale_mode=scale_mode
            )
            results.append(info)
        return results


def main():
    """测试图片处理"""
    import sys

    # 测试输出目录
    output_dir = Path("./temp/processed_images")
    output_dir.mkdir(parents=True, exist_ok=True)

    processor = ImageProcessor(output_dir)

    print("=" * 50)
    print("图片处理器测试")
    print("=" * 50)
    print(f"目标分辨率: {processor.TARGET_WIDTH}x{processor.TARGET_HEIGHT}")
    print(f"输出目录: {output_dir}")

    # 计算时长分配
    durations = processor.calculate_durations(3, 10.5, mode='average')
    print(f"\n假设3张图片，总时长10.5秒:")
    for i, d in enumerate(durations):
        print(f"  图片{i+1}: {d:.2f}秒")


if __name__ == '__main__':
    main()
