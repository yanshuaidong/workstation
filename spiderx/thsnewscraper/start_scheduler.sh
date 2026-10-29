#!/bin/bash
# 启动同花顺期货热点新闻爬虫调度器
# 使用 nohup 后台运行，输出重定向到 nohup.out

cd "$(dirname "$0")" || exit 1

echo "🚀 启动同花顺期货新闻爬虫调度器..."
echo "📁 当前目录: $(pwd)"
echo "⏰ 开始时间: $(date)"
echo ""

# 检查是否已在运行
if [ -f "scheduler.pid" ]; then
    OLD_PID=$(cat scheduler.pid)
    if ps -p "$OLD_PID" > /dev/null 2>&1; then
        echo "⚠️  调度器已在运行中 (PID: $OLD_PID)"
        echo "💡 如需重启，请先运行: ./stop_scheduler.sh"
        exit 1
    else
        echo "⚠️  发现过期的 PID 文件，清理中..."
        rm -f scheduler.pid
    fi
fi

# 检查 Python 环境
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ 错误: 未找到 Python 解释器"
    exit 1
fi

echo "🐍 使用 Python: $($PYTHON_CMD --version 2>&1)"

if [ ! -f "main.py" ]; then
    echo "❌ 错误: 未找到 main.py 文件"
    exit 1
fi

# 启动进程
nohup $PYTHON_CMD main.py schedule > nohup.out 2>&1 &
PYTHON_PID=$!
echo "$PYTHON_PID" > scheduler.pid

sleep 1

if ps -p "$PYTHON_PID" > /dev/null 2>&1; then
    echo "✅ 调度器已启动 (PID: $PYTHON_PID)"
    echo "📝 实时查看输出: tail -f nohup.out"
    echo "📝 按日期日志: tail -f logs/ths_news_\$(date +%Y-%m-%d).log"
    echo "🛑 停止程序: ./stop_scheduler.sh"
else
    echo "❌ 调度器启动失败，请检查日志"
    rm -f scheduler.pid
    cat nohup.out 2>/dev/null
    exit 1
fi

echo ""
echo "👀 输出预览："
sleep 1
head -10 nohup.out 2>/dev/null || echo "输出文件生成中，请稍等..."
