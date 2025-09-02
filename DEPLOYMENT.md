# 期货数据系统 Docker 部署指南

## 系统架构

```
外网用户 → 80/443 → Nginx(容器) → 前端静态文件(workfront) + 后端API代理(/api-a/* → automysqlback:7001)
```

## 部署准备

### 1. 服务器要求

- **操作系统**: CentOS 7+, Ubuntu 18.04+, 或其他支持Docker的Linux发行版
- **内存**: 最低2GB，推荐4GB+
- **磁盘**: 最低20GB可用空间
- **网络**: 需要访问外网（用于拉取Docker镜像和Python包）

### 2. 安装Docker和Docker Compose

#### CentOS/RHEL
```bash
# 安装Docker
sudo yum install -y yum-utils
sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
sudo yum install -y docker-ce docker-ce-cli containerd.io
sudo systemctl start docker
sudo systemctl enable docker

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

#### Ubuntu/Debian
```bash
# 安装Docker
sudo apt-get update
sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt-get update
sudo apt-get install -y docker-ce docker-ce-cli containerd.io

# 安装Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 启动Docker服务
sudo systemctl start docker
sudo systemctl enable docker
```

### 3. 配置防火墙

```bash
# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload

# Ubuntu/Debian (ufw)
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw reload
```

## 部署步骤

### 1. 上传项目文件

将整个项目目录上传到服务器，建议路径：`/opt/futures-system/`

```bash
# 创建目录
sudo mkdir -p /opt/futures-system
sudo chown $USER:$USER /opt/futures-system

# 上传文件（使用scp、rsync或其他方式）
# 确保以下文件和目录都已上传：
# - docker-compose.yml
# - deploy.sh
# - env.production
# - nginx/
# - workfront/
# - automysqlback/
```

### 2. 配置环境变量

```bash
cd /opt/futures-system

# 复制环境配置文件
cp env.production .env

# 编辑环境配置（根据实际情况修改）
vim .env
```

### 3. 部署服务

```bash
# 给部署脚本添加执行权限
chmod +x deploy.sh

# 启动服务
./deploy.sh start
```

### 4. 验证部署

```bash
# 检查服务状态
./deploy.sh status

# 查看日志
./deploy.sh logs

# 测试访问
curl http://localhost/health
curl http://localhost/api-a/settings
```

## 常用命令

```bash
# 启动服务
./deploy.sh start

# 停止服务
./deploy.sh stop

# 重启服务
./deploy.sh restart

# 查看状态
./deploy.sh status

# 查看所有日志
./deploy.sh logs

# 查看特定服务日志
./deploy.sh logs nginx
./deploy.sh logs automysqlback
./deploy.sh logs workfront

# 更新服务
./deploy.sh update

# 备份数据
./deploy.sh backup

# 清理资源
./deploy.sh cleanup
```

## 目录结构

```
/opt/futures-system/
├── docker-compose.yml          # Docker编排文件
├── deploy.sh                   # 部署脚本
├── .env                       # 环境配置文件
├── env.production             # 生产环境配置模板
├── .dockerignore              # Docker忽略文件
├── nginx/
│   ├── nginx.conf            # Nginx配置文件
│   └── logs/                 # Nginx日志目录
├── workfront/                # 前端项目
│   ├── Dockerfile
│   ├── nginx.conf
│   └── ...
├── automysqlback/            # 后端项目
│   ├── Dockerfile
│   ├── app.py
│   └── ...
└── logs/                     # 应用日志目录
    └── backend/
```

## 网络访问

- **前端访问**: `http://your-server-ip/`
- **API访问**: `http://your-server-ip/api-a/`
- **健康检查**: `http://your-server-ip/health`

## SSL/HTTPS配置（可选）

### 1. 获取SSL证书

```bash
# 使用Let's Encrypt（推荐）
sudo apt-get install -y certbot
sudo certbot certonly --standalone -d your-domain.com

# 证书文件位置
# 证书: /etc/letsencrypt/live/your-domain.com/fullchain.pem
# 私钥: /etc/letsencrypt/live/your-domain.com/privkey.pem
```

### 2. 配置SSL

1. 将证书文件复制到项目目录：
```bash
mkdir -p nginx/ssl
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem
sudo chown $USER:$USER nginx/ssl/*
```

2. 修改 `nginx/nginx.conf`，取消HTTPS配置的注释

3. 重启服务：
```bash
./deploy.sh restart
```

## 故障排除

### 1. 容器无法启动

```bash
# 查看容器日志
docker-compose logs [service-name]

# 查看容器状态
docker-compose ps

# 重新构建镜像
docker-compose build --no-cache [service-name]
```

### 2. 网络连接问题

```bash
# 检查端口占用
netstat -tlnp | grep :80
netstat -tlnp | grep :443

# 检查防火墙状态
sudo firewall-cmd --list-all  # CentOS
sudo ufw status              # Ubuntu
```

### 3. 数据库连接问题

```bash
# 检查数据库连接
docker-compose exec automysqlback python -c "
import pymysql
try:
    conn = pymysql.connect(host='your-db-host', user='your-user', password='your-password', database='futures')
    print('数据库连接成功')
    conn.close()
except Exception as e:
    print(f'数据库连接失败: {e}')
"
```

### 4. 性能优化

```bash
# 清理Docker资源
docker system prune -f

# 查看资源使用情况
docker stats

# 调整容器资源限制（在docker-compose.yml中）
```

## 监控和维护

### 1. 日志轮转

```bash
# 配置logrotate
sudo vim /etc/logrotate.d/futures-system
```

### 2. 定期备份

```bash
# 设置定时任务
crontab -e

# 每天凌晨2点备份
0 2 * * * /opt/futures-system/deploy.sh backup
```

### 3. 系统监控

```bash
# 安装监控工具
sudo apt-get install -y htop iotop nethogs

# 监控容器状态
watch docker-compose ps
```

## 更新部署

```bash
# 拉取最新代码（如果使用Git）
git pull

# 更新服务
./deploy.sh update
```
