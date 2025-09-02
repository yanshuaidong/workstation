# 期货数据系统

基于Docker的期货数据分析系统，包含前端展示、后端API和数据处理服务。

## 项目结构

```
workstation/
├── workfront/          # Vue.js前端项目
├── workback/           # Node.js后端服务 (7001端口)
├── workbackpy/         # Python后端服务 (可扩展)
├── automysqlback/      # 数据处理服务 (7001端口)
├── nginx/              # Nginx配置
├── docker-compose.yml  # Docker编排配置
├── deploy.sh           # 部署脚本
├── env.production      # 生产环境配置模板
└── .env               # 实际环境配置
```

## 核心功能

- **前端系统**: Vue.js开发的数据展示界面
- **后端API**: 提供期货数据接口
- **数据处理**: 自动获取和处理期货数据
- **反向代理**: Nginx统一入口和负载均衡

## 技术栈

- **前端**: Vue.js + Vue Router
- **后端**: Node.js / Python Flask
- **数据库**: MySQL (阿里云RDS)
- **容器**: Docker + Docker Compose
- **代理**: Nginx

## 访问地址

- **前端界面**: http://localhost/
- **后端API**: http://localhost/api-a/
- **监控面板**: http://localhost/monitor/

## 数据库配置

使用阿里云RDS MySQL数据库：
- 主机: rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com
- 端口: 3306
- 数据库: futures
- 到期时间: 2026年8月31日

## 开发说明

详细的开发和运维说明请参考 `OPERATIONS.md` 文档。




