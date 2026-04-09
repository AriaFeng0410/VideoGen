# -*- coding: utf-8 -*-
"""文本分割器 - 按标点分割文本"""

import re
from typing import List
from dataclasses import dataclass


@dataclass
class TextSegment:
    """文本片段"""
    text: str
    index: int
    char_count: int


class TextSplitter:
    """文本分割器 - 按句号等标点分割"""

    def __init__(self, max_segment_length: int = 50):
        """
        Args:
            max_segment_length: 单个片段最大字符数，超过则用逗号进一步分割
        """
        self.max_segment_length = max_segment_length

    def split(self, text: str) -> List[TextSegment]:
        """
        将文本分割成片段

        Args:
            text: 输入文本

        Returns:
            TextSegment列表

        ��例:
            输入: "这是第一句话。这是第二句话！这是第三句话？"
            输出: [
                TextSegment(text="这是第一句话。", index=0, char_count=7),
                TextSegment(text="这是第二句话！", index=1, char_count=7),
                TextSegment(text="这是第三句话？", index=2, char_count=7)
            ]
        """
        # 预处理：去除多余空白
        text = self._clean_text(text)

        # 第一步：按主要标点（句号、问号、感叹号）分割
        primary_segments = self._split_by_pattern(text, r'([。！？])')

        # 第二步：检查长度，超长的用次要标点（逗号、分号）分割
        final_segments = []
        for seg in primary_segments:
            if len(seg) > self.max_segment_length:
                sub_segments = self._split_by_pattern(seg, r'([，；、])')
                final_segments.extend(sub_segments)
            else:
                final_segments.append(seg)

        # 过滤空片段并生成 TextSegment 对象
        result = []
        index = 0
        for seg in final_segments:
            seg = seg.strip()
            if seg:
                result.append(TextSegment(
                    text=seg,
                    index=index,
                    char_count=len(seg)
                ))
                index += 1

        return result

    def _clean_text(self, text: str) -> str:
        """清理文本"""
        # 去除首尾空白
        text = text.strip()
        # 合并多个连续空白为一
        text = re.sub(r'\s+', '', text)
        return text

    def _split_by_pattern(self, text: str, pattern: str) -> List[str]:
        """
        按正则模式分割，保留分隔符

        Args:
            text: 输入文本
            pattern: 分隔符正则模式（需用捕获组）

        Returns:
            分割后的文本列表，分隔符附加在前一个片段末尾
        """
        # 使用正则分割，捕获组会保留分隔符
        parts = re.split(pattern, text)

        # 合并分隔符到前一个片段
        result = []
        current = ""

        for i, part in enumerate(parts):
            if re.match(pattern, part):
                # 这是分隔符，附加到当前片段
                current += part
            else:
                # 这是文本内容
                if current:
                    result.append(current)
                current = part

        # 添加最后一个片段
        if current:
            result.append(current)

        return result


def main():
    """测试入口"""
    splitter = TextSplitter(max_segment_length=50)

    # 测试文本
    test_text = """
    人工智能正在改变我们的生活方式。从智能手机到自动驾驶汽车，
    AI技术已经渗透到我们日常生活的方方面面！你是否想过，未来会是什么样子？
    让我们一起探索这个充满可能性的世界。
    """

    segments = splitter.split(test_text)

    print("=" * 50)
    print("文本分割测试")
    print("=" * 50)
    print(f"原文长度: {len(test_text)} 字符")
    print(f"分割结果: {len(segments)} 个片段")
    print()

    for seg in segments:
        print(f"[{seg.index}] ({seg.char_count}字) {seg.text}")


if __name__ == '__main__':
    main()
