#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频号视频生成工具
基于 Python + FFmpeg + Edge-TTS

使用方法:
    python main.py -t input/text/script.txt -i input/images -o output/video.mp4
    python main.py -p input/project.yaml
"""

import asyncio
import argparse
import sys
from pathlib import Path
from typing import Optional
import yaml

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.workflow import VideoWorkflow, WorkflowConfig
from utils.text_splitter import TextSplitter


def load_config(config_path: Optional[Path] = None) -> WorkflowConfig:
    """加载配置文件"""
    if config_path and config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        return parse_config_dict(config_dict)

    # 尝试加载默认配置
    default_config = Path(__file__).parent / 'config' / 'default_config.yaml'
    if default_config.exists():
        with open(default_config, 'r', encoding='utf-8') as f:
            config_dict = yaml.safe_load(f)
        return parse_config_dict(config_dict)

    return WorkflowConfig()


def parse_config_dict(config_dict: dict) -> WorkflowConfig:
    """解析配置字典"""
    config = WorkflowConfig()

    if 'tts' in config_dict:
        tts = config_dict['tts']
        config.voice = tts.get('voice', config.voice)
        config.speech_rate = tts.get('rate', config.speech_rate)
        config.speech_volume = tts.get('volume', config.speech_volume)

    if 'text_split' in config_dict:
        config.max_segment_length = config_dict['text_split'].get(
            'max_segment_length', config.max_segment_length
        )

    if 'subtitle' in config_dict:
        sub = config_dict['subtitle']
        config.subtitle_format = sub.get('format', config.subtitle_format)
        if 'style' in sub:
            style = sub['style']
            config.font_name = style.get('font_name', config.font_name)
            config.font_size = style.get('font_size', config.font_size)
            config.font_primary_color = style.get('primary_color', config.font_primary_color)
            config.font_outline_color = style.get('outline_color', config.font_outline_color)
            config.font_outline = style.get('outline', config.font_outline)
            config.font_shadow = style.get('shadow', config.font_shadow)
            config.margin_vertical = style.get('margin_vertical', config.margin_vertical)

    if 'image' in config_dict:
        img = config_dict['image']
        config.image_scale_mode = img.get('scale_mode', config.image_scale_mode)
        if 'background_color' in img:
            config.image_background = tuple(img['background_color'])

    if 'video' in config_dict:
        vid = config_dict['video']
        config.video_preset = vid.get('preset', config.video_preset)
        config.video_crf = vid.get('crf', config.video_crf)

    return config


def load_text(text_path: Path) -> str:
    """加载文本文件"""
    with open(text_path, 'r', encoding='utf-8') as f:
        return f.read().strip()


def get_image_list(image_dir: Path) -> list:
    """获取图片列表"""
    supported_extensions = ['.jpg', '.jpeg', '.png', '.webp', '.bmp']
    images = []

    for ext in supported_extensions:
        images.extend(image_dir.glob(f'*{ext}'))
        images.extend(image_dir.glob(f'*{ext.upper()}'))

    # 按文件名排序
    return sorted(images, key=lambda x: x.name.lower())


async def generate_video(text: str,
                        images: list,
                        output_path: Path,
                        config: WorkflowConfig,
                        temp_dir: Path) -> Path:
    """生成视频"""
    workflow = VideoWorkflow(config)
    result = await workflow.run(text, images, output_path, temp_dir)
    return result.output_path


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='视频号视频生成工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 基本用法
  python main.py -t input/text/script.txt -i input/images -o output/video.mp4

  # 使用项目配置文件
  python main.py -p input/project.yaml

  # 指定语音和语速
  python main.py -t text.txt -i images/ -o video.mp4 --voice zh-CN-YunxiNeural --rate +20%

  # 高质量输出
  python main.py -t text.txt -i images/ -o video.mp4 --preset slow --crf 18

可用语音:
  - zh-CN-XiaoxiaoNeural: 女声温柔（推荐）
  - zh-CN-XiaoyiNeural: 女声活泼
  - zh-CN-YunxiNeural: 男声标准
  - zh-CN-YunjianNeural: 男声解说
        """
    )

    # 输入参数
    parser.add_argument('-t', '--text', type=Path,
                       help='文本文件路径')
    parser.add_argument('-i', '--images', type=Path,
                       help='图片目录路径')
    parser.add_argument('-o', '--output', type=Path,
                       default=Path('output/video.mp4'),
                       help='输出视频路径（默认: output/video.mp4）')

    # 配置参数
    parser.add_argument('-c', '--config', type=Path,
                       help='配置文件路径')
    parser.add_argument('-p', '--project', type=Path,
                       help='项目配置文件路径（包含所有素材路径）')

    # TTS参数
    parser.add_argument('--voice', type=str,
                       help='Edge-TTS语音名称')
    parser.add_argument('--rate', type=str,
                       help='语速调整（如 +20%%, -10%%）')

    # 字幕参数
    parser.add_argument('--font', type=str,
                       help='字幕字体名称')
    parser.add_argument('--font-size', type=int,
                       help='字幕字体大小')

    # 视频参数
    parser.add_argument('--preset', type=str,
                       help='编码预设 (fast/medium/slow)')
    parser.add_argument('--crf', type=int,
                       help='视频质量参数（18-28）')

    args = parser.parse_args()

    # 加载配置
    config = load_config(args.config)

    # 应用命令行参数覆盖
    if args.voice:
        config.voice = args.voice
    if args.rate:
        config.speech_rate = args.rate
    if args.font:
        config.font_name = args.font
    if args.font_size:
        config.font_size = args.font_size
    if args.preset:
        config.video_preset = args.preset
    if args.crf:
        config.video_crf = args.crf

    # 处理项目配置
    if args.project:
        with open(args.project, 'r', encoding='utf-8') as f:
            project = yaml.safe_load(f)

        base_dir = args.project.parent
        text_path = base_dir / project['inputs']['text_file']

        if 'images' in project['inputs']:
            images = [base_dir / img for img in project['inputs']['images']]
        else:
            images = get_image_list(base_dir / project['inputs']['images_dir'])

        output_path = base_dir / project['output']['filename']

        # 应用项目覆盖配置
        if 'overrides' in project:
            for key, value in project['overrides'].items():
                if hasattr(config, key):
                    if isinstance(value, dict):
                        for k, v in value.items():
                            if hasattr(config, k):
                                setattr(config, k, v)
                    else:
                        setattr(config, key, value)
    else:
        if not args.text or not args.images:
            parser.error('需要提供 -t/--text 和 -i/--images 参数，或使用 -p/--project 指定项目文件')

        text_path = args.text
        images = get_image_list(args.images)
        output_path = args.output

    # 验证输入
    if not text_path.exists():
        print(f"错误：文本文件不存在: {text_path}")
        sys.exit(1)

    if not images:
        print("错误：未找到图片文件")
        sys.exit(1)

    # 创建必要的目录
    output_path.parent.mkdir(parents=True, exist_ok=True)
    temp_dir = Path('./temp')
    temp_dir.mkdir(exist_ok=True)

    # 加载文本
    text = load_text(text_path)

    # 显示配置信息
    print("""
╔════════════════════════════════════════════════════════════════╗
║                    视频��视频生成工具                          ║
╚════════════════════════════════════════════════════════════════╝
""")
    print("配置信息:")
    print(f"  语音: {config.voice}")
    print(f"  语速: {config.speech_rate}")
    print(f"  字体: {config.font_name} ({config.font_size}px)")
    print(f"  编码: {config.video_preset} (CRF={config.video_crf})")
    print()
    print("输入:")
    print(f"  文本: {text_path}")
    print(f"  图片: {len(images)} 张")
    print(f"  文本长度: {len(text)} 字符")
    print()
    print("输出:")
    print(f"  视频文件: {output_path}")
    print()

    # 执行视频生成
    try:
        result = asyncio.run(generate_video(text, images, output_path, config, temp_dir))
        print(f"\n成功生成视频: {result}")
    except KeyboardInterrupt:
        print("\n\n用户取消操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
