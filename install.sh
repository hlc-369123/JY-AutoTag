#!/bin/bash

echo "====================================="
echo "剪映自动化脚本 - 环境安装程序 (macOS)"
echo "====================================="

# 1. 检查 python3 是否安装
if ! command -v python3 &> /dev/null
then
    echo "[错误] 未找到 python3，请先安装 Python 环境！"
    echo "建议通过 Homebrew 安装（在终端输入）: brew install python"
    echo "或者前往官网下载: https://www.python.org/downloads/macos/"
    exit 1
fi

echo "✅ [正常] 发现 Python 环境: $(python3 --version)"

# 2. 检查 pip3 是否安装
if ! command -v pip3 &> /dev/null
then
    echo "⚠️ 未找到 pip3 命令，尝试使用 python3 -m pip"
    PIP_CMD="python3 -m pip"
else
    PIP_CMD="pip3"
fi

# 3. 安装依赖库
echo "📦 正在安装必备依赖库 (pyautogui, pynput, opencv-python)..."
# 使用国内清华镜像源加速下载
$PIP_CMD install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

if [ $? -eq 0 ]; then
    echo "====================================="
    echo "🎉 依赖库安装成功！"
    echo ""
    echo "⚠️ 【非常重要】要在其他 Mac 上运行，必须授予权限："
    echo "1. 打开 Mac 的『系统设置』 -> 『隐私与安全性』"
    echo "2. 找到『辅助功能』，把你用来运行脚本的终端程序（终端 或 iTerm2）添加并打勾。"
    echo "3. 找到『屏幕录制』，同样把你用来运行脚本的终端程序添加并打勾（脚本需要截图找搜索框）。"
    echo ""
    echo "准备就绪后，确保 search_box.png 截图放在本目录下，即可运行："
    echo "python3 capcut_auto.py"
    echo "====================================="
else
    echo "❌ 安装依赖时发生错误，请检查网络或权限。"
fi
