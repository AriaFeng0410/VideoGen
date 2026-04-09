# 字幕显示问题说明

## 问题原因

运行 `python3 main.py -t input/text/demo.txt -i input/images -o output/video.mp4` 后，视频已正确生成但看不到字幕。

**实际上字幕已经生成并嵌入到视频中！**

## 验证字幕存在

```bash
# 检查视频轨道
$ ffprobe -v error -show_streams output/video.mp4 | grep codec_type
codec_type=video    # 视频轨道
codec_type=audio    # 音频轨道
codec_type=subtitle # 字幕轨道 ← 字幕在这里！

# 提取字幕查看
$ python3 check_subtitle.py
轨道统计:
  视频轨道: 1
  音频轨道: 1
  字幕���道: 1  ✓
```

## 为什么看不到字幕

### 软字幕 vs 硬字幕

**当前实现：软字幕（Soft Subtitle）**
- 字幕作为独立轨道嵌入到 MP4 容器中
- 不会直接渲染到画面上
- 需要在播放器中手动开启
- 优点：字幕可选择开关、不影响画质、可编辑
- 缺点：需要播放器支持、默认不可见

**硬字幕（Hard Subtitle）**
- 字幕直接烧录到视频画面上
- 默认可见，无需播放器支持
- 缺点：��法关闭、影响画质、文件略大

### 如何查看软字幕

在不同播放器中开启字幕：

| 播放器 | 开启字幕方式 |
|--------|------------|
| **VLC** | 副标题 → 字幕轨道 → 选择字幕 |
| **QuickTime** | 显示 → 副标题 |
| **IINA (Mac)** | 字幕 → 选择字幕轨 |
| **PotPlayer (Windows)** | 字幕 → 选择字幕 |
| **浏览器** | 需要支持 track 标签 |

### macOS 上查看字幕

在 macOS 上推荐使用：

```bash
# 方法1：使用 IINA 播放器（推荐）
brew install --cask iina
open -a IINA output/video.mp4

# 方法2：使用 VLC
brew install --cask vlc
open -a VLC output/video.mp4
```

## 解决方案

### 方案1：保持软字幕（推荐）

适合场景：需要字幕可选择开关、用于视频平台发布

**使用现有代码即可**，只需在播放器中开启字幕：

```python
# 当前代码使用软字幕方式
# video_composer.py:228 已配置
'-c:s', 'mov_text',  # MP4 软字幕��码器
'-metadata:s:s:0', 'language=chi',  # 字幕语言标记
```

### 方案2：修改为硬字幕

适合场景：需要字幕默认可见、兼容所有播放器

需要修改 `core/video_composer.py` 的 `_compose_final_video` 方法：

```python
# 将软字幕改为硬字幕（字幕烧录到画面）
def _compose_final_video_hard_sub(self,
                                   image_video: Path,
                                   audio: Path,
                                   subtitle_path: Path,
                                   output_path: Path) -> Path:
    """
    合成最终视频（硬字幕 - 字幕烧录到画面）
    """
    # 需要使用 subtitles 滤镜
    subtitle_path_str = str(subtitle_path.absolute()).replace(':', '\\:')

    cmd = [
        'ffmpeg', '-y',
        '-i', str(image_video),
        '-i', str(audio),
        '-vf', f"subtitles='{subtitle_path_str}'",
        '-c:v', self.config.codec,
        '-preset', self.config.preset,
        '-crf', str(self.config.crf),
        '-c:a', self.config.audio_codec,
        '-b:a', self.config.audio_bitrate,
        '-shortest',
        str(output_path)
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg最终合成错误: {result.stderr}")

    return output_path
```

### 方案3：同时生成两个版本

生成软字幕版本和硬字幕版本

```python
# 在 workflow.py 中同时生成两个版本
def generate_both_versions(self, ...):
    # ... 生成软字幕版本
    soft_sub_video = self._compose_final_video(...)

    # ... 生成硬字幕版本
    hard_sub_video = self._compose_final_video_hard_sub(...)

    return soft_sub_video, hard_sub_video
```

## 总结

1. ✅ 字幕已正确生成（temp/subtitle.ass）
2. ✅ 字幕已嵌入视频（轨道 2: mov_text）
3. ⚠️ 当前使用软字幕方式，需要在播放器中手动开启
4. 💡 建议修改代码添加 `--hard-sub` 参数支持硬字幕选项

## 快速验证

运行检查脚本验证字幕：

```bash
python3 check_subtitle.py
```

使用支持字幕的播放器查看：

```bash
# 使用 IINA 播放（Mac 推荐）
open -a IINA output/video.mp4

# 或使用 VLC
open -a VLC output/video.mp4
```
