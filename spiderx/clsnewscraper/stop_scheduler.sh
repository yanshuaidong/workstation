#!/bin/bash
# 停止财联社新闻爬虫调度器

echo "🛑 停止财联社新闻爬虫调度器..."
echo "⏰ 停止时间: $(date)"
echo ""

# 检查是否存在scheduler.pid文件
if [ ! -f "scheduler.pid" ]; then
    echo "ℹ️  未找到scheduler.pid文件，调度器未在运行"
    echo "💡 提示: 这可能是误操作，无需关闭"
    exit 0
fi

# 读取PID
PID=$(cat scheduler.pid)
echo "📋 读取到进程ID: $PID"

# 检查进程是否存在
if ! ps -p $PID > /dev/null 2>&1; then
    echo "⚠️  进程 $PID 已不存在，删除过期的PID文件"
    rm scheduler.pid
    exit 0
fi

# 关闭进程
echo "🔍 进程 $PID 正在运行，准备停止..."
kill $PID
echo "📤 已发送停止信号，等待进程结束..."
sleep 3

# 确认关闭成功
if ps -p $PID > /dev/null 2>&1; then
    echo "⚠️  进程仍在运行，使用强制停止..."
    kill -9 $PID
    sleep 2
    
    # 最终确认
    if ps -p $PID > /dev/null 2>&1; then
        echo "❌ 进程停止失败"
        echo "🔧 请手动执行: kill -9 $PID"
        exit 1
    fi
fi

# 确认成功后删除PID文件
echo "✅ 进程已成功停止"
rm scheduler.pid
echo "🗑️  已删除scheduler.pid文件"
echo ""
echo "📝 提示: 如需重启调度器，请运行: ./start_scheduler.sh"
