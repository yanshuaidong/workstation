#!/bin/bash

# Webhook服务管理脚本
# 使用方法: ./webhook-service.sh [start|stop|restart|status|install]

WEBHOOK_DIR="/opt/futures-system"
WEBHOOK_SCRIPT="webhook-server.py"
PID_FILE="$WEBHOOK_DIR/webhook.pid"
LOG_FILE="$WEBHOOK_DIR/webhook.log"
SERVICE_NAME="futures-webhook"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查是否在正确目录
check_directory() {
    if [ ! -f "$WEBHOOK_DIR/$WEBHOOK_SCRIPT" ]; then
        print_error "Webhook script not found: $WEBHOOK_DIR/$WEBHOOK_SCRIPT"
        exit 1
    fi
}

# 获取进程ID
get_pid() {
    if [ -f "$PID_FILE" ]; then
        cat "$PID_FILE"
    fi
}

# 检查进程是否运行
is_running() {
    local pid=$(get_pid)
    if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
        return 0
    else
        return 1
    fi
}

# 启动服务
start_service() {
    check_directory
    
    if is_running; then
        print_warning "Webhook service is already running (PID: $(get_pid))"
        return 0
    fi
    
    print_info "Starting webhook service..."
    
    cd "$WEBHOOK_DIR"
    
    # 设置环境变量
    export WEBHOOK_SECRET="${WEBHOOK_SECRET:-futures-webhook-secret-2024}"
    export PROJECT_PATH="$WEBHOOK_DIR"
    export WEBHOOK_PORT="${WEBHOOK_PORT:-9000}"
    
    # 启动服务
    nohup python3 "$WEBHOOK_SCRIPT" > "$LOG_FILE" 2>&1 &
    local pid=$!
    
    # 保存PID
    echo "$pid" > "$PID_FILE"
    
    # 等待服务启动
    sleep 2
    
    if is_running; then
        print_success "Webhook service started (PID: $pid)"
        print_info "Log file: $LOG_FILE"
        print_info "Health check: http://localhost:${WEBHOOK_PORT:-9000}/health"
    else
        print_error "Failed to start webhook service"
        cat "$LOG_FILE" | tail -10
        exit 1
    fi
}

# 停止服务
stop_service() {
    if ! is_running; then
        print_warning "Webhook service is not running"
        return 0
    fi
    
    local pid=$(get_pid)
    print_info "Stopping webhook service (PID: $pid)..."
    
    kill "$pid"
    
    # 等待进程停止
    local count=0
    while is_running && [ $count -lt 10 ]; do
        sleep 1
        count=$((count + 1))
    done
    
    if is_running; then
        print_warning "Force killing webhook service..."
        kill -9 "$pid"
        sleep 1
    fi
    
    rm -f "$PID_FILE"
    print_success "Webhook service stopped"
}

# 重启服务
restart_service() {
    stop_service
    sleep 1
    start_service
}

# 查看服务状态
status_service() {
    if is_running; then
        local pid=$(get_pid)
        print_success "Webhook service is running (PID: $pid)"
        
        # 显示端口信息
        local port=$(netstat -tlnp 2>/dev/null | grep "$pid" | awk '{print $4}' | cut -d':' -f2)
        if [ -n "$port" ]; then
            print_info "Listening on port: $port"
        fi
        
        # 显示最近的日志
        if [ -f "$LOG_FILE" ]; then
            print_info "Recent logs:"
            tail -5 "$LOG_FILE"
        fi
    else
        print_error "Webhook service is not running"
        
        # 显示最近的错误日志
        if [ -f "$LOG_FILE" ]; then
            print_info "Recent error logs:"
            tail -10 "$LOG_FILE" | grep -i error || echo "No error logs found"
        fi
        exit 1
    fi
}

# 安装systemd服务
install_systemd_service() {
    print_info "Installing systemd service..."
    
    # 创建systemd服务文件
    sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null <<EOF
[Unit]
Description=Futures System Webhook Service
After=network.target

[Service]
Type=forking
User=$USER
WorkingDirectory=$WEBHOOK_DIR
Environment=WEBHOOK_SECRET=${WEBHOOK_SECRET:-futures-webhook-secret-2024}
Environment=PROJECT_PATH=$WEBHOOK_DIR
Environment=WEBHOOK_PORT=${WEBHOOK_PORT:-9000}
ExecStart=$WEBHOOK_DIR/webhook-service.sh start
ExecStop=$WEBHOOK_DIR/webhook-service.sh stop
ExecReload=$WEBHOOK_DIR/webhook-service.sh restart
PIDFile=$PID_FILE
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    # 重新加载systemd
    sudo systemctl daemon-reload
    sudo systemctl enable ${SERVICE_NAME}
    
    print_success "Systemd service installed: ${SERVICE_NAME}"
    print_info "Use 'sudo systemctl start ${SERVICE_NAME}' to start"
    print_info "Use 'sudo systemctl status ${SERVICE_NAME}' to check status"
}

# 卸载systemd服务
uninstall_systemd_service() {
    print_info "Uninstalling systemd service..."
    
    sudo systemctl stop ${SERVICE_NAME} 2>/dev/null || true
    sudo systemctl disable ${SERVICE_NAME} 2>/dev/null || true
    sudo rm -f /etc/systemd/system/${SERVICE_NAME}.service
    sudo systemctl daemon-reload
    
    print_success "Systemd service uninstalled"
}

# 查看日志
show_logs() {
    if [ -f "$LOG_FILE" ]; then
        if [ "$2" = "-f" ] || [ "$2" = "--follow" ]; then
            tail -f "$LOG_FILE"
        else
            tail -50 "$LOG_FILE"
        fi
    else
        print_error "Log file not found: $LOG_FILE"
    fi
}

# 主函数
case "${1:-status}" in
    "start")
        start_service
        ;;
    "stop")
        stop_service
        ;;
    "restart")
        restart_service
        ;;
    "status")
        status_service
        ;;
    "install")
        install_systemd_service
        ;;
    "uninstall")
        uninstall_systemd_service
        ;;
    "logs")
        show_logs "$@"
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  start     - Start webhook service"
        echo "  stop      - Stop webhook service"
        echo "  restart   - Restart webhook service"
        echo "  status    - Show service status (default)"
        echo "  install   - Install systemd service"
        echo "  uninstall - Uninstall systemd service"
        echo "  logs      - Show logs (use -f to follow)"
        echo "  help      - Show this help"
        ;;
    *)
        print_error "Unknown command: $1"
        print_info "Use '$0 help' for available commands"
        exit 1
        ;;
esac
