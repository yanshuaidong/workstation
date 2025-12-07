#!/bin/bash

# ============================================================
# Reuters 路透社新闻采集服务启动脚本
# 功能：启动 Reuters 新闻采集和处理服务
# 端口：1125
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

# 检查端口是否被占用
check_port() {
    if lsof -Pi :1125 -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0  # 端口被占用
    else
        return 1  # 端口空闲
    fi
}

# 检查Python环境
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        log_error "未找到Python环境，请先安装Python3"
        exit 1
    fi
    log_info "使用Python: $PYTHON_CMD ($($PYTHON_CMD --version))"
}

# 安装依赖
install_dependencies() {
    log_info "检查并安装依赖..."
    
    # 检查requirements.txt是否存在
    if [ -f "requirements.txt" ]; then
        $PYTHON_CMD -m pip install -r requirements.txt -q
        log_info "依赖安装完成"
    else
        log_warn "未找到requirements.txt，跳过依赖安装"
    fi
}

# 初始化数据库
init_database() {
    log_info "初始化数据库..."
    
    DB_INIT_SCRIPT="../db/init_db.py"
    if [ -f "$DB_INIT_SCRIPT" ]; then
        $PYTHON_CMD "$DB_INIT_SCRIPT"
        log_info "数据库初始化完成"
    else
        log_warn "未找到数据库初始化脚本: $DB_INIT_SCRIPT"
    fi
}

# 启动服务
start_service() {
    log_header "🚀 启动 Reuters 新闻采集服务"
    
    # 检查端口
    if check_port; then
        log_warn "端口 1125 已被占用，可能服务已在运行"
        echo -e "${YELLOW}如需重启，请先执行: ./stop_scheduler.sh${NC}"
        exit 1
    fi
    
    # 检查Python环境
    check_python
    
    # 安装依赖
    install_dependencies
    
    # 初始化数据库
    init_database
    
    # 启动服务（后台运行）
    log_info "启动Reuters新闻处理服务..."
    nohup $PYTHON_CMD main.py > reuters_service.log 2>&1 &
    
    # 获取PID并保存
    PID=$!
    echo $PID > reuters_service.pid
    
    # 等待服务启动
    sleep 2
    
    # 检查服务是否成功启动
    if check_port; then
        log_info "✅ Reuters新闻采集服务启动成功!"
        echo ""
        echo -e "${GREEN}服务信息:${NC}"
        echo -e "  📍 端口: 1125"
        echo -e "  📝 PID: $PID"
        echo -e "  📄 日志: $SCRIPT_DIR/reuters_service.log"
        echo ""
        echo -e "${GREEN}API接口:${NC}"
        echo -e "  🔗 接收数据: http://localhost:1125/api/capture"
        echo -e "  💚 健康检查: http://localhost:1125/api/health"
        echo -e "  📊 统计信息: http://localhost:1125/api/stats"
        echo -e "  🧪 测试处理: http://localhost:1125/api/process_test"
        echo ""
        echo -e "${GREEN}定时任务:${NC}"
        echo -e "  ⏰ 每天 5点、11点、17点、23点 执行（与彭博社错开1小时）"
        echo ""
        echo -e "${YELLOW}停止服务: ./stop_scheduler.sh${NC}"
    else
        log_error "服务启动失败，请检查日志: reuters_service.log"
        cat reuters_service.log | tail -20
        exit 1
    fi
}

# 主函数
main() {
    start_service
}

main "$@"

