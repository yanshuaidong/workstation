# 快速部署指南

## 阿里云服务器部署步骤

### 1. 准备服务器环境

```bash
# 更新系统
sudo yum update -y

# 安装Docker
sudo yum install -y yum-utils device-mapper-persistent-data lvm2
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io

# 启动Docker
sudo systemctl start docker
sudo systemctl enable docker

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

### 2. 上传项目文件

```bash
# 在服务器上创建目录
sudo mkdir -p /opt/futures-system
sudo chown $USER:$USER /opt/futures-system

# 将项目文件上传到服务器（在本地执行）
# 方法1: 使用scp
scp -r workstation/* user@your-server-ip:/opt/futures-system/

# 方法2: 使用rsync
rsync -avz --progress workstation/ user@your-server-ip:/opt/futures-system/

# 方法3: 使用Git（推荐）
# 在服务器上执行
cd /opt/futures-system
git clone your-repository-url .
```

### 3. 配置环境

```bash
# 进入项目目录
cd /opt/futures-system

# 复制环境配置
cp env.production .env

# 编辑配置文件（根据实际情况修改数据库信息）
vim .env

# 给部署脚本添加执行权限
chmod +x deploy.sh
```

### 4. 配置防火墙

```bash
# 开放HTTP和HTTPS端口
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload

# 查看开放的端口
sudo firewall-cmd --list-ports
```

### 5. 部署服务

```bash
# 启动服务
./deploy.sh start

# 检查状态
./deploy.sh status

# 查看日志
./deploy.sh logs
```

### 6. 验证部署

```bash
# 测试健康检查
curl http://localhost/health

# 测试前端
curl -I http://localhost/

# 测试后端API
curl http://localhost/api-a/settings
```

## 一键部署脚本

创建 `quick-setup.sh` 文件：

```bash
#!/bin/bash
set -e

echo "开始快速部署期货数据系统..."

# 检查是否为root用户
if [ "$EUID" -eq 0 ]; then
    echo "请不要使用root用户运行此脚本"
    exit 1
fi

# 安装Docker（如果未安装）
if ! command -v docker &> /dev/null; then
    echo "安装Docker..."
    sudo yum update -y
    sudo yum install -y yum-utils device-mapper-persistent-data lvm2
    sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    sudo yum install -y docker-ce docker-ce-cli containerd.io
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -aG docker $USER
    echo "Docker安装完成，请重新登录后继续"
    exit 0
fi

# 安装Docker Compose（如果未安装）
if ! command -v docker-compose &> /dev/null; then
    echo "安装Docker Compose..."
    sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
fi

# 配置防火墙
echo "配置防火墙..."
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload

# 创建环境配置
if [ ! -f ".env" ]; then
    cp env.production .env
    echo "已创建.env文件，请根据需要修改配置"
fi

# 部署服务
echo "部署服务..."
chmod +x deploy.sh
./deploy.sh start

echo "部署完成！"
echo "访问地址: http://$(curl -s ifconfig.me)/"
```

## 常见问题解决

### 问题1: Docker权限问题
```bash
# 将用户添加到docker组
sudo usermod -aG docker $USER
# 重新登录或执行
newgrp docker
```

### 问题2: 端口被占用
```bash
# 查看端口占用
sudo netstat -tlnp | grep :80
# 停止占用端口的服务
sudo systemctl stop httpd  # 或nginx
```

### 问题3: 内存不足
```bash
# 查看内存使用
free -h
# 创建swap文件
sudo dd if=/dev/zero of=/swapfile bs=1024 count=2048000
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### 问题4: 网络连接问题
```bash
# 检查网络连接
ping google.com
# 检查DNS
nslookup google.com
```

## 生产环境优化

### 1. 性能优化
```bash
# 调整Docker配置
sudo vim /etc/docker/daemon.json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}

# 重启Docker
sudo systemctl restart docker
```

### 2. 安全加固
```bash
# 禁用不必要的服务
sudo systemctl disable postfix
sudo systemctl disable cups

# 配置SSH安全
sudo vim /etc/ssh/sshd_config
# 修改默认端口，禁用root登录等
```

### 3. 监控配置
```bash
# 安装监控工具
sudo yum install -y htop iotop nethogs

# 设置日志轮转
sudo vim /etc/logrotate.d/futures-system
```
