#!/bin/bash

# Portainer初始化脚本
# 创建管理员密码文件

set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}[INFO]${NC} 初始化Portainer监控面板..."

# 创建portainer数据目录
mkdir -p ./portainer_data

# 设置默认管理员密码 (admin/admin123456)
# 密码需要使用bcrypt加密
DEFAULT_PASSWORD_HASH='$2y$10$YzZzZzZzZzZzZzZzZzZzZe.aBCDEFGHIJKLMNOPQRSTUVWXYZ1234'

# 如果密码文件不存在，创建默认密码
if [ ! -f "./portainer_data/admin_password" ]; then
    echo "admin123456" > ./portainer_data/admin_password
    chmod 600 ./portainer_data/admin_password
    echo -e "${GREEN}[SUCCESS]${NC} Portainer管理员密码已设置"
    echo -e "${YELLOW}[INFO]${NC} 默认登录信息:"
    echo -e "  用户名: admin"
    echo -e "  密码: admin123456"
    echo -e "${YELLOW}[WARNING]${NC} 首次登录后请立即修改密码！"
else
    echo -e "${GREEN}[INFO]${NC} Portainer密码文件已存在"
fi

echo -e "${GREEN}[SUCCESS]${NC} Portainer初始化完成" 