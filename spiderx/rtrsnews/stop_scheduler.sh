#!/bin/bash

# ============================================================
# Reuters 路透社新闻采集服务停止脚本
# 功能：停止 Reuters 新闻采集和处理服务
# ============================================================

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_header() {
    echo -e "${BLUE}============================================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================================${NC}"
}

# 停止服务
stop_service() {
    log_header "🛑 停止 Reuters 新闻采集服务"
    
    STOPPED=false
    
    # 方法1：通过PID文件停止
    if [ -f "reuters_service.pid" ]; then
        PID=$(cat reuters_service.pid)
        if ps -p $PID > /dev/null 2>&1; then
            log_info "通过PID文件停止服务 (PID: $PID)..."
            kill $PID 2>/dev/null
            sleep 2
            
            # 如果还在运行，强制终止
            if ps -p $PID > /dev/null 2>&1; then
                log_warn "进程未响应，强制终止..."
                kill -9 $PID 2>/dev/null
            fi
            STOPPED=true
        fi
        rm -f reuters_service.pid
    fi
    
    # 方法2：通过端口查找并停止
    PIDS=$(lsof -ti:1125 2>/dev/null)
    if [ ! -z "$PIDS" ]; then
        log_info "通过端口 1125 停止服务..."
        for PID in $PIDS; do
            log_info "终止进程: $PID"
            kill $PID 2>/dev/null
        done
        sleep 2
        
        # 再次检查，强制终止
        PIDS=$(lsof -ti:1125 2>/dev/null)
        if [ ! -z "$PIDS" ]; then
            log_warn "进程未响应，强制终止..."
            for PID in $PIDS; do
                kill -9 $PID 2>/dev/null
            done
        fi
        STOPPED=true
    fi
    
    # 方法3：通过进程名查找并停止
    PIDS=$(pgrep -f "python.*main.py" 2>/dev/null | head -5)
    if [ ! -z "$PIDS" ]; then
        for PID in $PIDS; do
            # 检查是否是reuters目录下的进程
            CMDLINE=$(ps -p $PID -o args= 2>/dev/null)
            if echo "$CMDLINE" | grep -q "rtrsnews"; then
                log_info "终止Reuters进程: $PID"
                kill $PID 2>/dev/null
                STOPPED=true
            fi
        done
    fi
    
    # 检查结果
    sleep 1
    if lsof -Pi :1125 -sTCP:LISTEN -t >/dev/null 2>&1; then
        log_error "服务停止失败，端口 1125 仍被占用"
        log_info "尝试强制终止..."
        PIDS=$(lsof -ti:1125 2>/dev/null)
        for PID in $PIDS; do
            kill -9 $PID 2>/dev/null
        done
        sleep 1
    fi
    
    if ! lsof -Pi :1125 -sTCP:LISTEN -t >/dev/null 2>&1; then
        if [ "$STOPPED" = true ]; then
            log_info "✅ Reuters新闻采集服务已停止"
        else
            log_info "ℹ️ 服务未在运行"
        fi
    else
        log_error "无法停止服务，请手动检查"
        exit 1
    fi
}

# 主函数
main() {
    stop_service
}

main "$@"

