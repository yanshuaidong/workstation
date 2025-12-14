#!/bin/bash
# 一键停止所有爬虫服务
# 遍历 spiderx 目录下所有子文件夹，执行停止脚本

echo "╔═══════════════════════════════════════════════╗"
echo "║        🛑 停止所有爬虫服务                    ║"
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

# 需要停止的服务目录列表（排除示例目录和没有停止脚本的目录）
SERVICES=(
    "bbgnews"
    "chatgpthelper"
    "clsnewscraper"
    "eastfutuscraper"
    "futurestop10"
    "geminihelper"
    "gthtposiscraper"
    "rtrsnews"
)

echo "📋 待停止服务: ${#SERVICES[@]} 个"
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
    
    echo "⏹️  停止 [$SERVICE]..."
    
    # 检查停止脚本（geminihelper/chatgpthelper 使用 stop_server.sh，其他使用 stop_scheduler.sh）
    if [ "$SERVICE" = "geminihelper" ] || [ "$SERVICE" = "chatgpthelper" ]; then
        STOP_SCRIPT="$SERVICE_DIR/stop_server.sh"
    else
        STOP_SCRIPT="$SERVICE_DIR/stop_scheduler.sh"
    fi
    
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
        echo "   ❌ 停止失败 (退出码: $EXIT_CODE)"
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
echo "   - 启动所有服务: ./runall.sh"
echo "╔═══════════════════════════════════════════════╗"
echo "║        🎉 停止流程完成                        ║"
echo "╚═══════════════════════════════════════════════╝"

