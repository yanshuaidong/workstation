#!/bin/bash
# 启动国泰君安持仓数据爬虫调度器
# 使用nohup在后台运行，输出重定向到nohup.out

echo "🚀 启动国泰君安持仓数据爬虫调度器..."
echo "📁 当前目录: $(pwd)"
echo "⏰ 开始时间: $(date)"
echo "📋 运行模式: 14天长期调度（仅交易日下午18:30执行）"
echo "📝 控制台输出将保存到: nohup.out"
echo "📂 详细日志将保存到: logs/ 目录"
echo ""

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

# 检查操作系统类型
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 检测到macOS系统，使用caffeinate防止系统休眠"
    # macOS使用caffeinate防止系统休眠
    nohup caffeinate -i $PYTHON_CMD scheduler.py > nohup.out 2>&1 &
else
    echo "🐧 检测到非macOS系统，直接启动"
    # 其他系统直接运行
    nohup $PYTHON_CMD scheduler.py > nohup.out 2>&1 &
fi

# 获取进程ID
PID=$!

echo "✅ 调度器已在后台启动"
echo "🆔 进程ID: $PID"
echo "📝 实时查看输出: tail -f nohup.out"
echo "🔍 查看详细日志: tail -f logs/position_crawler_\$(date +%Y-%m-%d).log"
echo "🛑 停止程序: kill $PID 或运行 ./stop_scheduler.sh"
echo ""
echo "进程信息已保存到 scheduler.pid 文件"
echo $PID > scheduler.pid

echo "👀 前10行输出预览："
sleep 2
head -10 nohup.out 2>/dev/null || echo "输出文件尚未生成，请稍等..."

