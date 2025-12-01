#!/bin/bash

# Gemini Helper 后端服务停止脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "====================================="
echo "停止 Gemini Helper 后端服务"
echo "====================================="

if [ ! -f "server.pid" ]; then
    echo "ℹ️  未找到 PID 文件，服务可能未运行"
    echo "💡 如需启动服务，请运行: ./start_server.sh"
    exit 0
fi

PID=$(cat server.pid)
echo "📋 进程ID: $PID"

# 检查进程是否存在
if ! ps -p $PID > /dev/null 2>&1; then
    echo "⚠️  进程 $PID 不存在（可能是系统重启后遗留的PID文件）"
    rm -f server.pid
    echo "🗑️  已清理过期的PID文件"
    exit 0
fi

echo "正在停止服务 (PID: $PID)..."
kill $PID

# 等待进程结束
for i in {1..10}; do
    if ! ps -p $PID > /dev/null 2>&1; then
        break
    fi
    sleep 1
done

# 如果还在运行，强制停止
if ps -p $PID > /dev/null 2>&1; then
    echo "进程未响应，强制停止..."
    kill -9 $PID
fi

echo "✅ 服务已停止"

rm -f server.pid

echo "====================================="
echo "清理完成"
echo "====================================="

