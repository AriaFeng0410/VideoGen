# 视频号视频生成工具

基于 Python + FFmpeg + Edge-TTS 的自动化视频生成工作流，专为腾讯视频号（竖屏 1080x1920）设计。

## 功能特性

- **TTS配音**: 使用 Edge-TTS 生成高质量中文配音
- **硬字幕**: 自动生成 ASS 格式字幕并烧录到视频
- **智能分割**: 按标点自动分割文本，生成字幕片段
- **竖屏适配**: 自动将图片适配为 1080x1920 竖屏格式
- **配置灵活**: 支持 YAML 配置文件和命令行参数

## 快速开始

### 1. 安装依赖

**macOS / Linux:**
```bash
chmod +x install.sh
./install.sh
```

**Windows:**
```cmd
install.bat
```

**手动安装:**
```bash
# 安装 ffmpeg (macOS)
brew install ffmpeg

# 安装 ffmpeg (Ubuntu)
sudo apt install ffmpeg

# 安装 Python 依赖
pip install edge-tts Pillow PyYAML
```

### 2. 准备素材

将素材放入对应目录：
- **图片**: `input/images/` (支持 JPG/PNG/WEBP)
- **文本**: `input/text/` (UTF-8 编码的文本文件)

### 3. 生成视频

```bash
# 基本用法
python main.py -t input/text/demo.txt -i input/images -o output/video.mp4

# 使用项目配置文件
python main.py -p input/project.yaml

# 自定义语音和语速
python main.py -t text.txt -i images/ -o video.mp4 \
    --voice zh-CN-YunxiNeural \
    --rate +20%

# 高质量输出
python main.py -t text.txt -i images/ -o video.mp4 \
    --preset slow \
    --crf 18
```

## 可用语音

| 参数值 | 风格 | 适用场景 |
|--------|------|----------|
| `zh-CN-XiaoxiaoNeural` | 女声温柔 | 通用、故事讲解（默认） |
| `zh-CN-XiaoyiNeural` | 女声活泼 | 轻松、活力内容 |
| `zh-CN-YunxiNeural` | 男声标准 | 新闻、教程 |
| `zh-CN-YunjianNeural` | 男声解说 | 纪录片、解说 |

## 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `-t, --text` | 文本文件路径 | - |
| `-i, --images` | 图片目录路径 | - |
| `-o, --output` | 输出视频路径 | `output/video.mp4` |
| `-c, --config` | 配置文件路径 | `config/default_config.yaml` |
| `-p, --project` | 项目配置文件 | - |
| `--voice` | TTS语音 | `zh-CN-XiaoxiaoNeural` |
| `--rate` | 语速调整 | `+0%` |
| `--font` | 字幕字体 | `Source Han Sans CN Bold` |
| `--font-size` | 字体大小 | `36` |
| `--preset` | 编码预设 | `medium` |
| `--crf` | 质量参数 | `23` |

## 配置文件

### 默认配置 (`config/default_config.yaml`)

```yaml
# TTS配置
tts:
  voice: "zh-CN-XiaoxiaoNeural"
  rate: "+0%"
  volume: "+0%"

# 字幕配置
subtitle:
  format: "ass"
  style:
    font_name: "Source Han Sans CN Bold"
    font_size: 36
    primary_color: "&H00FFFFFF"
    outline: 2
    margin_vertical: 80

# 图片配置
image:
  scale_mode: "fit"  # fit/ fill/ stretch

# 视频配置
video:
  width: 1080
  height: 1920
  fps: 30
  codec: "libx264"
  preset: "medium"
  crf: 23
```

### 项目配置 (`input/project.yaml`)

```yaml
project:
  name: "我的视频"
  description: "视频描述"

inputs:
  text_file: "text/demo.txt"
  images_dir: "images"

output:
  filename: "../output/my_video.mp4"

overrides:
  tts:
    voice: "zh-CN-YunxiNeural"
    rate: "+10%"
```

## 工作流程

```
输入                          处理                        输出
─────                        ─────                       ─────

纯文本  ─────► 分割器 ─────► 文本片段
                              │
                              ▼
                         Edge-TTS ─────► 音频片段 + 时长
                              │
                              ▼
                         字幕生成器 ─────► ASS字幕
                              │
图片序列 ─────► 图片处理器 ─────► 1080x1920图片
                              │
                              ▼
                         FFmpeg ─────► 最终视频
```

## 项目结构

```
video_generator/
├── main.py                    # 主入口
├── install.sh                 # macOS/Linux 安装脚本
├── install.bat                # Windows 安装脚本
├── requirements.txt           # Python 依赖
├── config/
│   └── default_config.yaml    # 默认配置
├── core/
│   ├── tts_engine.py          # TTS引擎
│   ├── subtitle_generator.py  # 字幕生成
│   ├── image_processor.py     # 图片处理
│   ├── video_composer.py      # 视频合成
│   └── workflow.py            # 工作流编排
├── utils/
│   └── text_splitter.py       # 文本分割
├── input/
│   ├── images/                # 图片素材
│   ├── text/                  # 文本素材
│   └── project.yaml           # 项目配置
├── output/                    # 输出视频
└── temp/                      # 临时文件
```

## 常见问题

### Q: ffmpeg 安装失败？

**macOS:**
```bash
# 修复 Homebrew 权限
sudo chown -R $(whoami) /opt/homebrew
brew install ffmpeg
```

**Windows:**
从 https://www.gyan.dev/ffmpeg/builds/ 下载，解压后添加到 PATH。

### Q: 字幕显示乱码？

确保系统安装了对应字体：
- **macOS**: 使用苹方字体或安装思源黑体
- **Windows**: 使用微软雅黑或安装思源黑体
- **Linux**: 安装 fonts-noto-cjk

### Q: TTS 生成失败？

检查网络连接，Edge-TTS 需要访问微软服务器。如需离线使用，可替换为本地 TTS 引擎。

### Q: 视频质量不满意？

调整以下参数：
```bash
# 更高质量（文件更大）
python main.py ... --preset slow --crf 18

# 更快编码（质量略低）
python main.py ... --preset fast --crf 26
```

## 扩展开发

### 添加新的 TTS 引擎

编辑 `core/tts_engine.py`，实现新的 TTS 类：

```python
class MyTTSEngine:
    def generate_audio(self, text: str, output_path: Path) -> TTSResult:
        # 实现您的 TTS 逻辑
        pass
```

### 添加转场效果

编辑 `core/video_composer.py`，使用 FFmpeg 的 xfade 滤镜：

```python
# 在 _create_image_sequence_video 中添加转场
filter_complex = """
    [0:v]fade=t=out:st=3.0:d=0.5[v0];
    [1:v]fade=t=in:st=0:d=0.5[v1];
    [v0][v1]concat=n=2:v=1:a=0[outv]
"""
```

## 系统要求

- Python 3.8+
- FFmpeg 4.0+
- 内存: 4GB+ (建议 8GB)
- 磁盘: 临时文件约需 500MB-2GB

## License

MIT License
