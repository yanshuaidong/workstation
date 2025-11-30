#!/bin/bash
# 启动爬虫调度器示例

echo "🚀 启动调度器..."
echo "⏰ 启动时间: $(date)"
echo ""

# 获取脚本所在目录（支持从任意位置运行）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
echo "📂 工作目录: $SCRIPT_DIR"

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

# 检查并激活虚拟环境（推荐使用，但不强制）
if [ -d "venv" ]; then
    echo "🐍 检测到虚拟环境 venv，正在激活..."
    source venv/bin/activate
    PYTHON_CMD="python"
    echo "✅ 虚拟环境已激活: $(which python)"
elif [ -d ".venv" ]; then
    echo "🐍 检测到虚拟环境 .venv，正在激活..."
    source .venv/bin/activate
    PYTHON_CMD="python"
    echo "✅ 虚拟环境已激活: $(which python)"
else
    echo "⚠️  未检测到虚拟环境，使用系统Python"
    echo "💡 推荐创建虚拟环境: python3 -m venv venv"
    echo "   然后激活: source venv/bin/activate"
    echo ""
    # 检查系统Python环境
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "❌ 错误: 未找到Python解释器"
        exit 1
    fi
fi

echo "🐍 使用Python: $($PYTHON_CMD --version)"

# 检查必要文件
if [ ! -f "scheduler.py" ]; then
    echo "❌ 错误: 缺少 scheduler.py 文件"
    exit 1
fi

# 检查依赖（可选：如果有requirements.txt）
if [ -f "requirements.txt" ]; then
    echo "🔍 检查依赖..."
    $PYTHON_CMD -c "import apscheduler" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo "⚠️  检测到缺少依赖，正在安装..."
        $PYTHON_CMD -m pip install -r requirements.txt
        if [ $? -ne 0 ]; then
            echo "❌ 依赖安装失败"
            exit 1
        fi
        echo "✅ 依赖安装完成"
    else
        echo "✅ 依赖检查通过"
    fi
fi

# 启动调度器
echo ""
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
echo "📝 查看日志: tail -f scheduler.log"
echo "📝 查看输出: tail -f nohup.out"
echo "🛑 停止程序: ./stop_scheduler.sh"
echo ""

# 等待启动
sleep 2

# 输出预览
echo "👀 日志预览："
tail -10 scheduler.log 2>/dev/null || tail -10 nohup.out 2>/dev/null || echo "日志文件尚未生成，请稍等..."

