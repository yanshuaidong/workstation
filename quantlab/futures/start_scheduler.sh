#!/bin/bash
# 启动期货多策略预测调度器

echo "🚀 启动期货多策略预测调度器..."
echo "⏰ 启动时间: $(date)"
echo ""

# 切换到脚本所在目录
cd "$(dirname "$0")" || exit 1

# 检查是否已在运行
if [ -f "scheduler.pid" ]; then
    # 读取第一行作为 Python PID
    PYTHON_PID=$(head -1 scheduler.pid)
    if ps -p $PYTHON_PID > /dev/null 2>&1; then
        echo "⚠️  调度器已在运行 (PID: $PYTHON_PID)"
        echo "🛑 如需重启，请先运行: ./stop_scheduler.sh"
        exit 1
    else
        echo "🗑️  清理过期的PID文件..."
        rm -f scheduler.pid
    fi
fi

# 检查 Python 环境
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "❌ 错误: 未找到Python解释器"
    exit 1
fi

echo "🐍 使用 Python: $($PYTHON_CMD --version)"

# 检查必要文件
if [ ! -f "scheduler.py" ] || [ ! -f "predict.py" ]; then
    echo "❌ 错误: 缺少必要文件，请确保在正确的目录下运行"
    exit 1
fi

# 启动调度器，保存所有相关进程的 PID
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 macOS系统，使用caffeinate防止休眠"
    nohup $PYTHON_CMD scheduler.py > nohup.out 2>&1 &
    PYTHON_PID=$!
    # 使用 caffeinate 跟踪 Python 进程，防止系统休眠
    caffeinate -i -w $PYTHON_PID &
    CAFFEINATE_PID=$!
    # 保存两个 PID：第一行 Python，第二行 caffeinate
    echo "$PYTHON_PID" > scheduler.pid
    echo "$CAFFEINATE_PID" >> scheduler.pid
    echo "☕ caffeinate 已启动 (PID: $CAFFEINATE_PID)，跟踪 Python 进程"
else
    echo "🐧 Linux系统"
    nohup $PYTHON_CMD scheduler.py > nohup.out 2>&1 &
    PYTHON_PID=$!
    echo "$PYTHON_PID" > scheduler.pid
fi

# 等待进程实际启动
sleep 1

# 验证进程是否成功启动
if ps -p $PYTHON_PID > /dev/null 2>&1; then
    echo "✅ 调度器已启动 (PID: $PYTHON_PID)"
    echo "📝 查看输出: tail -f nohup.out"
    echo "🛑 停止程序: ./stop_scheduler.sh"
else
    echo "❌ 调度器启动失败，请检查日志"
    rm -f scheduler.pid
    cat nohup.out 2>/dev/null
    exit 1
fi

