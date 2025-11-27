#!/bin/bash
# 停止东方财富期货数据爬虫调度器

echo "🛑 停止东方财富期货数据爬虫调度器..."
echo "⏰ 停止时间: $(date)"
echo ""

# 检查是否存在scheduler.pid文件
if [ ! -f "scheduler.pid" ]; then
    echo "ℹ️  未找到scheduler.pid文件"
    echo "💡 调度器可能未运行，或者是误操作"
    echo "📝 如需启动调度器，请运行: ./start_scheduler.sh"
    exit 0
fi

# 读取PID
PID=$(cat scheduler.pid)
echo "📋 从scheduler.pid读取到进程ID: $PID"

# 检查进程是否还在运行
if ! ps -p $PID > /dev/null 2>&1; then
    echo "⚠️  进程 $PID 不存在或已停止"
    rm scheduler.pid
    echo "🗑️  已删除过期的scheduler.pid文件"
    echo "✅ 调度器已停止"
    exit 0
fi

echo "🔍 进程 $PID 正在运行，准备停止..."

# 尝试优雅停止
kill $PID
echo "📤 已发送停止信号 (SIGTERM)..."

# 等待进程停止（最多等待3秒）
for i in {1..6}; do
    sleep 0.5
    if ! ps -p $PID > /dev/null 2>&1; then
        echo "✅ 进程已优雅停止"
        rm scheduler.pid
        echo "🗑️  已删除scheduler.pid文件"
        echo ""
        echo "📝 如需重启调度器，请运行: ./start_scheduler.sh"
        exit 0
    fi
done

# 如果3秒后还在运行，使用强制停止
echo "⚠️  进程仍在运行，使用强制停止 (SIGKILL)..."
kill -9 $PID
sleep 1

# 最终检查
if ps -p $PID > /dev/null 2>&1; then
    echo "❌ 进程停止失败，请手动处理"
    echo "🔧 手动停止命令: kill -9 $PID"
    echo "⚠️  scheduler.pid文件未删除，请手动检查"
    exit 1
fi

echo "✅ 进程已强制停止"
rm scheduler.pid
echo "🗑️  已删除scheduler.pid文件"
echo ""
echo "📝 如需重启调度器，请运行: ./start_scheduler.sh"

