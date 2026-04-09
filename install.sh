#!/bin/bash
# -*- coding: utf-8 -*-
#
# 视频号视频生成工具 - 一键安装脚本
# 用法: chmod +x install.sh && ./install.sh
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印函数
print_header() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║${NC}          视频号视频生成工具 - 依赖安装脚本                    ${BLUE}║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

print_step() {
    echo -e "\n${GREEN}[步骤 $1]${NC} $2"
}

print_info() {
    echo -e "  ${BLUE}→${NC} $1"
}

print_success() {
    echo -e "  ${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "  ${RED}✗${NC} $1"
}

print_warning() {
    echo -e "  ${YELLOW}!${NC} $1"
}

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if command_exists apt-get; then
            echo "ubuntu"
        elif command_exists yum; then
            echo "centos"
        else
            echo "linux"
        fi
    else
        echo "unknown"
    fi
}

# 安装 ffmpeg (macOS)
install_ffmpeg_macos() {
    print_info "检测 macOS 系统"

    if command_exists brew; then
        print_success "Homebrew 已安装"
    else
        print_info "安装 Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi

    # 检查并修复权限问题
    print_info "检查 Homebrew 权限..."
    local brew_owner=$(stat -f "%Su" /opt/homebrew 2>/dev/null || stat -f "%Su" /usr/local/Homebrew 2>/dev/null || echo "unknown")

    if [[ "$brew_owner" != "$(whoami)" ]]; then
        print_warning "Homebrew 目录权限需要修复"
        print_info "请运行以下命令（需要密码）:"
        echo ""
        echo "    sudo chown -R \$(whoami) /opt/homebrew /Users/\$(whoami)/Library/Caches/Homebrew /Users/\$(whoami)/Library/Logs/Homebrew"
        echo ""
        read -p "  是否已修复权限? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "请先修复权限后重新运行此脚本"
            exit 1
        fi
    fi

    print_info "安装 ffmpeg..."
    brew install ffmpeg

    if command_exists ffmpeg; then
        print_success "ffmpeg 安装成功: $(ffmpeg -version 2>&1 | head -1)"
    else
        print_error "ffmpeg 安装失败"
        exit 1
    fi
}

# 安装 ffmpeg (Ubuntu/Debian)
install_ffmpeg_ubuntu() {
    print_info "检测 Ubuntu/Debian 系统"

    print_info "更新软件源..."
    sudo apt-get update -qq

    print_info "安装 ffmpeg..."
    sudo apt-get install -y ffmpeg

    if command_exists ffmpeg; then
        print_success "ffmpeg 安装成功: $(ffmpeg -version 2>&1 | head -1)"
    else
        print_error "ffmpeg 安装失败"
        exit 1
    fi
}

# 安装 ffmpeg (CentOS/RHEL)
install_ffmpeg_centos() {
    print_info "检测 CentOS/RHEL 系统"

    print_info "启用 EPEL 和 RPM Fusion..."
    sudo yum install -y epel-release
    sudo yum localinstall -y --nogpgcheck https://download1.rpmfusion.org/free/el/rpmfusion-free-release-$(rpm -E %rhel).noarch.rpm

    print_info "安装 ffmpeg..."
    sudo yum install -y ffmpeg ffmpeg-devel

    if command_exists ffmpeg; then
        print_success "ffmpeg 安装成功: $(ffmpeg -version 2>&1 | head -1)"
    else
        print_error "ffmpeg 安装失败"
        exit 1
    fi
}

# 安装 Python 依赖
install_python_deps() {
    print_step "2" "安装 Python 依赖"

    # 检查 Python
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        print_error "未找到 Python，请先安装 Python 3.x"
        exit 1
    fi

    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
    print_success "Python: $PYTHON_VERSION"

    # 检查 pip
    if $PYTHON_CMD -m pip --version >/dev/null 2>&1; then
        print_success "pip 已安装"
    else
        print_info "安装 pip..."
        curl -sS https://bootstrap.pypa.io/get-pip.py | $PYTHON_CMD
    fi

    # 安装依赖
    print_info "安装依赖包..."

    # 尝试使用国内镜像加速
    MIRRORS=(
        "https://pypi.tuna.tsinghua.edu.cn/simple"
        "https://mirrors.aliyun.com/pypi/simple"
        "https://pypi.doubanio.com/simple"
    )

    INSTALLED=false
    for mirror in "${MIRRORS[@]}"; do
        print_info "尝试镜像: $mirror"
        if $PYTHON_CMD -m pip install -i "$mirror" --timeout 30 --retries 3 \
            edge-tts>=6.1.0 Pillow>=10.0.0 PyYAML>=6.0 tqdm>=4.66.0 2>/dev/null; then
            INSTALLED=true
            print_success "使用镜像 $mirror 安装成功"
            break
        fi
    done

    if [[ "$INSTALLED" == false ]]; then
        print_warning "国内镜像安装失败，尝试官方源..."
        $PYTHON_CMD -m pip install --timeout 60 --retries 3 \
            edge-tts Pillow PyYAML tqdm
    fi

    # 验证安装
    print_info "验证依赖..."

    $PYTHON_CMD -c "import edge_tts; print('  ✓ edge-tts:', edge_tts.__version__)" 2>/dev/null || print_error "edge-tts 未正确安装"
    $PYTHON_CMD -c "import PIL; print('  ✓ Pillow:', PIL.__version__)" 2>/dev/null || print_error "Pillow 未正确安装"
    $PYTHON_CMD -c "import yaml; print('  ✓ PyYAML: 已安装')" 2>/dev/null || print_error "PyYAML 未正确安装"
}

# 验证安装
verify_installation() {
    print_step "3" "验证安装"

    local all_ok=true

    # 检查 ffmpeg
    if command_exists ffmpeg; then
        print_success "ffmpeg: $(ffmpeg -version 2>&1 | head -1 | cut -d' ' -f3)"
    else
        print_error "ffmpeg 未安装"
        all_ok=false
    fi

    # 检查 ffprobe
    if command_exists ffprobe; then
        print_success "ffprobe: 已安装"
    else
        print_error "ffprobe 未安装"
        all_ok=false
    fi

    # 检查 Python 依赖
    if command_exists python3; then
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python"
    fi

    if $PYTHON_CMD -c "import edge_tts" 2>/dev/null; then
        print_success "edge-tts: 已安装"
    else
        print_error "edge-tts: 未安装"
        all_ok=false
    fi

    if $PYTHON_CMD -c "import PIL" 2>/dev/null; then
        print_success "Pillow: 已安装"
    else
        print_error "Pillow: 未安装"
        all_ok=false
    fi

    if $PYTHON_CMD -c "import yaml" 2>/dev/null; then
        print_success "PyYAML: 已安装"
    else
        print_error "PyYAML: 未安装"
        all_ok=false
    fi

    echo ""
    if [[ "$all_ok" == true ]]; then
        echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${GREEN}║${NC}                  ✓ 所有依赖安装成功！                         ${GREEN}║${NC}"
        echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo "现在可以运行以下命令生成视频:"
        echo ""
        echo "    python3 main.py -t input/text/demo.txt -i input/images -o output/video.mp4"
        echo ""
    else
        echo -e "${RED}╔════════════════════════════════════════════════════════════════╗${NC}"
        echo -e "${RED}║${NC}                  ✗ 部分依赖安装失败                            ${RED}║${NC}"
        echo -e "${RED}╚════════════════════════════════════════════════════════════════╝${NC}"
        echo ""
        echo "请检查错误信息并手动安装失败的依赖"
        exit 1
    fi
}

# 显示帮助
show_help() {
    echo "视频号视频生成工具 - 依赖安装脚本"
    echo ""
    echo "用法: ./install.sh [选项]"
    echo ""
    echo "选项:"
    echo "  -h, --help     显示帮助信息"
    echo "  --ffmpeg-only  仅安装 ffmpeg"
    echo "  --python-only  仅安装 Python 依赖"
    echo "  --no-verify    跳过安装验证"
    echo ""
    echo "示例:"
    echo "  ./install.sh              # 安装所有依赖"
    echo "  ./install.sh --ffmpeg-only # 仅安装 ffmpeg"
    echo ""
}

# 主函数
main() {
    local ffmpeg_only=false
    local python_only=false
    local verify=true

    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            --ffmpeg-only)
                ffmpeg_only=true
                shift
                ;;
            --python-only)
                python_only=true
                shift
                ;;
            --no-verify)
                verify=false
                shift
                ;;
            *)
                print_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done

    print_header

    # 安装 ffmpeg
    if [[ "$python_only" == false ]]; then
        print_step "1" "安装 ffmpeg"

        if command_exists ffmpeg && command_exists ffprobe; then
            print_success "ffmpeg 已安装: $(ffmpeg -version 2>&1 | head -1)"
        else
            OS=$(detect_os)
            case $OS in
                macos)
                    install_ffmpeg_macos
                    ;;
                ubuntu)
                    install_ffmpeg_ubuntu
                    ;;
                centos)
                    install_ffmpeg_centos
                    ;;
                *)
                    print_error "不支持的操作系统: $OSTYPE"
                    print_info "请手动安装 ffmpeg: https://ffmpeg.org/download.html"
                    exit 1
                    ;;
            esac
        fi
    fi

    # 安装 Python 依赖
    if [[ "$ffmpeg_only" == false ]]; then
        install_python_deps
    fi

    # 验证
    if [[ "$verify" == true ]]; then
        verify_installation
    fi
}

# 运行
main "$@"
