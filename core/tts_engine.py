# -*- coding: utf-8 -*-
"""TTS引擎 - Edge-TTS封装"""

import asyncio
import subprocess
from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass

try:
    import edge_tts
except ImportError:
    raise ImportError("请安装 edge-tts: pip install edge-tts")


@dataclass
class TTSResult:
    """TTS生成结果"""
    audio_path: Path
    duration: float      # 音频时长（秒）
    text: str
    segment_index: int


class TTSEngine:
    """Edge-TTS 封装"""

    # 常用中文语音
    CHINESE_VOICES = {
        'female_soft': 'zh-CN-XiaoxiaoNeural',      # 女声温柔（推荐）
        'female_lively': 'zh-CN-XiaoyiNeural',      # 女声活泼
        'male_standard': 'zh-CN-YunxiNeural',       # 男声标准
        'male_narration': 'zh-CN-YunjianNeural',    # 男声解说
    }

    def __init__(self,
                 voice: str = 'zh-CN-XiaoxiaoNeural',
                 rate: str = '+0%',
                 volume: str = '+0%'):
        """
        Args:
            voice: 语音名称
            rate: 语速调整 (-50% to +100%)
            volume: 音量调整 (-50% to +100%)
        """
        self.voice = voice
        self.rate = rate
        self.volume = volume

    async def generate_audio(self, text: str, output_path: Path) -> TTSResult:
        """
        生成单个音频文件

        Args:
            text: 要转换的文本
            output_path: 输出路径

        Returns:
            TTSResult 对象
        """
        # 创建通信对象
        communicate = edge_tts.Communicate(
            text=text,
            voice=self.voice,
            rate=self.rate,
            volume=self.volume
        )

        # 保存音频
        await communicate.save(str(output_path))

        # 获取时长
        duration = self._get_audio_duration(output_path)

        return TTSResult(
            audio_path=output_path,
            duration=duration,
            text=text,
            segment_index=0
        )

    async def batch_generate(self,
                             texts: List[str],
                             output_dir: Path) -> List[TTSResult]:
        """
        批量生成音频（并行处理）

        Args:
            texts: 文本列表
            output_dir: 输出目录

        Returns:
            TTSResult列表
        """
        output_dir.mkdir(parents=True, exist_ok=True)

        tasks = []
        for i, text in enumerate(texts):
            output_path = output_dir / f"segment_{i:03d}.mp3"
            task = self.generate_audio(text, output_path)
            tasks.append(task)

        # 并行执行
        results = await asyncio.gather(*tasks)

        # 设置正确的索引
        for i, result in enumerate(results):
            result.segment_index = i

        return results

    def _get_audio_duration(self, audio_path: Path) -> float:
        """
        使用 ffprobe 获取音频时长

        Args:
            audio_path: 音频文件路径

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
            raise RuntimeError(f"ffprobe 错误: {result.stderr}")

        return float(result.stdout.strip())

    @classmethod
    def list_voices(cls) -> dict:
        """列出可用的中文语音"""
        return cls.CHINESE_VOICES.copy()


async def test_tts():
    """测试TTS引擎"""
    engine = TTSEngine(voice='zh-CN-XiaoxiaoNeural')

    print("=" * 50)
    print("TTS引擎测试")
    print("=" * 50)

    # 测试文本
    texts = [
        "这是第一句话，用于测试。",
        "这是第二句话！",
        "这是第三句话？"
    ]

    output_dir = Path("./temp/tts_test")
    output_dir.mkdir(parents=True, exist_ok=True)

    results = await engine.batch_generate(texts, output_dir)

    print(f"\n生成 {len(results)} 个音频文件:")
    for r in results:
        print(f"  [{r.segment_index}] {r.audio_path.name} - {r.duration:.2f}s")
        print(f"      文本: {r.text}")


if __name__ == '__main__':
    asyncio.run(test_tts())
