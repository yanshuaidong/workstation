# WorkBack - 标准化Express后端项目

## 项目结构

```
workback/
├── app.js                    # Express应用配置
├── server.js                 # 服务器启动文件
├── package.json              # 项目依赖和脚本
├── env.example              # 环境变量示例
├── config/                   # 配置文件
│   └── config.js            # 主配置文件
├── routes/                   # 路由定义
│   └── api.js               # API路由
├── controllers/              # 控制器层
│   └── varietiesController.js
├── services/                 # 服务层
│   └── varietiesService.js
└── utils/                    # 工具类
    ├── httpClient.js        # HTTP客户端
    └── responseHandler.js   # 响应处理器
```

## 快速开始

### 1. 安装依赖
```bash
npm install
```

### 2. 配置环境变量
复制 `env.example` 为 `.env` 并修改配置：
```bash
cp env.example .env
```

### 3. 启动服务器
```bash
# 开发模式（自动重启）
npm run dev

# 生产模式
npm start
```

## API接口

### 获取品种数据
- **接口**: `POST /api/get-varieties`
- **描述**: 获取第三方交易品种数据
- **响应格式**:
```json
{
  "success": true,
  "message": "数据获取成功",
  "data": { ... },
  "timestamp": "2024-01-20T10:30:00.000Z"
}
```

## 项目特点

- **分层架构**: Controller → Service → Utils 清晰的分层结构
- **配置集中**: 统一的配置管理
- **错误处理**: 全局错误处理中间件
- **响应规范**: 统一的API响应格式
- **日志记录**: Morgan中间件记录请求日志
- **优雅关闭**: 支持优雅关闭服务器

## 开发规范

1. **控制器**：只负责接收请求和返回响应
2. **服务层**：处理业务逻辑
3. **工具类**：提供通用功能
4. **配置文件**：集中管理所有配置

## 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| PORT | 服务器端口 | 3000 |
| NODE_ENV | 运行环境 | development |
| CORS_ORIGIN | CORS来源 | * |
| JIAOYIKECHA_COOKIE | 第三方API Cookie | - |