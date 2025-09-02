#!/bin/bash

# 服务器端更新脚本
# 使用方法: ./update.sh [branch_name]

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

# 获取分支名称，默认为main
BRANCH=${1:-main}
BACKUP_DIR="backup/$(date +%Y%m%d_%H%M%S)"

print_info "开始更新部署，目标分支: $BRANCH"

# 检查是否在正确的目录
if [ ! -f "docker-compose.yml" ] || [ ! -f "deploy.sh" ]; then
    print_error "请在项目根目录执行此脚本"
    exit 1
fi

# 检查Git仓库状态
if [ ! -d ".git" ]; then
    print_error "当前目录不是Git仓库"
    exit 1
fi

# 检查是否有未提交的更改
if ! git diff-index --quiet HEAD --; then
    print_warning "检测到未提交的更改，将被重置"
    read -p "是否继续？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_info "更新已取消"
        exit 0
    fi
fi

# 创建备份
print_info "创建备份到 $BACKUP_DIR..."
./deploy.sh backup

# 停止服务
print_info "停止当前服务..."
./deploy.sh stop

# 保存当前提交ID
CURRENT_COMMIT=$(git rev-parse HEAD)
print_info "当前版本: $CURRENT_COMMIT"

# 重置本地更改（如果有）
print_info "重置本地更改..."
git reset --hard HEAD
git clean -fd

# 拉取最新代码
print_info "拉取最新代码..."
git fetch origin
git checkout $BRANCH
git reset --hard origin/$BRANCH

NEW_COMMIT=$(git rev-parse HEAD)
print_info "新版本: $NEW_COMMIT"

# 检查是否有更新
if [ "$CURRENT_COMMIT" = "$NEW_COMMIT" ]; then
    print_warning "代码没有更新，重新启动服务..."
    ./deploy.sh start
    exit 0
fi

# 显示更新日志
print_info "更新日志:"
git log --oneline $CURRENT_COMMIT..$NEW_COMMIT

# 检查是否需要重新构建镜像
NEED_REBUILD=false

# 检查关键文件是否有变化
if git diff --name-only $CURRENT_COMMIT $NEW_COMMIT | grep -E "(Dockerfile|requirements\.txt|package\.json|package-lock\.json)" > /dev/null; then
    NEED_REBUILD=true
    print_warning "检测到依赖文件变化，需要重新构建镜像"
fi

# 更新环境配置（如果有新的配置文件）
if [ -f "env.production" ]; then
    if [ ! -f ".env" ]; then
        print_info "创建环境配置文件..."
        cp env.production .env
        print_warning "请检查并更新 .env 文件中的配置"
    else
        # 检查是否有新的配置项
        if ! diff -q env.production .env > /dev/null 2>&1; then
            print_warning "环境配置文件有更新，请检查 .env 文件"
            print_info "新增配置项："
            diff env.production .env || true
        fi
    fi
fi

# 重新部署
if [ "$NEED_REBUILD" = true ]; then
    print_info "重新构建并启动服务..."
    docker-compose build --no-cache
    docker-compose up -d
else
    print_info "启动服务..."
    ./deploy.sh start
fi

# 等待服务启动
print_info "等待服务启动..."
sleep 15

# 检查服务状态
print_info "检查服务状态..."
if ./deploy.sh status; then
    print_success "更新部署成功！"
    print_info "新版本已部署: $NEW_COMMIT"
    
    # 清理旧的备份（保留最近5个）
    print_info "清理旧备份..."
    ls -t backup/ | tail -n +6 | xargs -r -I {} rm -rf backup/{}
    
else
    print_error "服务启动失败，尝试回滚..."
    
    # 回滚到之前的版本
    git reset --hard $CURRENT_COMMIT
    ./deploy.sh restart
    
    print_error "已回滚到之前版本: $CURRENT_COMMIT"
    exit 1
fi

print_success "更新完成！"
