#!/bin/bash

# Gemini Helper 后端服务停止脚本

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "====================================="
echo "停止 Gemini Helper 后端服务"
echo "====================================="

if [ ! -f "server.pid" ]; then
    echo "未找到 PID 文件，服务可能未运行"
    exit 1
fi

PID=$(cat server.pid)

if ps -p $PID > /dev/null 2>&1; then
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
    
    echo "服务已停止"
else
    echo "服务未运行 (PID: $PID)"
fi

rm -f server.pid

echo "====================================="
echo "清理完成"
echo "====================================="

