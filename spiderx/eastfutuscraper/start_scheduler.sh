#!/bin/bash
# 启动东方财富期货数据爬虫调度器
# 使用nohup在后台运行，输出重定向到nohup.out

echo "🚀 启动东方财富期货数据爬虫调度器..."
echo "📁 当前目录: $(pwd)"
echo "⏰ 开始时间: $(date)"
echo "📋 运行模式: 14天长期调度（仅交易日下午4点执行）"
echo ""

# 检查是否已经有调度器在运行
if [ -f "scheduler.pid" ]; then
    OLD_PID=$(cat scheduler.pid)
    if ps -p $OLD_PID > /dev/null 2>&1; then
        echo "⚠️  检测到调度器已在运行 (PID: $OLD_PID)"
        echo "❌ 无法启动，请先停止现有调度器: ./stop_scheduler.sh"
        exit 1
    else
        echo "🗑️  清理过期的PID文件..."
        rm -f scheduler.pid
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

echo "🐍 使用Python: $PYTHON_CMD"

# 检查scheduler.py是否存在
if [ ! -f "scheduler.py" ]; then
    echo "❌ 错误: 未找到scheduler.py文件，请确保在正确的目录下运行"
    exit 1
fi

# 检查main.py是否存在
if [ ! -f "main.py" ]; then
    echo "❌ 错误: 未找到main.py文件，请确保在正确的目录下运行"
    exit 1
fi

echo "📝 控制台输出将保存到: nohup.out"
echo "📂 详细日志将保存到: logs/ 目录"
echo ""

# 检查操作系统类型
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 检测到macOS系统，使用caffeinate防止系统休眠"
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
    echo "🐧 检测到非macOS系统，直接启动"
    nohup $PYTHON_CMD scheduler.py > nohup.out 2>&1 &
    PYTHON_PID=$!
    echo "$PYTHON_PID" > scheduler.pid
fi

# 等待进程实际启动
sleep 1

# 验证进程是否成功启动
if ps -p $PYTHON_PID > /dev/null 2>&1; then
    echo "✅ 调度器已在后台启动"
    echo "🆔 进程ID: $PYTHON_PID"
    echo "📝 进程信息已保存到: scheduler.pid"
    echo ""
    echo "📖 查看命令："
    echo "  - 实时查看输出: tail -f nohup.out"
    echo "  - 查看详细日志: tail -f logs/futures_crawler_\$(date +%Y-%m-%d).log"
    echo "🛑 停止命令: ./stop_scheduler.sh"
else
    echo "❌ 调度器启动失败，请检查日志"
    rm -f scheduler.pid
    cat nohup.out 2>/dev/null
    exit 1
fi

echo ""
echo "👀 前10行输出预览："
sleep 1
head -10 nohup.out 2>/dev/null || echo "输出文件尚未生成，请稍等..."

