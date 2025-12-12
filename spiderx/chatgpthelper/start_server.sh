#!/bin/bash

# ChatGPT Helper 后端服务启动脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "====================================="
echo "启动 ChatGPT Helper 后端服务"
echo "====================================="

# 检查 Python 环境
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ 错误: 未找到Python解释器"
    exit 1
fi

echo "🐍 使用 Python: $($PYTHON_CMD --version)"

# 检查是否已经在运行
if [ -f "server.pid" ]; then
    OLD_PID=$(cat server.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "服务已在运行 (PID: $OLD_PID)"
        echo "如需重启，请先运行 ./stop_server.sh"
        exit 1
    else
        echo "🗑️  清理过期的PID文件..."
        rm -f server.pid
    fi
fi

# 启动服务
echo "启动服务（端口 1126）..."
nohup $PYTHON_CMD main.py > nohup.out 2>&1 &
PID=$!

# 保存 PID
echo $PID > server.pid

echo "====================================="
echo "服务启动成功！"
echo "PID: $PID"
echo "端口: 1126"
echo "日志文件: nohup.out"
echo "健康检查: http://localhost:1126/health"
echo "====================================="

