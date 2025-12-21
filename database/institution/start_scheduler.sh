#!/bin/bash
# 启动机构持仓数据定时更新调度器

echo "🚀 启动机构持仓数据调度器..."
echo "⏰ 启动时间: $(date)"
echo ""

# 获取脚本所在目录（支持从任意位置运行）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
echo "📂 工作目录: $SCRIPT_DIR"

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
        rm scheduler.pid
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

echo "🐍 使用Python: $($PYTHON_CMD --version)"

# 检查必要文件
if [ ! -f "scheduler.py" ]; then
    echo "❌ 错误: 缺少 scheduler.py 文件"
    exit 1
fi

if [ ! -f "update.py" ]; then
    echo "❌ 错误: 缺少 update.py 文件"
    exit 1
fi

# 检查依赖
echo "🔍 检查依赖..."
$PYTHON_CMD -c "import apscheduler" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  检测到缺少 APScheduler，正在安装..."
    $PYTHON_CMD -m pip install apscheduler
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
    echo "✅ 依赖安装完成"
else
    echo "✅ 依赖检查通过"
fi

# 启动调度器
echo ""
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 macOS系统，使用caffeinate防止休眠"
    nohup $PYTHON_CMD scheduler.py > nohup.out 2>&1 &
    PYTHON_PID=$!
    caffeinate -i -w $PYTHON_PID &
    CAFFEINATE_PID=$!
    echo "$PYTHON_PID" > scheduler.pid
    echo "$CAFFEINATE_PID" >> scheduler.pid
    echo "☕ caffeinate 已启动 (PID: $CAFFEINATE_PID)"
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
    echo "📝 查看日志: tail -f scheduler.log"
    echo "📝 查看输出: tail -f nohup.out"
    echo "🛑 停止程序: ./stop_scheduler.sh"
else
    echo "❌ 调度器启动失败，请检查日志"
    rm -f scheduler.pid
    cat nohup.out 2>/dev/null
    exit 1
fi

echo ""
echo "👀 日志预览："
sleep 1
tail -10 scheduler.log 2>/dev/null || tail -10 nohup.out 2>/dev/null || echo "日志文件尚未生成，请稍等..."

