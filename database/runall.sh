#!/bin/bash
# 启动所有数据库更新调度器

echo "========================================"
echo "🚀 启动所有数据库更新调度器"
echo "⏰ 启动时间: $(date)"
echo "========================================"
echo ""

# 获取脚本所在目录（支持从任意位置运行）
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"
echo "📂 工作目录: $SCRIPT_DIR"
echo ""

# 统计
SUCCESS_COUNT=0
FAIL_COUNT=0
ALREADY_RUNNING=0

# 定义要启动的调度器目录
SCHEDULERS=("futures" "institution" "stock")
NAMES=("期货数据" "机构持仓" "股票数据")

# 逐个启动
for i in "${!SCHEDULERS[@]}"; do
    DIR="${SCHEDULERS[$i]}"
    NAME="${NAMES[$i]}"
    
    echo "----------------------------------------"
    echo "📊 启动 ${NAME} 调度器 (${DIR})"
    echo "----------------------------------------"
    
    if [ ! -d "$DIR" ]; then
        echo "❌ 目录不存在: $DIR"
        ((FAIL_COUNT++))
        echo ""
        continue
    fi
    
    if [ ! -f "$DIR/start_scheduler.sh" ]; then
        echo "❌ 启动脚本不存在: $DIR/start_scheduler.sh"
        ((FAIL_COUNT++))
        echo ""
        continue
    fi
    
    # 检查是否已在运行
    if [ -f "$DIR/scheduler.pid" ]; then
        PYTHON_PID=$(head -1 "$DIR/scheduler.pid")
        if ps -p $PYTHON_PID > /dev/null 2>&1; then
            echo "⚠️  ${NAME}调度器已在运行 (PID: $PYTHON_PID)"
            ((ALREADY_RUNNING++))
            echo ""
            continue
        fi
    fi
    
    # 启动调度器
    cd "$DIR"
    bash start_scheduler.sh
    
    if [ $? -eq 0 ]; then
        ((SUCCESS_COUNT++))
    else
        ((FAIL_COUNT++))
    fi
    
    cd "$SCRIPT_DIR"
    echo ""
done

# 汇总
echo "========================================"
echo "📋 启动汇总"
echo "========================================"
echo "  ✅ 成功启动: $SUCCESS_COUNT 个"
echo "  ⚠️  已在运行: $ALREADY_RUNNING 个"
echo "  ❌ 启动失败: $FAIL_COUNT 个"
echo ""
echo "💡 停止所有调度器: ./stopall.sh"
echo "💡 查看各调度器日志:"
for DIR in "${SCHEDULERS[@]}"; do
    echo "   tail -f $DIR/scheduler.log"
done
echo "========================================"

