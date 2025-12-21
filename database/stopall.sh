#!/bin/bash
# 一键停止所有数据库更新调度器

echo "╔═══════════════════════════════════════════════╗"
echo "║        🛑 停止所有数据库调度器                ║"
echo "╚═══════════════════════════════════════════════╝"
echo "⏰ 停止时间: $(date)"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 统计
SUCCESS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

# 定义要停止的调度器目录
SCHEDULERS=("futures" "institution" "stock")

echo "📋 待停止服务: ${#SCHEDULERS[@]} 个"
echo "───────────────────────────────────────────────"
echo ""

for DIR in "${SCHEDULERS[@]}"; do
    SERVICE_DIR="$SCRIPT_DIR/$DIR"
    
    if [ ! -d "$SERVICE_DIR" ]; then
        echo "⚠️  [$DIR] 目录不存在，跳过"
        ((SKIP_COUNT++))
        echo ""
        continue
    fi
    
    echo "⏹️  停止 [$DIR]..."
    
    STOP_SCRIPT="$SERVICE_DIR/stop_scheduler.sh"
    
    if [ ! -f "$STOP_SCRIPT" ]; then
        echo "   ⚠️  未找到停止脚本，跳过"
        ((SKIP_COUNT++))
        echo ""
        continue
    fi
    
    # 执行停止脚本
    cd "$SERVICE_DIR"
    bash "$STOP_SCRIPT" > /dev/null 2>&1
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "   ✅ 停止成功"
        ((SUCCESS_COUNT++))
    else
        echo "   ❌ 停止失败"
        ((FAIL_COUNT++))
    fi
    
    echo ""
    cd "$SCRIPT_DIR"
done

echo "───────────────────────────────────────────────"
echo "📊 停止结果汇总:"
echo "   ✅ 成功: $SUCCESS_COUNT"
echo "   ❌ 失败: $FAIL_COUNT"
echo "   ⏭️  跳过: $SKIP_COUNT"
echo ""
echo "💡 提示:"
echo "   - 启动服务: ./runall.sh"
echo "╔═══════════════════════════════════════════════╗"
echo "║        🎉 停止流程完成                        ║"
echo "╚═══════════════════════════════════════════════╝"

