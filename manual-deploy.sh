#!/bin/bash

# 手动部署脚本 - 从本地推送并部署到服务器
# 使用方法: ./manual-deploy.sh [server_ip] [branch]

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

# 默认配置
DEFAULT_SERVER_IP=""
DEFAULT_BRANCH="main"
DEFAULT_USER="root"
DEFAULT_PROJECT_PATH="/opt/futures-system"

# 解析参数
SERVER_IP=${1:-$DEFAULT_SERVER_IP}
BRANCH=${2:-$DEFAULT_BRANCH}
SERVER_USER=${3:-$DEFAULT_USER}
PROJECT_PATH=${4:-$DEFAULT_PROJECT_PATH}

# 检查参数
if [ -z "$SERVER_IP" ]; then
    print_error "请提供服务器IP地址"
    echo "使用方法: $0 <server_ip> [branch] [user] [project_path]"
    echo "示例: $0 192.168.1.100 main root /opt/futures-system"
    exit 1
fi

print_info "部署配置:"
print_info "  服务器: $SERVER_USER@$SERVER_IP"
print_info "  分支: $BRANCH"
print_info "  项目路径: $PROJECT_PATH"
echo

# 检查本地Git状态
print_info "检查本地Git状态..."

if [ ! -d ".git" ]; then
    print_error "当前目录不是Git仓库"
    exit 1
fi

# 检查是否有未提交的更改
if ! git diff-index --quiet HEAD --; then
    print_warning "检测到未提交的更改:"
    git status --porcelain
    echo
    read -p "是否先提交这些更改？(Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        read -p "请输入提交信息: " commit_message
        if [ -n "$commit_message" ]; then
            git add .
            git commit -m "$commit_message"
            print_success "更改已提交"
        else
            print_error "提交信息不能为空"
            exit 1
        fi
    fi
fi

# 推送到远程仓库
print_info "推送到远程仓库..."
git push origin $BRANCH

COMMIT_ID=$(git rev-parse HEAD)
COMMIT_MESSAGE=$(git log -1 --pretty=%B)
print_success "推送完成，提交ID: ${COMMIT_ID:0:8}"

# 连接服务器并部署
print_info "连接服务器并开始部署..."

# 生成部署脚本
DEPLOY_SCRIPT=$(cat << 'EOF'
#!/bin/bash
set -e

PROJECT_PATH="$1"
BRANCH="$2"
COMMIT_ID="$3"

echo "开始服务器端部署..."
echo "项目路径: $PROJECT_PATH"
echo "目标分支: $BRANCH"
echo "提交ID: $COMMIT_ID"

# 检查项目目录
if [ ! -d "$PROJECT_PATH" ]; then
    echo "错误: 项目目录不存在: $PROJECT_PATH"
    exit 1
fi

cd "$PROJECT_PATH"

# 检查必要文件
if [ ! -f "update.sh" ]; then
    echo "错误: 更新脚本不存在: $PROJECT_PATH/update.sh"
    exit 1
fi

# 给脚本添加执行权限
chmod +x update.sh deploy.sh 2>/dev/null || true

# 执行更新
echo "执行更新脚本..."
./update.sh "$BRANCH"

echo "部署完成！"
EOF
)

# 执行远程部署
ssh -o StrictHostKeyChecking=no "$SERVER_USER@$SERVER_IP" "bash -s" -- "$PROJECT_PATH" "$BRANCH" "$COMMIT_ID" <<< "$DEPLOY_SCRIPT"

if [ $? -eq 0 ]; then
    print_success "部署成功完成！"
    
    # 显示访问信息
    echo
    print_info "访问地址:"
    print_info "  前端: http://$SERVER_IP/"
    print_info "  API: http://$SERVER_IP/api-a/"
    print_info "  健康检查: http://$SERVER_IP/health"
    
    # 测试连接
    print_info "测试服务连接..."
    if curl -f -s "http://$SERVER_IP/health" > /dev/null; then
        print_success "服务运行正常"
    else
        print_warning "服务可能需要更多时间启动"
    fi
    
else
    print_error "部署失败"
    exit 1
fi
