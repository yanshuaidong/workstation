#!/bin/bash

# 期货数据系统部署脚本
# 使用方法: ./deploy.sh [deploy|start|stop|restart|logs|status|add-service]

set -e

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

# 统一的 compose 命令
compose() {
    if command -v docker-compose >/dev/null 2>&1; then
        docker-compose "$@"
    elif docker compose version >/dev/null 2>&1; then
        docker compose "$@"
    else
        print_error "Docker Compose 未安装"
        exit 1
    fi
}

# 检查系统资源
check_system_resources() {
    if command -v free >/dev/null 2>&1; then
        local total_memory=$(free -m | awk 'NR==2{printf "%.0f", $2}')
        local available_memory=$(free -m | awk 'NR==2{printf "%.0f", $7}')
        local swap_total=$(free -m | awk 'NR==3{printf "%.0f", $2}')
        local swap_used=$(free -m | awk 'NR==3{printf "%.0f", $3}')
        
        print_info "系统内存状态:"
        print_info "  总内存: ${total_memory}MB"
        print_info "  可用内存: ${available_memory}MB"
        print_info "  Swap总量: ${swap_total}MB"
        print_info "  Swap已用: ${swap_used}MB"
        
        # 内存不足警告和自动创建swap
        if [ "$available_memory" -lt 1024 ]; then
            print_warning "可用内存不足1GB，构建可能失败"
            
            # 检查是否有足够的swap
            local swap_available=$((swap_total - swap_used))
            if [ "$swap_available" -lt 1024 ]; then
                print_warning "Swap空间不足，尝试自动创建swap空间..."
                
                # 检查是否已存在swapfile
                if [ ! -f "/swapfile" ]; then
                    print_info "创建2GB swap文件..."
                    if fallocate -l 2G /swapfile 2>/dev/null && \
                       chmod 600 /swapfile && \
                       mkswap /swapfile >/dev/null 2>&1 && \
                       swapon /swapfile 2>/dev/null; then
                        print_success "Swap空间创建成功"
                        # 添加到fstab以便重启后自动挂载
                        if ! grep -q "/swapfile" /etc/fstab 2>/dev/null; then
                            echo "/swapfile none swap sw 0 0" >> /etc/fstab 2>/dev/null || true
                        fi
                    else
                        print_warning "自动创建swap失败，请手动创建:"
                        print_info "  sudo fallocate -l 2G /swapfile"
                        print_info "  sudo chmod 600 /swapfile"
                        print_info "  sudo mkswap /swapfile"
                        print_info "  sudo swapon /swapfile"
                    fi
                else
                    print_info "Swap文件已存在，尝试启用..."
                    swapon /swapfile 2>/dev/null || true
                fi
            fi
            
            print_info "正在尝试释放内存..."
            # 清理Docker缓存
            docker system prune -f --volumes >/dev/null 2>&1 || true
            # 清理系统缓存
            sync && echo 3 | tee /proc/sys/vm/drop_caches >/dev/null 2>&1 || true
        fi
    fi
}

# 浏览器环境测试功能已移除 - 爬虫功能已迁移到 spiderx 项目

# 部署更新（拉代码+重启）
deploy_update() {
    local branch=${1:-main}
    
    print_info "开始部署更新，分支: $branch"
    
    # 检查Git仓库
    if [ ! -d ".git" ]; then
        print_error "当前目录不是Git仓库"
        exit 1
    fi
    
    # 停止服务
    print_info "停止服务..."
    compose down || true
    
    # 备份当前版本
    local backup_commit=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    print_info "备份当前版本: ${backup_commit:0:8}"
    
    # 拉取最新代码
    print_info "拉取最新代码..."
    git fetch origin
    git checkout $branch
    git reset --hard origin/$branch
    
    local new_commit=$(git rev-parse HEAD)
    print_success "更新到版本: ${new_commit:0:8}"
    
    # 显示更新内容
    if [ "$backup_commit" != "$new_commit" ] && [ "$backup_commit" != "unknown" ]; then
        print_info "更新内容:"
        git log --oneline $backup_commit..$new_commit | head -5
    fi
    
    # 检查环境配置
    if [ ! -f ".env" ]; then
        if [ -f "env.production" ]; then
            print_info "创建环境配置文件..."
            cp env.production .env
        else
            print_error "环境配置文件不存在"
            exit 1
        fi
    fi
    
    # 重新构建并启动
    print_info "构建并启动服务..."
    
    # 设置 Docker BuildKit 和内存优化
    export DOCKER_BUILDKIT=1
    export BUILDKIT_PROGRESS=plain
    
    # 检查系统内存和swap
    check_system_resources
    
    # 构建时添加内存限制（适合2GB内存服务器）
    print_info "开始构建镜像（使用内存优化配置）..."
    # 先尝试逐个构建服务以减少内存压力
    if ! compose build --no-cache workfront; then
        print_warning "前端构建失败，尝试释放内存后重试..."
        docker system prune -f --volumes || true
        if ! compose build --no-cache workfront; then
            print_error "前端构建仍然失败"
            exit 1
        fi
    fi
    
    if ! compose build --no-cache automysqlback; then
        print_warning "后端构建失败，尝试释放内存后重试..."
        docker system prune -f --volumes || true
        if ! compose build --no-cache automysqlback; then
            print_error "后端构建仍然失败"
            exit 1
        fi
    fi
    
    compose up -d
    
    # 等待服务启动
    print_info "等待服务启动..."
    sleep 15
    
    # 检查服务状态
    check_services
    
    # 浏览器测试已移除 - 爬虫功能已迁移到 spiderx 项目
    print_info "注意：爬虫功能已迁移到 spiderx 项目，请在本地运行"
    
    print_success "部署完成！"
}

# 等待服务健康
wait_for_service() {
    local service_name=$1
    local check_url=$2
    local max_wait=${3:-120}
    local wait_time=0
    
    print_info "等待 $service_name 服务启动..."
    
    while [ $wait_time -lt $max_wait ]; do
        if curl -f -s "$check_url" > /dev/null 2>&1; then
            print_success "$service_name 服务已就绪"
            return 0
        else
            printf "."
            sleep 5
            wait_time=$((wait_time + 5))
        fi
    done
    
    echo ""
    print_error "$service_name 服务启动超时 (${max_wait}秒)"
    return 1
}

# 检查容器状态
check_container() {
    local container_name=$1
    local max_wait=${2:-60}
    local wait_time=0
    
    print_info "检查容器 $container_name 状态..."
    
    while [ $wait_time -lt $max_wait ]; do
        local status=$(docker inspect -f '{{.State.Status}}' "$container_name" 2>/dev/null || echo "not_found")
        
        case "$status" in
            "running")
                print_success "容器 $container_name 正在运行"
                return 0
                ;;
            "not_found")
                print_info "容器 $container_name 不存在，等待创建..."
                ;;
            "exited"|"dead")
                print_error "容器 $container_name 已退出，状态: $status"
                return 1
                ;;
            *)
                print_info "容器 $container_name 状态: $status，继续等待..."
                ;;
        esac
        
        sleep 5
        wait_time=$((wait_time + 5))
    done
    
    print_error "容器 $container_name 检查超时"
    return 1
}

# 启动服务
start_services() {
    print_info "启动期货数据系统服务（轻量级版本）..."
    
    # 检查环境配置
    if [ ! -f ".env" ]; then
        if [ -f "env.production" ]; then
            print_info "复制生产环境配置..."
            cp env.production .env
        else
            print_error "环境配置文件不存在"
            exit 1
        fi
    fi
    
    # 1. 启动后端服务
    print_info "第1步: 启动后端 API 服务..."
    compose up -d automysqlback
    
    # 等待后端容器启动
    if ! check_container "futures-backend" 120; then
        print_error "后端容器启动失败"
        compose logs automysqlback
        return 1
    fi
    
    # 2. 启动前端服务
    print_info "第2步: 启动前端服务..."
    compose up -d workfront
    
    # 3. 最后启动 Nginx 代理
    print_info "第3步: 启动 Nginx 反向代理..."
    compose up -d nginx
    
    # 等待服务完全启动
    print_info "第4步: 等待服务完全启动..."
    sleep 10
    
    # 检查服务状态
    check_services
    
    print_success "所有服务启动完成！"
    print_info "注意：爬虫功能已迁移到 spiderx 项目，请在本地运行"
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
    compose down
    compose up -d
    sleep 5
    check_services
}

# 检查服务状态
check_services() {
    print_info "检查服务状态..."
    
    compose ps
    
    echo ""
    print_info "服务健康检查:"
    
    # 检查前端
    if curl -f -s http://localhost/ > /dev/null 2>&1; then
        print_success "前端服务正常"
    else
        print_warning "前端服务异常"
    fi
    
    # 检查后端API
    if curl -f -s http://localhost/api-a/settings > /dev/null 2>&1; then
        print_success "后端API服务正常"
    else
        print_warning "后端API服务异常"
    fi
    
    # Selenium服务已移除 - 爬虫功能已迁移到 spiderx 项目
    
    echo ""
    print_info "访问地址:"
    print_info "  前端: http://localhost"
    print_info "  后端API: http://localhost/api-a/"
    # print_info "  监控面板: http://localhost/monitor/"  # 已停用portainer
}

# 查看日志
show_logs() {
    if [ -n "$2" ]; then
        compose logs -f "$2"
    else
        compose logs -f
    fi
}

# 添加新服务
add_service() {
    local service_name=$2
    local port=$3
    
    if [ -z "$service_name" ] || [ -z "$port" ]; then
        print_error "使用方法: $0 add-service <服务名> <端口>"
        print_error "例如: $0 add-service newservice 7002"
        exit 1
    fi
    
    print_info "添加新服务: $service_name (端口: $port)"
    
    # 检查docker-compose.yml是否存在该服务
    if grep -q "^  $service_name:" docker-compose.yml; then
        print_warning "服务 $service_name 已存在于 docker-compose.yml"
    else
        print_info "请手动在 docker-compose.yml 中添加服务配置"
        print_info "然后在 nginx/nginx.conf 中添加代理配置"
    fi
    
    # 检查nginx配置
    if grep -q "server $service_name:$port" nginx/nginx.conf; then
        print_warning "Nginx配置中已存在该服务"
    else
        print_info "需要在 nginx/nginx.conf 中添加以下配置:"
        echo ""
        echo "    upstream ${service_name}_api {"
        echo "        server $service_name:$port;"
        echo "        keepalive 32;"
        echo "    }"
        echo ""
        echo "    location /api-${service_name}/ {"
        echo "        rewrite ^/api-${service_name}/(.*)$ /api/$1 break;"
        echo "        proxy_pass http://${service_name}_api;"
        echo "        proxy_set_header Host \$host;"
        echo "        proxy_set_header X-Real-IP \$remote_addr;"
        echo "        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;"
        echo "        proxy_set_header X-Forwarded-Proto \$scheme;"
        echo "        proxy_http_version 1.1;"
        echo "        proxy_set_header Connection \"\";"
        echo "    }"
        echo ""
        print_info "添加配置后运行: $0 restart"
    fi
}

# Selenium测试功能已移除 - 爬虫功能已迁移到 spiderx 项目

# 主函数
main() {
    case "${1:-help}" in
        "deploy")
            deploy_update "$2"
            ;;
        "start")
            start_services
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "status")
            check_services
            ;;
        "logs")
            show_logs "$@"
            ;;
        "add-service")
            add_service "$@"
            ;;
        "help"|"-h"|"--help")
            echo "期货数据系统部署脚本"
            echo ""
            echo "使用方法: $0 [command] [options]"
            echo ""
            echo "主要命令:"
            echo "  deploy [branch]  - 拉取代码并部署更新 (默认main分支)"
            echo "  start           - 启动所有服务并等待健康检查"
            echo "  stop            - 停止所有服务"
            echo "  restart         - 重启所有服务"
            echo "  status          - 查看服务状态"
            echo "  logs [service]  - 查看日志 (可指定服务名)"
            echo "  add-service <name> <port> - 添加新服务指导"
            echo ""
            echo "常用场景:"
            echo "  修改代码后部署: $0 deploy"
            echo "  首次启动系统: $0 start"
            echo "  查看服务状态: $0 status"
            echo "  查看日志: $0 logs"
            echo "  重启服务: $0 restart"
            echo ""
            echo "注意事项:"
            echo "  爬虫功能已迁移到 spiderx 项目，请在本地运行"
            ;;
        *)
            print_error "未知命令: $1"
            print_info "使用 '$0 help' 查看帮助"
            exit 1
            ;;
    esac
}

main "$@"
