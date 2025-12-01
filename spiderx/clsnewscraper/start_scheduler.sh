#!/bin/bash
# 启动财联社新闻爬虫调度器
# 使用nohup在后台运行，输出重定向到nohup.out

echo "🚀 启动财联社新闻爬虫调度器..."
echo "📁 当前目录: $(pwd)"
echo "⏰ 开始时间: $(date)"
echo ""

# 检查是否已在运行
if [ -f "scheduler.pid" ]; then
    OLD_PID=$(cat scheduler.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "⚠️  调度器已在运行中 (PID: $OLD_PID)"
        echo "💡 如需重启，请先运行: ./stop_scheduler.sh"
        exit 1
    else
        echo "⚠️  发现过期的PID文件，清理中..."
        rm scheduler.pid
    fi
fi

# 检查Python环境
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ 错误: 未找到Python解释器"
    exit 1
fi

echo "🐍 使用Python: $($PYTHON_CMD --version 2>&1)"

# 检查main.py是否存在
if [ ! -f "main.py" ]; then
    echo "❌ 错误: 未找到main.py文件"
    exit 1
fi

# 启动进程
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 macOS系统，使用caffeinate防止休眠"
    nohup $PYTHON_CMD main.py schedule > nohup.out 2>&1 &
    PYTHON_PID=$!
    # 使用 caffeinate 跟踪 Python 进程，防止系统休眠
    caffeinate -i -w $PYTHON_PID &
    CAFFEINATE_PID=$!
    # 保存两个 PID：第一行 Python，第二行 caffeinate
    echo "$PYTHON_PID" > scheduler.pid
    echo "$CAFFEINATE_PID" >> scheduler.pid
    echo "☕ caffeinate 已启动 (PID: $CAFFEINATE_PID)，跟踪 Python 进程"
else
    echo "🐧 启动调度器..."
    nohup $PYTHON_CMD main.py schedule > nohup.out 2>&1 &
    PYTHON_PID=$!
    echo "$PYTHON_PID" > scheduler.pid
fi

# 等待进程实际启动
sleep 1

# 验证进程是否成功启动
if ps -p $PYTHON_PID > /dev/null 2>&1; then
    echo "✅ 调度器已启动 (PID: $PYTHON_PID)"
    echo "📝 实时查看输出: tail -f nohup.out"
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
