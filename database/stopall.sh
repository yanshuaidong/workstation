#!/bin/bash
# 停止所有数据库更新调度器

echo "========================================"
echo "🛑 停止所有数据库更新调度器"
echo "⏰ 停止时间: $(date)"
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
NOT_RUNNING=0

# 定义要停止的调度器目录
SCHEDULERS=("futures" "institution" "stock")
NAMES=("期货数据" "机构持仓" "股票数据")

# 逐个停止
for i in "${!SCHEDULERS[@]}"; do
    DIR="${SCHEDULERS[$i]}"
    NAME="${NAMES[$i]}"
    
    echo "----------------------------------------"
    echo "📊 停止 ${NAME} 调度器 (${DIR})"
    echo "----------------------------------------"
    
    if [ ! -d "$DIR" ]; then
        echo "❌ 目录不存在: $DIR"
        ((FAIL_COUNT++))
        echo ""
        continue
    fi
    
    if [ ! -f "$DIR/stop_scheduler.sh" ]; then
        echo "❌ 停止脚本不存在: $DIR/stop_scheduler.sh"
        ((FAIL_COUNT++))
        echo ""
        continue
    fi
    
    # 检查是否在运行
    if [ ! -f "$DIR/scheduler.pid" ]; then
        echo "⚠️  ${NAME}调度器未在运行"
        ((NOT_RUNNING++))
        echo ""
        continue
    fi
    
    # 停止调度器
    cd "$DIR"
    bash stop_scheduler.sh
    
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
echo "📋 停止汇总"
echo "========================================"
echo "  ✅ 成功停止: $SUCCESS_COUNT 个"
echo "  ⚠️  未在运行: $NOT_RUNNING 个"
echo "  ❌ 停止失败: $FAIL_COUNT 个"
echo ""
echo "💡 重新启动所有调度器: ./runall.sh"
echo "========================================"

