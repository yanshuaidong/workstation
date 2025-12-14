#!/bin/bash
# 停止期货涨跌幅TOP10定时任务调度器

# 切换到脚本所在目录
cd "$(dirname "$0")" || exit 1

echo "🛑 停止期货涨跌幅TOP10调度器..."
echo "⏰ 停止时间: $(date)"
echo ""

# 检查是否存在scheduler.pid文件
if [ ! -f "scheduler.pid" ]; then
    echo "⚠️  未找到scheduler.pid文件"
    echo "📝 调度器未运行或已停止（可能是误操作）"
    echo "💡 如需启动调度器，请运行: ./start_scheduler.sh"
    exit 0
fi

# 读取PID（支持多行：第一行 Python PID，第二行 caffeinate PID）
PYTHON_PID=$(sed -n '1p' scheduler.pid)
CAFFEINATE_PID=$(sed -n '2p' scheduler.pid)

echo "📋 Python 进程ID: $PYTHON_PID"
[ -n "$CAFFEINATE_PID" ] && echo "📋 Caffeinate 进程ID: $CAFFEINATE_PID"

# 检查 Python 进程是否存在
if ! ps -p $PYTHON_PID > /dev/null 2>&1; then
    echo "⚠️  Python 进程 $PYTHON_PID 不存在（可能是系统重启后遗留的PID文件）"
    # 清理 caffeinate 进程（如果还在运行）
    if [ -n "$CAFFEINATE_PID" ] && ps -p $CAFFEINATE_PID > /dev/null 2>&1; then
        echo "🧹 清理残留的 caffeinate 进程..."
        kill $CAFFEINATE_PID 2>/dev/null
    fi
    rm -f scheduler.pid
    echo "🗑️  已清理过期的PID文件"
    exit 0
fi

# 尝试优雅停止 Python 进程（发送 SIGTERM）
echo "🔍 正在优雅停止 Python 进程..."
kill $PYTHON_PID

# 等待进程响应，最多等待 10 秒
for i in {1..10}; do
    if ! ps -p $PYTHON_PID > /dev/null 2>&1; then
        echo "✅ Python 进程已优雅停止"
        break
    fi
    sleep 1
    echo "   等待中... ($i/10)"
done

# 如果还没停止，强制停止
if ps -p $PYTHON_PID > /dev/null 2>&1; then
    echo "⚠️  进程未响应，强制停止..."
    kill -9 $PYTHON_PID
    sleep 1
fi

# 确认 Python 进程已关闭
if ps -p $PYTHON_PID > /dev/null 2>&1; then
    echo "❌ Python 进程停止失败，请手动处理: kill -9 $PYTHON_PID"
    exit 1
fi

# 停止 caffeinate 进程（如果存在且还在运行）
if [ -n "$CAFFEINATE_PID" ] && ps -p $CAFFEINATE_PID > /dev/null 2>&1; then
    echo "🧹 停止 caffeinate 进程..."
    kill $CAFFEINATE_PID 2>/dev/null
    sleep 1
    # 强制停止
    if ps -p $CAFFEINATE_PID > /dev/null 2>&1; then
        kill -9 $CAFFEINATE_PID 2>/dev/null
    fi
    echo "✅ caffeinate 进程已停止"
fi

# 删除PID文件
rm -f scheduler.pid
echo "✅ 调度器已停止"
echo "🗑️  已删除PID文件"
echo ""
echo "💡 如需重启调度器，请运行: ./start_scheduler.sh"

