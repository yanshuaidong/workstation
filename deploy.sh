#!/bin/bash

# 期货数据系统部署脚本
# 使用方法: ./deploy.sh [start|stop|restart|logs|status]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印彩色信息
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

# 统一的 compose 命令封装（自动兼容 docker-compose 与 docker compose）
compose() {
    if command -v docker-compose >/dev/null 2>&1; then
        docker-compose "$@"
    elif docker compose version >/dev/null 2>&1; then
        docker compose "$@"
    else
        print_error "未检测到 Docker Compose。请安装独立的 docker-compose 或使用 Docker 内置的 docker compose 插件。"
        exit 1
    fi
}

# 检查Docker和Docker Compose
check_requirements() {
    print_info "检查系统要求..."

    if ! command -v docker &> /dev/null; then
        print_error "Docker未安装，请先安装Docker"
        exit 1
    fi

    # 这里通过封装函数进行一次探测
    if command -v docker-compose >/dev/null 2>&1; then
        print_info "检测到 docker-compose：$(docker-compose --version 2>/dev/null | head -n1)"
    elif docker compose version >/dev/null 2>&1; then
        print_info "检测到 docker compose 插件：$(docker compose version 2>/dev/null | head -n1)"
    else
        print_error "Docker Compose未安装，请先安装Docker Compose（独立二进制或 docker compose 插件）"
        exit 1
    fi

    print_success "系统要求检查通过"
}

# 创建必要的目录
create_directories() {
    print_info "创建必要的目录..."

    mkdir -p nginx/logs
    mkdir -p logs/backend

    print_success "目录创建完成"
}

# 检查环境配置
check_env() {
    print_info "检查环境配置..."

    if [ ! -f ".env" ]; then
        if [ -f "env.production" ]; then
            print_warning ".env文件不存在，复制env.production为.env"
            cp env.production .env
            print_warning "请根据实际情况修改.env文件中的配置"
        else
            print_error "环境配置文件不存在，请创建.env文件"
            exit 1
        fi
    fi

    print_success "环境配置检查完成"
}

# 构建和启动服务
start_services() {
    print_info "构建和启动服务..."

    # 停止可能存在的服务（忽略错误）
    compose down 2>/dev/null || true

    # 构建镜像
    print_info "构建Docker镜像..."
    compose build --no-cache

    # 启动服务
    print_info "启动服务..."
    compose up -d

    # 等待服务启动
    print_info "等待服务启动..."
    sleep 10

    # 检查服务状态
    check_services_status
}

# 停止服务
stop_services() {
    print_info "停止服务..."
    compose down
    print_success "服务已停止"
}

# 重启服务
restart_services() {
    print_info "重启服务..."
    stop_services
    start_services
}

# 检查服务状态
check_services_status() {
    print_info "检查服务状态..."

    # 检查容器状态
    echo "=== 容器状态 ==="
    compose ps

    echo ""
    echo "=== 服务健康检查 ==="

    # 检查Nginx
    if curl -f -s http://localhost/health > /dev/null; then
        print_success "Nginx服务正常"
    else
        print_error "Nginx服务异常"
    fi

    # 检查后端API
    if curl -f -s http://localhost/api-a/settings > /dev/null; then
        print_success "后端API服务正常"
    else
        print_warning "后端API服务可能需要更多时间启动"
    fi

    echo ""
    echo "=== 访问地址 ==="
    print_info "前端地址: http://localhost"
    print_info "后端API: http://localhost/api-a/"
}

# 查看日志
show_logs() {
    if [ -n "$2" ]; then
        # 查看特定服务的日志
        print_info "查看 $2 服务日志..."
        compose logs -f "$2"
    else
        # 查看所有服务日志
        print_info "查看所有服务日志..."
        compose logs -f
    fi
}

# 清理资源
cleanup() {
    print_info "清理Docker资源..."

    # 停止服务、删除容器/网络
    compose down || true

    # 删除镜像
    compose down --rmi all || true

    # 删除卷
    compose down --volumes || true

    # 清理未使用的资源
    docker system prune -f

    print_success "资源清理完成"
}

# 备份数据
backup_data() {
    print_info "备份数据..."

    BACKUP_DIR="backup/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    # 备份日志
    if [ -d "logs" ]; then
        cp -r logs "$BACKUP_DIR/"
    fi

    # 备份nginx配置
    if [ -d "nginx" ]; then
        cp -r nginx "$BACKUP_DIR/"
    fi

    print_success "数据备份完成: $BACKUP_DIR"
}

# 更新服务
update_services() {
    print_info "更新服务..."

    # 备份数据
    backup_data

    # 拉取最新代码（如果是从git部署）
    if [ -d ".git" ]; then
        print_info "拉取最新代码..."
        git pull
    fi

    # 重新构建和启动
    restart_services

    print_success "服务更新完成"
}

# 主函数
main() {
    case "${1:-start}" in
        "start")
            check_requirements
            create_directories
            check_env
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "status")
            check_services_status
            ;;
        "logs")
            show_logs "$@"
            ;;
        "cleanup")
            cleanup
            ;;
        "backup")
            backup_data
            ;;
        "update")
            update_services
            ;;
        "help"|"-h"|"--help")
            echo "使用方法: $0 [command]"
            echo ""
            echo "可用命令:"
            echo "  start    - 启动服务 (默认)"
            echo "  stop     - 停止服务"
            echo "  restart  - 重启服务"
            echo "  status   - 检查服务状态"
            echo "  logs     - 查看日志 (可指定服务名)"
            echo "  cleanup  - 清理Docker资源"
            echo "  backup   - 备份数据"
            echo "  update   - 更新服务"
            echo "  help     - 显示帮助信息"
            ;;
        *)
            print_error "未知命令: $1"
            print_info "使用 '$0 help' 查看可用命令"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
