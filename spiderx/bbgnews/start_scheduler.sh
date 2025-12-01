#!/bin/bash
# 启动 Bloomberg 新闻处理服务

echo "🚀 启动 Bloomberg 新闻处理服务..."
echo "⏰ 启动时间: $(date)"
echo ""

# 获取脚本所在目录（支持从任意位置运行）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 检查是否已在运行
if [ -f "scheduler.pid" ]; then
    PID=$(cat scheduler.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "⚠️  服务已在运行 (PID: $PID)"
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

# 检查必要文件
if [ ! -f "main.py" ]; then
    echo "❌ 错误: 缺少 main.py 文件"
    exit 1
fi

# 检查依赖
echo "🔍 检查依赖..."
$PYTHON_CMD -c "import flask, flask_cors, apscheduler, pymysql, requests" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  检测到缺少依赖，正在安装..."
    $PYTHON_CMD -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
fi

# 创建数据目录
if [ ! -d "captured_data" ]; then
    mkdir captured_data
    echo "📁 创建数据目录: captured_data"
fi

# 启动服务
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "🍎 macOS系统，使用caffeinate防止休眠"
    nohup caffeinate -i $PYTHON_CMD main.py > nohup.out 2>&1 &
else
    echo "🐧 Linux系统"
    nohup $PYTHON_CMD main.py > nohup.out 2>&1 &
fi

# 保存PID
PID=$!
echo $PID > scheduler.pid

echo "✅ 服务已启动 (PID: $PID)"
echo "📝 查看日志: tail -f bloomberg_service.log"
echo "📝 查看输出: tail -f nohup.out"
echo "🛑 停止服务: ./stop_scheduler.sh"
echo ""

# 等待服务启动
sleep 3

# 健康检查
echo "🔍 检查服务状态..."
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:1123/api/health 2>/dev/null)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ 服务运行正常"
    echo "🔗 健康检查: http://localhost:1123/api/health"
    echo "🔗 统计信息: http://localhost:1123/api/stats"
    echo "🔗 接收接口: http://localhost:1123/api/capture"
else
    echo "⚠️  服务可能未正常启动，请检查日志"
fi

echo ""
echo "👀 日志预览："
tail -10 bloomberg_service.log 2>/dev/null || echo "日志文件尚未生成，请稍等..."


