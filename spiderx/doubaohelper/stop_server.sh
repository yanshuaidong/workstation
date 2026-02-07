#!/bin/bash

echo "正在停止豆包 Helper 后端服务..."

# 查找并杀死运行在 1127 端口的进程
PID=$(lsof -ti:1127)

if [ -z "$PID" ]; then
    echo "没有找到运行在端口 1127 的服务"
else
    kill -9 $PID
    echo "服务已停止 (PID: $PID)"
fi
