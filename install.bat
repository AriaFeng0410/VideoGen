@echo off
chcp 65001 >nul
REM 视频号视频生成工具 - Windows 一键安装脚本

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║          视频号视频生成工具 - 依赖安装脚本                    ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.

REM 检查管理员权限
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [警告] 建议以管理员身份运行此脚本
    echo.
)

REM 步骤1: 检查 Python
echo [步骤1] 检查 Python
echo.

python --version >nul 2>&1
if %errorLevel% equ 0 (
    for /f "tokens=*" %%i in ('python --version') do echo   ✓ %%i
) else (
    echo   ✗ Python 未安装
    echo.
    echo   请从以下地址下载并安装 Python 3.x:
    echo   https://www.python.org/downloads/
    echo.
    echo   安装时请勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

REM 步骤2: 安装 ffmpeg
echo.
echo [步骤2] 安装 ffmpeg
echo.

ffmpeg -version >nul 2>&1
if %errorLevel% equ 0 (
    echo   ✓ ffmpeg 已安装
) else (
    echo   ffmpeg 未安装，正在尝试安装...
    echo.

    REM 检查 winget
    winget --version >nul 2>&1
    if %errorLevel% equ 0 (
        echo   使用 winget 安装 ffmpeg...
        winget install ffmpeg -e --source winget
    ) else (
        REM 检查 chocolatey
        choco --version >nul 2>&1
        if %errorLevel% equ 0 (
            echo   使用 Chocolatey 安装 ffmpeg...
            choco install ffmpeg -y
        ) else (
            echo   ✗ 未找到 winget 或 Chocolatey
            echo.
            echo   请手动安装 ffmpeg:
            echo   1. 访问 https://www.gyan.dev/ffmpeg/builds/
            echo   2. 下载 "ffmpeg-release-essentials.zip"
            echo   3. 解压到 C:\ffmpeg
            echo   4. 将 C:\ffmpeg\bin 添加到系统 PATH
            echo.
            echo   或者安装 Chocolatey:
            echo   https://chocolatey.org/install
            echo.
            pause
            exit /b 1
        )
    )

    REM 验证安装
    ffmpeg -version >nul 2>&1
    if %errorLevel% equ 0 (
        echo   ✓ ffmpeg 安装成功
    ) else (
        echo   ✗ ffmpeg 安装失败，请手动安装
        pause
        exit /b 1
    )
)

REM 步骤3: 安装 Python 依赖
echo.
echo [步骤3] 安装 Python 依赖
echo.

echo   安装 edge-tts...
pip install edge-tts -i https://pypi.tuna.tsinghua.edu.cn/simple 2>nul
if %errorLevel% neq 0 (
    pip install edge-tts
)

echo   安装 Pillow...
pip install Pillow -i https://pypi.tuna.tsinghua.edu.cn/simple 2>nul
if %errorLevel% neq 0 (
    pip install Pillow
)

echo   安装 PyYAML...
pip install PyYAML -i https://pypi.tuna.tsinghua.edu.cn/simple 2>nul
if %errorLevel% neq 0 (
    pip install PyYAML
)

echo   安装 tqdm...
pip install tqdm -i https://pypi.tuna.tsinghua.edu.cn/simple 2>nul
if %errorLevel% neq 0 (
    pip install tqdm
)

REM 步骤4: 验证安装
echo.
echo [步骤4] 验证安装
echo.

python -c "import edge_tts; print('  ✓ edge-tts:', edge_tts.__version__)" 2>nul
if %errorLevel% neq 0 (
    echo   ✗ edge-tts 未正确安装
)

python -c "import PIL; print('  ✓ Pillow:', PIL.__version__)" 2>nul
if %errorLevel% neq 0 (
    echo   ✗ Pillow 未正确安装
)

python -c "import yaml; print('  ✓ PyYAML: 已安装')" 2>nul
if %errorLevel% neq 0 (
    echo   ✗ PyYAML 未正确安装
)

ffmpeg -version >nul 2>&1
if %errorLevel% equ 0 (
    echo   ✓ ffmpeg: 已安装
) else (
    echo   ✗ ffmpeg: 未安装
)

echo.
echo ╔════════════════════════════════════════════════════════════════╗
echo ║                    安装��成！                                  ║
echo ╚════════════════════════════════════════════════════════════════╝
echo.
echo 现在可以运行以下命令生成视频:
echo.
echo     python main.py -t input/text/demo.txt -i input/images -o output/video.mp4
echo.
pause
