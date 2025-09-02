# CI/CD 自动化部署指南

基于你的GitHub仓库 `github.com/yanshuaidong/workstation`，我为你准备了多种部署方案，从简单到复杂，你可以根据需要选择。

## 🚀 部署方案总览

| 方案 | 复杂度 | 自动化程度 | 适用场景 |
|------|--------|------------|----------|
| 1. 手动部署 | ⭐ | 手动 | 开发测试、紧急发布 |
| 2. 服务器端更新 | ⭐⭐ | 半自动 | 小团队、简单项目 |
| 3. Webhook自动部署 | ⭐⭐⭐ | 自动 | 中小型项目 |
| 4. GitHub Actions | ⭐⭐⭐⭐ | 全自动 | 企业级、大型项目 |

## 🎯 推荐方案：Webhook自动部署

**最简单可靠的方法**，推送代码后自动部署，无需复杂配置。

### 设置步骤：

#### 1. 服务器端设置

```bash
# 1. 确保项目已部署并运行
cd /opt/futures-system
./deploy.sh status

# 2. 启动Webhook服务
chmod +x webhook-service.sh
./webhook-service.sh start

# 3. 开放端口（如果有防火墙）
sudo firewall-cmd --permanent --add-port=9000/tcp
sudo firewall-cmd --reload
```

#### 2. GitHub仓库设置

1. 进入你的GitHub仓库：`https://github.com/yanshuaidong/workstation`
2. 点击 `Settings` → `Webhooks` → `Add webhook`
3. 填写配置：
   - **Payload URL**: `http://your-server-ip:9000/webhook`
   - **Content type**: `application/json`
   - **Secret**: `futures-webhook-secret-2024`（可自定义）
   - **Events**: 选择 `Just the push event`
4. 点击 `Add webhook`

#### 3. 测试自动部署

```bash
# 在本地修改代码后
git add .
git commit -m "测试自动部署"
git push origin main

# 查看服务器日志
ssh your-server-ip
cd /opt/futures-system
./webhook-service.sh logs -f
```

## 📋 所有部署方案详解

### 方案1: 手动部署 (最简单)

适合：开发测试、紧急修复

```bash
# 在本地执行
chmod +x manual-deploy.sh
./manual-deploy.sh your-server-ip main

# 脚本会自动：
# 1. 检查本地代码状态
# 2. 推送到GitHub
# 3. SSH到服务器执行更新
```

### 方案2: 服务器端更新 (半自动)

适合：小团队开发

```bash
# 在服务器上执行
cd /opt/futures-system
./update.sh main

# 手动触发更新，自动处理：
# 1. 代码拉取
# 2. 服务重启
# 3. 状态检查
```

### 方案3: Webhook自动部署 (推荐)

适合：大多数项目

**特点：**
- ✅ 推送代码后自动部署
- ✅ 安全验证（GitHub签名）
- ✅ 支持多分支
- ✅ 详细日志记录
- ✅ 健康检查

**配置文件：**
- `webhook-server.py` - Webhook服务器
- `webhook-service.sh` - 服务管理脚本

### 方案4: GitHub Actions (企业级)

适合：大型项目、团队协作

**特点：**
- ✅ 完全自动化
- ✅ 可视化流程
- ✅ 支持测试、构建、部署
- ✅ 多环境支持

**配置文件：**
- `.github/workflows/deploy.yml`

#### GitHub Actions 设置步骤：

1. **设置GitHub Secrets**：
   - 进入仓库 `Settings` → `Secrets and variables` → `Actions`
   - 添加以下secrets：
     - `HOST`: 服务器IP
     - `USERNAME`: SSH用户名
     - `PRIVATE_KEY`: SSH私钥
     - `PORT`: SSH端口（默认22）

2. **生成SSH密钥**：
```bash
# 在本地生成密钥对
ssh-keygen -t rsa -b 4096 -C "github-actions"

# 将公钥添加到服务器
ssh-copy-id -i ~/.ssh/id_rsa.pub user@your-server-ip

# 将私钥内容复制到GitHub Secrets的PRIVATE_KEY
cat ~/.ssh/id_rsa
```

## 🔧 环境配置

### 环境变量配置

```bash
# Webhook配置
export WEBHOOK_SECRET="futures-webhook-secret-2024"
export PROJECT_PATH="/opt/futures-system"
export WEBHOOK_PORT="9000"

# 服务器配置
export SERVER_IP="your-server-ip"
export SERVER_USER="root"
```

### 防火墙配置

```bash
# 开放必要端口
sudo firewall-cmd --permanent --add-port=80/tcp    # HTTP
sudo firewall-cmd --permanent --add-port=443/tcp   # HTTPS
sudo firewall-cmd --permanent --add-port=9000/tcp  # Webhook
sudo firewall-cmd --reload
```

## 🛠️ 常用命令

### Webhook服务管理

```bash
# 启动Webhook服务
./webhook-service.sh start

# 查看状态
./webhook-service.sh status

# 查看日志
./webhook-service.sh logs

# 重启服务
./webhook-service.sh restart

# 安装为系统服务
./webhook-service.sh install
sudo systemctl start futures-webhook
```

### 部署管理

```bash
# 手动更新
./update.sh main

# 查看部署状态
./deploy.sh status

# 查看日志
./deploy.sh logs

# 备份数据
./deploy.sh backup

# 回滚（如果需要）
git reset --hard previous-commit-id
./deploy.sh restart
```

## 🔍 故障排除

### 1. Webhook无法触发

```bash
# 检查Webhook服务状态
./webhook-service.sh status

# 查看日志
./webhook-service.sh logs

# 检查端口是否开放
netstat -tlnp | grep 9000

# 测试连接
curl http://your-server-ip:9000/health
```

### 2. 部署失败

```bash
# 查看详细错误
./webhook-service.sh logs

# 手动执行更新
./update.sh main

# 检查Git状态
git status
git log --oneline -5
```

### 3. 服务无法启动

```bash
# 查看容器状态
docker-compose ps

# 查看容器日志
docker-compose logs

# 重新构建
docker-compose build --no-cache
```

## 📊 监控和维护

### 日志监控

```bash
# 实时查看日志
tail -f webhook.log
./deploy.sh logs -f

# 日志轮转配置
sudo vim /etc/logrotate.d/futures-system
```

### 性能监控

```bash
# 查看资源使用
docker stats

# 查看系统状态
htop
iotop
```

### 定期维护

```bash
# 清理Docker资源
docker system prune -f

# 备份数据
./deploy.sh backup

# 更新系统
sudo yum update -y
```

## 🎉 最佳实践

### 1. 分支策略
- `main/master`: 生产环境
- `develop`: 开发环境
- `feature/*`: 功能分支

### 2. 提交规范
```bash
git commit -m "feat: 添加新功能"
git commit -m "fix: 修复bug"
git commit -m "docs: 更新文档"
```

### 3. 部署检查清单
- [ ] 代码已测试
- [ ] 数据库迁移已完成
- [ ] 环境变量已更新
- [ ] 备份已创建
- [ ] 监控正常

### 4. 安全建议
- 使用强密码和密钥
- 定期更新系统和依赖
- 限制SSH访问
- 使用HTTPS

## 🆘 紧急回滚

如果部署出现问题，快速回滚：

```bash
# 方法1: Git回滚
git log --oneline -10  # 查看最近提交
git reset --hard <previous-commit-id>
./deploy.sh restart

# 方法2: 使用备份
ls backup/  # 查看备份
# 手动恢复配置文件

# 方法3: 容器回滚
docker-compose down
docker-compose up -d
```

---

选择适合你的部署方案，推荐从 **Webhook自动部署** 开始！
