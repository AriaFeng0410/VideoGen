#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化测试脚本 - 不需要安装额外依赖
测试核心视频合成功能
"""

import subprocess
from pathlib import Path
import os


def check_ffmpeg():
    """检查ffmpeg"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True)
        return result.returncode == 0
    except:
        return False


def generate_silent_audio(output_path: Path, duration: float):
    """使用ffmpeg生成静音音频"""
    cmd = [
        'ffmpeg', '-y',
        '-f', 'lavfi',
        '-i', f'anullsrc=r=44100:cl=stereo',
        '-t', str(duration),
        '-c:a', 'libmp3lame',
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True)


def generate_ass_subtitle(texts, durations, output_path: Path):
    """生成ASS字幕文件"""

    def seconds_to_ass_time(seconds):
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}:{minutes:02d}:{secs:05.2f}"

    header = """[Script Info]
Title: Test Subtitle
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,36,&H00FFFFFF,&H0000FFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,1,2,60,60,80,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    lines = [header]
    current_time = 0.0

    for i, (text, duration) in enumerate(zip(texts, durations)):
        start = seconds_to_ass_time(current_time)
        end = seconds_to_ass_time(current_time + duration)
        lines.append(f"Dialogue: 0,{start},{end},Default,,0,0,0,,{text}\n")
        current_time += duration

    with open(output_path, 'w', encoding='utf-8') as f:
        f.writelines(lines)


def create_image_sequence_video(images: list, durations: list, output_path: Path):
    """创建图片序列视频"""
    temp_dir = output_path.parent / "temp_concat"
    temp_dir.mkdir(exist_ok=True)

    # 创建concat文件
    concat_file = temp_dir / "concat.txt"
    with open(concat_file, 'w') as f:
        for img, duration in zip(images, durations):
            f.write(f"file '{img.absolute()}'\n")
            f.write(f"duration {duration}\n")
        f.write(f"file '{images[-1].absolute()}'\n")

    # 生成视频
    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', str(concat_file),
        '-vsync', 'vfr',
        '-pix_fmt', 'yuv420p',
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    return True


def merge_audio(audio_files: list, output_path: Path):
    """合并音频"""
    temp_dir = output_path.parent / "temp_concat"
    concat_file = temp_dir / "audio_concat.txt"
    with open(concat_file, 'w') as f:
        for audio in audio_files:
            f.write(f"file '{audio.absolute()}'\n")

    cmd = [
        'ffmpeg', '-y',
        '-f', 'concat',
        '-safe', '0',
        '-i', str(concat_file),
        '-c', 'copy',
        str(output_path)
    ]
    subprocess.run(cmd, capture_output=True)


def compose_final_video(video_path: Path, audio_path: Path, subtitle_path: Path, output_path: Path):
    """合成最终视频"""
    cmd = [
        'ffmpeg', '-y',
        '-i', str(video_path),
        '-i', str(audio_path),
        '-vf', f"ass='{subtitle_path.absolute()}'",
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-shortest',
        str(output_path)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    return True


def main():
    """主测试流程"""
    print("=" * 60)
    print("简化版视频生成测试")
    print("=" * 60)

    # 检查ffmpeg
    if not check_ffmpeg():
        print("错误: ffmpeg 未安装")
        return

    print("✓ ffmpeg 可用")

    # 准备目录
    base_dir = Path(__file__).parent
    input_dir = base_dir / "input" / "images"
    output_dir = base_dir / "output"
    temp_dir = base_dir / "temp" / "test"
    output_dir.mkdir(exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 获取测试图片
    images = sorted(input_dir.glob("*.jpg"))
    if not images:
        print("错误: 未找到测试图片")
        return

    print(f"✓ 找到 {len(images)} 张图片")
    for img in images:
        print(f"  - {img.name}")

    # 测试文本（按句号分割）
    test_text = """人工智能正在改变我���的生活方式。
从智能手机到自动驾驶汽车，AI技术已经渗透到我们日常生活的方方面面！
你是否想过，未来会是什么样子？
让我们一起探索这个充满可能性的世界。
科技让生活更美好，创新让未来更精彩。"""

    texts = [t.strip() for t in test_text.split('。') if t.strip()]
    # 处理带问号和感叹号的句子
    final_texts = []
    for t in texts:
        if '！' in t:
            final_texts.extend([s.strip() for s in t.split('！') if s.strip()])
        elif '？' in t:
            final_texts.extend([s.strip() for s in t.split('？') if s.strip()])
        else:
            if t:
                final_texts.append(t)

    print(f"\n✓ 文本分割为 {len(final_texts)} 个片段")
    for i, t in enumerate(final_texts):
        print(f"  [{i+1}] {t}")

    # 每个片段时长
    segment_duration = 3.0  # 每句话3秒
    durations = [segment_duration] * len(final_texts)
    total_duration = sum(durations)

    # 为每句话生成静音音频
    print(f"\n生成 {len(final_texts)} 个音频片段（共 {total_duration:.1f} 秒）...")
    audio_files = []
    for i, duration in enumerate(durations):
        audio_path = temp_dir / f"segment_{i:03d}.mp3"
        generate_silent_audio(audio_path, duration)
        audio_files.append(audio_path)
        print(f"  [{i+1}] {audio_path.name}")

    # 生成字幕
    print("\n生成字幕文件...")
    subtitle_path = temp_dir / "subtitle.ass"
    generate_ass_subtitle(final_texts, durations, subtitle_path)
    print(f"  ✓ {subtitle_path}")

    # 合并音频
    print("\n合并音频...")
    merged_audio = temp_dir / "merged_audio.mp3"
    merge_audio(audio_files, merged_audio)
    print(f"  ✓ {merged_audio}")

    # 计算每张图片时长
    image_duration = total_duration / len(images)
    image_durations = [image_duration] * len(images)

    # 创建图片序列视频
    print("\n创建图片序列视频...")
    image_video = temp_dir / "image_sequence.mp4"
    if create_image_sequence_video(images, image_durations, image_video):
        print(f"  ✓ {image_video}")
    else:
        print("  ✗ 创建失败")
        return

    # 合成最终视频
    print("\n合成最终视频...")
    final_video = output_dir / "demo_video.mp4"
    if compose_final_video(image_video, merged_audio, subtitle_path, final_video):
        print(f"\n{'=' * 60}")
        print("✓ 视频生成成功！")
        print(f"{'=' * 60}")
        print(f"输出文件: {final_video}")
        print(f"视频时长: {total_duration:.1f} 秒")
        print(f"���幕片段: {len(final_texts)} 个")
        print(f"图片数量: {len(images)} 张")

        # 获取视频信息
        cmd = ['ffprobe', '-v', 'error', '-show_entries',
               'format=duration,size', '-of', 'default=noprint_wrappers=1',
               str(final_video)]
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(f"\n视频信息:")
        print(result.stdout)
    else:
        print("  ✗ 合成失败")


if __name__ == '__main__':
    main()
