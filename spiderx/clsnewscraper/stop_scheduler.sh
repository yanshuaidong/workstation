#!/bin/bash
# 停止财联社新闻爬虫调度器

echo "🛑 停止财联社新闻爬虫调度器..."
echo "⏰ 停止时间: $(date)"
echo ""

# 检查是否存在scheduler.pid文件
if [ -f "scheduler.pid" ]; then
    PID=$(cat scheduler.pid)
    echo "📋 从scheduler.pid读取到进程ID: $PID"
    
    # 检查进程是否还在运行
    if ps -p $PID > /dev/null 2>&1; then
        echo "🔍 进程 $PID 正在运行，准备停止..."
        
        # 尝试优雅停止
        kill $PID
        echo "📤 已发送停止信号..."
        
        # 等待几秒看进程是否停止
        sleep 3
        
        # 检查进程是否还在运行
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚠️  进程仍在运行，使用强制停止..."
            kill -9 $PID
            sleep 2
            
            # 最终检查
            if ps -p $PID > /dev/null 2>&1; then
                echo "❌ 进程停止失败，请手动处理"
                echo "🔧 手动停止命令: kill -9 $PID"
                exit 1
            else
                echo "✅ 进程已强制停止"
            fi
        else
            echo "✅ 进程已优雅停止"
        fi
        
        # 删除pid文件
        rm scheduler.pid
        echo "🗑️  已删除scheduler.pid文件"
        
    else
        echo "⚠️  进程 $PID 不存在或已停止"
        rm scheduler.pid
        echo "🗑️  已删除过期的scheduler.pid文件"
    fi
    
else
    echo "⚠️  未找到scheduler.pid文件，尝试手动查找进程..."
    
    # 手动查找进程
    PIDS=$(ps aux | grep "main.py schedule" | grep -v grep | awk '{print $2}')
    
    if [ -z "$PIDS" ]; then
        echo "✅ 未发现运行中的调度器进程"
    else
        echo "🔍 发现以下进程:"
        ps aux | grep "main.py schedule" | grep -v grep
        echo ""
        
        for PID in $PIDS; do
            echo "🛑 停止进程 $PID..."
            kill $PID
        done
        
        sleep 3
        
        # 检查是否还有残留进程
        REMAINING=$(ps aux | grep "main.py schedule" | grep -v grep | awk '{print $2}')
        if [ -n "$REMAINING" ]; then
            echo "⚠️  发现残留进程，使用强制停止..."
            for PID in $REMAINING; do
                kill -9 $PID
            done
        fi
        
        echo "✅ 所有调度器进程已停止"
    fi
fi

echo ""
echo "🔍 最终检查..."
FINAL_CHECK=$(ps aux | grep "main.py schedule" | grep -v grep)

if [ -z "$FINAL_CHECK" ]; then
    echo "✅ 确认：所有调度器进程已停止"
    echo "📊 当前Python进程:"
    ps aux | grep python | grep -v grep | head -5
else
    echo "❌ 警告：仍有相关进程在运行"
    echo "$FINAL_CHECK"
fi

echo ""
echo "📝 提示: 如需重启调度器，请运行: ./start_scheduler.sh"
