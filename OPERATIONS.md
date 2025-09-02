# 运维操作指南

这是期货数据系统的日常运维操作文档，包含开发、部署、维护的所有常用操作。

## 快速开始

### 首次部署

1. **准备服务器环境**
```bash
# 安装Docker和Docker Compose
sudo yum install -y docker docker-compose
sudo systemctl start docker
sudo systemctl enable docker

# 克隆项目到服务器
cd /opt
git clone your-repository-url futures-system
cd futures-system
```

2. **配置环境**
```bash
# 复制环境配置
cp env.production .env

# 根据需要修改数据库配置
vim .env
```

3. **首次部署**
```bash
chmod +x deploy.sh
./deploy.sh deploy
```

## 日常操作

### 情况1: 修改了前端或后端代码

当你修改了前端(`workfront/`)或后端(`workback/`, `automysqlback/`)代码后：

```bash
# 1. 提交代码到Git仓库
git add .
git commit -m "修改了某某功能"
git push origin main

# 2. 在服务器上部署更新
cd /opt/futures-system
./deploy.sh deploy

# 3. 检查服务状态
./deploy.sh status
```

**一键完成**: `./deploy.sh deploy` 会自动完成拉代码→构建→重启的全过程。

### 情况2: 添加新的后端服务

假设你要添加一个新服务在7002端口：

1. **获取配置指导**
```bash
./deploy.sh add-service newapi 7002
```

2. **修改docker-compose.yml**
```yaml
services:
  # 添加新服务
  newapi:
    build:
      context: ./newapi
      dockerfile: Dockerfile
    container_name: futures-newapi
    expose:
      - "7002"
    environment:
      - DB_HOST=${DB_HOST}
      - DB_PASSWORD=${DB_PASSWORD}
    networks:
      - futures-network
```

3. **修改nginx/nginx.conf**
```nginx
# 添加upstream
upstream newapi_backend {
    server newapi:7002;
    keepalive 32;
}

# 添加location
location /api-newapi/ {
    rewrite ^/api-newapi/(.*)$ /api/$1 break;
    proxy_pass http://newapi_backend;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
}
```

4. **部署新服务**
```bash
./deploy.sh deploy
```

5. **访问新服务**
- API地址: `http://localhost/api-newapi/`

## 常用命令

### 部署相关
```bash
# 拉代码并部署更新
./deploy.sh deploy

# 指定分支部署
./deploy.sh deploy develop

# 启动所有服务
./deploy.sh start

# 停止所有服务
./deploy.sh stop

# 重启所有服务
./deploy.sh restart
```

### 监控相关
```bash
# 查看服务状态
./deploy.sh status

# 查看所有日志
./deploy.sh logs

# 查看特定服务日志
./deploy.sh logs nginx
./deploy.sh logs automysqlback
./deploy.sh logs workfront

# 实时查看日志
./deploy.sh logs -f
```

### Docker操作
```bash
# 查看容器状态
docker-compose ps

# 进入容器
docker-compose exec automysqlback bash
docker-compose exec workfront sh

# 查看容器资源使用
docker stats

# 清理未使用的镜像
docker system prune -f
```

## 故障排除

### 1. 服务无法启动

```bash
# 查看详细日志
./deploy.sh logs

# 检查配置文件
cat .env
docker-compose config

# 重新构建镜像
docker-compose build --no-cache
./deploy.sh restart
```

### 2. 前端页面无法访问

```bash
# 检查nginx状态
curl http://localhost/health
./deploy.sh logs nginx

# 检查前端服务
./deploy.sh logs workfront
```

### 3. API接口报错

```bash
# 检查后端日志
./deploy.sh logs automysqlback

# 检查数据库连接
docker-compose exec automysqlback python -c "
import pymysql
conn = pymysql.connect(host='rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com', 
                      user='ysd', password='Yan1234567', database='futures')
print('数据库连接正常')
"
```

### 4. 端口冲突

```bash
# 查看端口占用
netstat -tlnp | grep :80
netstat -tlnp | grep :443

# 停止占用端口的服务
sudo systemctl stop nginx  # 如果有系统nginx
sudo systemctl stop httpd  # 如果有apache
```

## 开发流程

### 本地开发

1. **前端开发**
```bash
cd workfront
npm install
npm run serve  # 开发模式
npm run build  # 构建生产版本
```

2. **后端开发**
```bash
cd workback
npm install
npm start      # 启动Node.js服务

# 或Python服务
cd workbackpy
pip install -r requirements.txt
python app.py
```

### 上线流程

1. **本地测试** → 2. **提交代码** → 3. **服务器部署**

```bash
# 本地测试完成后
git add .
git commit -m "功能描述"
git push origin main

# 服务器部署
ssh your-server
cd /opt/futures-system
./deploy.sh deploy
```

## 环境配置

### 生产环境变量

编辑 `.env` 文件：

```bash
# 数据库配置
DB_HOST=rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com
DB_PORT=3306
DB_USER=ysd
DB_PASSWORD=Yan1234567
DB_DATABASE=futures

# 服务端口
NGINX_HTTP_PORT=80
NGINX_HTTPS_PORT=443
BACKEND_PORT=7001

# 日志级别
LOG_LEVEL=INFO
```

### 防火墙配置

```bash
# 开放必要端口
sudo firewall-cmd --permanent --add-port=80/tcp
sudo firewall-cmd --permanent --add-port=443/tcp
sudo firewall-cmd --reload
```

## 备份与恢复

### 代码备份
```bash
# Git自动备份，每次部署前会显示版本信息
./deploy.sh deploy  # 会显示当前版本和更新内容
```

### 数据库备份
```bash
# 备份数据库（如果需要）
mysqldump -h rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com \
          -u ysd -p futures > backup_$(date +%Y%m%d).sql
```

### 配置文件备份
```bash
# 备份重要配置
cp .env .env.backup.$(date +%Y%m%d)
cp nginx/nginx.conf nginx/nginx.conf.backup.$(date +%Y%m%d)
```

## 性能监控

### 系统监控
```bash
# 查看系统资源
htop
df -h
free -h

# 查看Docker资源使用
docker stats

# 查看日志大小
du -sh logs/
du -sh nginx/logs/
```

### 服务监控
```bash
# 定期检查服务状态
./deploy.sh status

# 设置定时检查（可选）
# 在crontab中添加：
# */5 * * * * cd /opt/futures-system && ./deploy.sh status > /dev/null || echo "服务异常" | mail -s "系统告警" your-email
```

## 常见问题

**Q: 部署后前端页面显示404**
A: 检查nginx配置和workfront服务状态，运行 `./deploy.sh logs workfront`

**Q: API接口返回502错误**
A: 后端服务可能未启动，检查 `./deploy.sh logs automysqlback`

**Q: 数据库连接失败**
A: 检查.env文件中的数据库配置，确认网络连通性

**Q: 如何回滚到上一个版本**
A: `git log --oneline` 查看版本，然后 `git reset --hard <commit-id>` 后重新部署

---

**记住**: 99%的操作就是 `./deploy.sh deploy`，这一个命令解决大部分部署需求！ 