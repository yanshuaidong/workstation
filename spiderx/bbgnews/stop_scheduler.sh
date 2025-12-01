#!/bin/bash
# 停止 Bloomberg 新闻处理服务

echo "🛑 停止 Bloomberg 新闻处理服务..."
echo "⏰ 停止时间: $(date)"
echo ""

# 获取脚本所在目录（支持从任意位置运行）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查是否存在scheduler.pid文件
if [ ! -f "scheduler.pid" ]; then
    echo "⚠️  未找到scheduler.pid文件"
    echo "📝 服务未运行或已停止"
    echo "💡 如需启动服务，请运行: ./start_scheduler.sh"
    exit 0
fi

# 读取PID
PID=$(cat scheduler.pid)
echo "📋 进程ID: $PID"

# 检查进程是否存在
if ! ps -p $PID > /dev/null 2>&1; then
    echo "⚠️  进程 $PID 不存在（可能是系统重启后遗留的PID文件）"
    rm -f scheduler.pid
    echo "🗑️  已清理过期的PID文件"
    exit 0
fi

# 尝试优雅停止（发送SIGTERM信号）
echo "🔍 正在优雅停止进程..."
kill $PID
sleep 3

# 检查是否成功停止
if ps -p $PID > /dev/null 2>&1; then
    echo "⚠️  进程未响应，强制停止..."
    kill -9 $PID
    sleep 2
fi

# 确认关闭成功
if ps -p $PID > /dev/null 2>&1; then
    echo "❌ 进程停止失败，请手动处理: kill -9 $PID"
    exit 1
fi

# 删除PID文件
rm -f scheduler.pid
echo "✅ 服务已停止"
echo "🗑️  已删除PID文件"
echo ""
echo "💡 如需重启服务，请运行: ./start_scheduler.sh"


