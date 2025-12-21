#!/bin/bash
# 一键启动所有数据库更新调度器

echo "╔═══════════════════════════════════════════════╗"
echo "║        🚀 启动所有数据库调度器                ║"
echo "╚═══════════════════════════════════════════════╝"
echo "⏰ 启动时间: $(date)"
echo ""

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 统计
SUCCESS_COUNT=0
FAIL_COUNT=0
SKIP_COUNT=0

# 定义要启动的调度器目录
SCHEDULERS=("futures" "institution" "stock")

echo "📋 待启动服务: ${#SCHEDULERS[@]} 个"
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
    
    echo "▶️  启动 [$DIR]..."
    
    START_SCRIPT="$SERVICE_DIR/start_scheduler.sh"
    
    if [ ! -f "$START_SCRIPT" ]; then
        echo "   ⚠️  未找到启动脚本，跳过"
        ((SKIP_COUNT++))
        echo ""
        continue
    fi
    
    # 执行启动脚本
    cd "$SERVICE_DIR"
    bash "$START_SCRIPT" > /dev/null 2>&1
    EXIT_CODE=$?
    
    if [ $EXIT_CODE -eq 0 ]; then
        echo "   ✅ 启动成功"
        ((SUCCESS_COUNT++))
    else
        echo "   ⏸️  已在运行或启动失败"
        ((FAIL_COUNT++))
    fi
    
    echo ""
    cd "$SCRIPT_DIR"
done

echo "───────────────────────────────────────────────"
echo "📊 启动结果汇总:"
echo "   ✅ 成功: $SUCCESS_COUNT"
echo "   ❌ 失败/已运行: $FAIL_COUNT"
echo "   ⏭️  跳过: $SKIP_COUNT"
echo ""
echo "💡 提示:"
echo "   - 查看日志: tail -f <服务目录>/scheduler.log"
echo "   - 停止服务: ./stopall.sh"
echo "╔═══════════════════════════════════════════════╗"
echo "║        🎉 启动流程完成                        ║"
echo "╚═══════════════════════════════════════════════╝"

