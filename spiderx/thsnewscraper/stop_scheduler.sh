#!/bin/bash
# 停止同花顺期货热点新闻爬虫调度器

cd "$(dirname "$0")" || exit 1

echo "🛑 停止同花顺期货新闻爬虫调度器..."
echo "⏰ 停止时间: $(date)"
echo ""

if [ ! -f "scheduler.pid" ]; then
    echo "ℹ️  未找到 scheduler.pid 文件，调度器未在运行"
    echo "💡 提示: 这可能是误操作，无需关闭"
    exit 0
fi

PYTHON_PID=$(sed -n '1p' scheduler.pid)
echo "📋 进程 ID: $PYTHON_PID"

if ! ps -p "$PYTHON_PID" > /dev/null 2>&1; then
    echo "⚠️  进程 $PYTHON_PID 不存在（可能是系统重启后遗留的 PID 文件）"
    rm -f scheduler.pid
    echo "🗑️  已清理过期的 PID 文件"
    exit 0
fi

# 先发 SIGTERM，让调度器走优雅退出
echo "🔍 正在优雅停止进程..."
kill "$PYTHON_PID"

for i in {1..10}; do
    if ! ps -p "$PYTHON_PID" > /dev/null 2>&1; then
        echo "✅ 进程已优雅停止"
        break
    fi
    sleep 1
    echo "   等待中... ($i/10)"
done

if ps -p "$PYTHON_PID" > /dev/null 2>&1; then
    echo "⚠️  进程未响应，强制停止..."
    kill -9 "$PYTHON_PID"
    sleep 1
fi

if ps -p "$PYTHON_PID" > /dev/null 2>&1; then
    echo "❌ 进程停止失败，请手动处理: kill -9 $PYTHON_PID"
    exit 1
fi

rm -f scheduler.pid
echo "✅ 调度器已停止"
echo "🗑️  已删除 PID 文件"
echo ""
echo "📝 提示: 如需重启调度器，请运行: ./start_scheduler.sh"
