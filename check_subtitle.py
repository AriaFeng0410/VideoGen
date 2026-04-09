#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查视频字幕信息"""

import subprocess
from pathlib import Path

def check_subtitle_tracks(video_path):
    """检查视频中的字幕轨道"""
    cmd = [
        'ffprobe', '-v', 'error',
        '-show_entries', 'stream=index,codec_type,codec_name,codec_long_name,tags',
        '-of', 'default=noprint_wrappers=1',
        str(video_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    print("=" * 60)
    print(f"视频文件: {video_path}")
    print("=" * 60)
    print(result.stdout)

    # 统计轨道数量
    lines = result.stdout.split('\n')
    video_count = sum(1 for line in lines if 'codec_type=video' in line)
    audio_count = sum(1 for line in lines if 'codec_type=audio' in line)
    subtitle_count = sum(1 for line in lines if 'codec_type=subtitle' in line)

    print(f"\n轨道统计:")
    print(f"  视频轨道: {video_count}")
    print(f"  音频轨道: {audio_count}")
    print(f"  字幕轨道: {subtitle_count}")

    if subtitle_count > 0:
        print("\n✓ 视频包含字幕轨道（软字幕）")
        print("\n提示：软字幕需要在播放器中手动开启才能显示")
        print("常用播放器：")
        print("  - VLC: 副标题 -> 字幕轨道 -> 选择字幕")
        print("  - QuickTime: 显示 -> 副标题")
        print("  - IINA: 字幕 -> 选择字幕轨")
    else:
        print("\n✗ 视频不包含字幕轨道")


def extract_subtitle(video_path, output_srt):
    """从视频中提取字幕"""
    cmd = [
        'ffmpeg', '-y',
        '-i', str(video_path),
        '-map', '0:s:0',  # 选择第一个字幕轨道
        str(output_srt)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"\n✓ 字幕已提取到: {output_srt}")
        return True
    else:
        print(f"\n✗ 提取字幕失败: {result.stderr}")
        return False


if __name__ == '__main__':
    video_path = Path('output/video.mp4')

    if video_path.exists():
        check_subtitle_tracks(video_path)

        # 提取字幕供查看
        output_srt = Path('output/extracted_subtitle.srt')
        extract_subtitle(video_path, output_srt)
    else:
        print(f"视频文件不存在: {video_path}")% 
