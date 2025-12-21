#!/bin/bash
# 一键启动所有量化预测服务
# 遍历 quantlab 目录下所有子文件夹，执行启动脚本

echo "╔═══════════════════════════════════════════════╗"
echo "║        🚀 启动所有量化预测服务                ║"
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

# 需要启动的服务目录列表
SERVICES=(
    "futures"
    "institution"
)

echo "📋 待启动服务: ${#SERVICES[@]} 个"
echo "───────────────────────────────────────────────"
echo ""

for SERVICE in "${SERVICES[@]}"; do
    SERVICE_DIR="$SCRIPT_DIR/$SERVICE"
    
    if [ ! -d "$SERVICE_DIR" ]; then
        echo "⚠️  [$SERVICE] 目录不存在，跳过"
        ((SKIP_COUNT++))
        echo ""
        continue
    fi
    
    echo "▶️  启动 [$SERVICE]..."
    
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
    elif [ $EXIT_CODE -eq 1 ]; then
        # 通常返回1表示已在运行
        echo "   ⏸️  已在运行或启动失败，请检查"
        ((FAIL_COUNT++))
    else
        echo "   ❌ 启动失败 (退出码: $EXIT_CODE)"
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
echo "   - 查看各服务日志: tail -f <服务目录>/nohup.out"
echo "   - 停止所有服务: ./stopall.sh"
echo "╔═══════════════════════════════════════════════╗"
echo "║        🎉 启动流程完成                        ║"
echo "╚═══════════════════════════════════════════════╝"

