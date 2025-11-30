#!/bin/bash

# Gemini Helper 后端服务启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "====================================="
echo "启动 Gemini Helper 后端服务"
echo "====================================="

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "未找到虚拟环境，正在创建..."
    python3 -m venv venv
    echo "虚拟环境创建完成"
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "检查并安装依赖..."
pip install -q -r requirements.txt

# 检查是否已经在运行
if [ -f "server.pid" ]; then
    OLD_PID=$(cat server.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "服务已在运行 (PID: $OLD_PID)"
        echo "如需重启，请先运行 ./stop_server.sh"
        exit 1
    else
        rm server.pid
    fi
fi

# 启动服务
echo "启动服务（端口 1124）..."
nohup python main.py > nohup.out 2>&1 &
PID=$!

# 保存 PID
echo $PID > server.pid

echo "====================================="
echo "服务启动成功！"
echo "PID: $PID"
echo "端口: 1124"
echo "日志文件: nohup.out"
echo "健康检查: http://localhost:1124/health"
echo "====================================="

