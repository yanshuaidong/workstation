#!/bin/bash

echo "========================================"
echo "  豆包 Helper 后端服务启动"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3，请先安装 Python 3.7+"
    exit 1
fi

echo "[1/3] 检查依赖..."
if ! python3 -c "import flask" &> /dev/null; then
    echo "[提示] 正在安装依赖..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "[错误] 依赖安装失败"
        exit 1
    fi
fi

echo "[2/3] 检查数据库..."
if [ ! -f "../db/crawler.db" ]; then
    echo "[警告] 本地数据库不存在: ../db/crawler.db"
    echo "[提示] 请确保数据库文件存在后再启动服务"
fi

echo "[3/3] 启动服务..."
echo ""
echo "========================================"
echo "  服务地址: http://localhost:1127"
echo "  健康检查: http://localhost:1127/health"
echo "  按 Ctrl+C 停止服务"
echo "========================================"
echo ""

python3 main.py
