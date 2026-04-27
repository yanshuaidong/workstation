#!/bin/bash

# 腾讯云非 Docker 部署脚本
# 使用方法: bash deploy-tencent.sh [deploy|start|stop|restart|status|logs|install-service|install-nginx|build]

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

PROJECT_DIR=${PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)}
FRONTEND_DIR="${PROJECT_DIR}/workfront"
BACKEND_DIR="${PROJECT_DIR}/automysqlback"
VENV_DIR="${BACKEND_DIR}/.venv"
SERVICE_NAME="workstation-backend"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
NGINX_SOURCE="${PROJECT_DIR}/nginx/tencent-nginx.conf"
NGINX_TARGET="/etc/nginx/nginx.conf"
PIP_INDEX_URL=${PIP_INDEX_URL:-https://pypi.tuna.tsinghua.edu.cn/simple}

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

require_root() {
    if [ "$(id -u)" -ne 0 ]; then
        print_error "该命令需要 root 权限，请使用 root 用户或 sudo 执行"
        exit 1
    fi
}

require_command() {
    if ! command -v "$1" >/dev/null 2>&1; then
        print_error "缺少命令: $1"
        exit 1
    fi
}

ensure_project_root() {
    if [ ! -f "${FRONTEND_DIR}/package.json" ] || [ ! -f "${BACKEND_DIR}/start.py" ]; then
        print_error "项目目录不正确: ${PROJECT_DIR}"
        print_info "请在项目根目录执行，或设置 PROJECT_DIR=/root/workstation"
        exit 1
    fi
}

ensure_env() {
    if [ -f "${PROJECT_DIR}/.env" ]; then
        print_info "使用现有环境配置: ${PROJECT_DIR}/.env"
        return
    fi

    if [ -f "${PROJECT_DIR}/env.production" ]; then
        print_warning "未找到 .env，正在从 env.production 复制"
        cp "${PROJECT_DIR}/env.production" "${PROJECT_DIR}/.env"
        print_warning "请确认 .env 中的数据库和 OSS 密钥已配置正确"
        return
    fi

    print_error "未找到 .env 或 env.production"
    exit 1
}

check_dependencies() {
    require_command python3
    require_command npm
    require_command nginx
    require_command systemctl
    require_command curl
}

build_frontend() {
    print_info "构建前端..."
    cd "${FRONTEND_DIR}"

    if [ -f "package-lock.json" ]; then
        npm ci
    else
        npm install
    fi

    npm run build

    if [ ! -f "${FRONTEND_DIR}/dist/index.html" ]; then
        print_error "前端构建失败，未找到 dist/index.html"
        exit 1
    fi

    print_success "前端构建完成: ${FRONTEND_DIR}/dist"
}

setup_backend() {
    print_info "准备后端 Python 环境..."
    cd "${BACKEND_DIR}"

    if [ ! -d "${VENV_DIR}" ]; then
        python3 -m venv "${VENV_DIR}"
    fi

    "${VENV_DIR}/bin/python" -m pip install --upgrade pip
    PIP_INDEX_URL="${PIP_INDEX_URL}" "${VENV_DIR}/bin/pip" install -r requirements.txt

    print_success "后端依赖安装完成"
}

install_service() {
    require_root
    ensure_project_root
    ensure_env
    setup_backend

    print_info "写入 systemd 服务: ${SERVICE_FILE}"
    cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=Workstation Futures Backend API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=${BACKEND_DIR}
Environment=PYTHONUNBUFFERED=1
Environment=MALLOC_ARENA_MAX=2
Environment=PYTHONPATH=${BACKEND_DIR}
EnvironmentFile=-${PROJECT_DIR}/env.production
EnvironmentFile=-${PROJECT_DIR}/.env
ExecStart=${VENV_DIR}/bin/python start.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable "${SERVICE_NAME}"
    print_success "systemd 服务安装完成"
}

install_nginx() {
    require_root
    ensure_project_root

    if [ ! -f "${NGINX_SOURCE}" ]; then
        print_error "未找到 Nginx 配置模板: ${NGINX_SOURCE}"
        exit 1
    fi

    local backup_file="${NGINX_TARGET}.bak.$(date +%Y%m%d%H%M%S)"
    print_info "备份当前 Nginx 配置: ${backup_file}"
    cp "${NGINX_TARGET}" "${backup_file}"

    print_info "安装腾讯云 Nginx 配置..."
    if [ "${PROJECT_DIR}" = "/root/workstation" ]; then
        cp "${NGINX_SOURCE}" "${NGINX_TARGET}"
    else
        sed "s#/root/workstation#${PROJECT_DIR}#g" "${NGINX_SOURCE}" > "${NGINX_TARGET}"
    fi

    if nginx -t; then
        systemctl reload nginx
        print_success "Nginx 配置已安装并重载"
    else
        print_error "Nginx 配置校验失败，正在恢复备份"
        cp "${backup_file}" "${NGINX_TARGET}"
        nginx -t || true
        exit 1
    fi
}

start_services() {
    require_root
    systemctl start "${SERVICE_NAME}"
    systemctl reload nginx
    print_success "服务已启动"
}

stop_services() {
    require_root
    systemctl stop "${SERVICE_NAME}"
    print_success "后端服务已停止"
}

restart_services() {
    require_root
    systemctl restart "${SERVICE_NAME}"
    systemctl reload nginx
    print_success "服务已重启"
}

show_status() {
    print_info "后端服务状态:"
    systemctl status "${SERVICE_NAME}" --no-pager || true

    echo ""
    print_info "Nginx 配置检查:"
    nginx -t || true

    echo ""
    print_info "健康检查:"
    if curl -fsS http://127.0.0.1/ >/dev/null 2>&1; then
        print_success "前端访问正常"
    else
        print_warning "前端访问异常"
    fi

    if curl -fsS http://127.0.0.1/api-a/settings >/dev/null 2>&1; then
        print_success "后端 API 访问正常"
    else
        print_warning "后端 API 访问异常"
    fi
}

show_logs() {
    journalctl -u "${SERVICE_NAME}" -f --no-pager
}

deploy() {
    require_root
    ensure_project_root
    check_dependencies
    ensure_env
    build_frontend
    install_service
    install_nginx
    restart_services
    sleep 3
    show_status
    print_success "腾讯云非 Docker 部署完成"
}

usage() {
    echo "腾讯云非 Docker 部署脚本"
    echo ""
    echo "使用方法: bash $0 [command]"
    echo ""
    echo "命令:"
    echo "  deploy          构建前端、安装后端服务、安装 Nginx 配置并启动"
    echo "  build           仅构建前端并安装后端依赖"
    echo "  install-service 安装/更新 systemd 后端服务"
    echo "  install-nginx   安装/更新腾讯云 Nginx 配置"
    echo "  start           启动后端服务并重载 Nginx"
    echo "  stop            停止后端服务"
    echo "  restart         重启后端服务并重载 Nginx"
    echo "  status          查看服务状态和健康检查"
    echo "  logs            查看后端服务日志"
    echo ""
    echo "可选环境变量:"
    echo "  PROJECT_DIR     项目目录，默认脚本所在目录"
    echo "  PIP_INDEX_URL   pip 源，默认清华源"
}

main() {
    case "${1:-help}" in
        deploy)
            deploy
            ;;
        build)
            ensure_project_root
            check_dependencies
            ensure_env
            build_frontend
            setup_backend
            ;;
        install-service)
            check_dependencies
            install_service
            ;;
        install-nginx)
            check_dependencies
            install_nginx
            ;;
        start)
            start_services
            ;;
        stop)
            stop_services
            ;;
        restart)
            restart_services
            ;;
        status)
            show_status
            ;;
        logs)
            show_logs
            ;;
        help|-h|--help)
            usage
            ;;
        *)
            print_error "未知命令: $1"
            usage
            exit 1
            ;;
    esac
}

main "$@"
