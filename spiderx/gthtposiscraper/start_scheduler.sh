#!/bin/bash
# 启动国泰君安持仓数据爬虫调度器

echo "🚀 启动国泰君安持仓数据爬虫调度器..."
echo "⏰ 启动时间: $(date)"
echo ""

# 检查是否已在运行
if [ -f "scheduler.pid" ]; then
    PID=$(cat scheduler.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  调度器已在运行 (PID: $PID)"
        echo "🛑 如需重启，请先运行: ./stop_scheduler.sh"
        exit 1
    else
        echo "🗑️  清理过期的PID文件..."
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

# 检查必要文件
if [ ! -f "scheduler.py" ] || [ ! -f "main.py" ]; then
    echo "❌ 错误: 缺少必要文件，请确保在正确的目录下运行"
    exit 1
fi

# 启动调度器
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 macOS系统，使用caffeinate防止休眠"
    nohup caffeinate -i $PYTHON_CMD scheduler.py > nohup.out 2>&1 &
else
    echo "🐧 Linux系统"
    nohup $PYTHON_CMD scheduler.py > nohup.out 2>&1 &
fi

# 保存PID
PID=$!
echo $PID > scheduler.pid

echo "✅ 调度器已启动 (PID: $PID)"
echo "📝 查看输出: tail -f nohup.out"
echo "🛑 停止程序: ./stop_scheduler.sh"
echo ""

# 输出预览
sleep 2
echo "👀 输出预览："
head -10 nohup.out 2>/dev/null || echo "输出文件尚未生成，请稍等..."

