# Flask 后端 API 服务

这是一个使用 Flask 构建的后端 API 服务。

## 项目结构

```
workbackpy/
├── app.py                 # 主应用程序入口
├── config/
│   └── config.py         # 配置文件
├── controllers/
│   └── example_controller.py  # 控制器
├── services/
│   └── example_service.py     # 服务层
├── routes/
│   └── api.py            # API 路由
├── utils/
│   ├── response_handler.py    # 响应处理工具
│   └── http_client.py         # HTTP 客户端工具
├── requirements.txt      # 依赖文件
├── env_example.txt      # 环境变量示例
├── .gitignore          # Git 忽略文件
└── README.md           # 项目说明
```

## 安装和运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 环境配置

复制 `env_example.txt` 为 `.env` 并根据需要修改配置：

```bash
cp env_example.txt .env
```

### 3. 运行服务

开发模式：
```bash
python app.py
```

生产模式：
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:create_app()
```

## API 端点

### 健康检查
- `GET /health` - 服务健康检查

### 示例 API
- `GET /api/test` - 测试端点
- `GET /api/examples` - 获取所有示例数据
- `POST /api/examples` - 创建示例数据
- `GET /api/examples/{id}` - 根据 ID 获取示例数据
- `PUT /api/examples/{id}` - 更新示例数据
- `DELETE /api/examples/{id}` - 删除示例数据

## 响应格式

### 成功响应
```json
{
  "success": true,
  "message": "操作成功",
  "timestamp": "2024-01-01T00:00:00",
  "data": {...}
}
```

### 错误响应
```json
{
  "success": false,
  "message": "错误信息",
  "timestamp": "2024-01-01T00:00:00",
  "error_code": "ERROR_CODE"
}
```

## 开发指南

### 添加新的 API

1. 在 `controllers/` 目录下创建控制器
2. 在 `services/` 目录下创建服务层
3. 在 `routes/api.py` 中添加路由
4. 测试 API 功能

### 项目特性

- ✅ 统一的响应格式
- ✅ 错误处理机制
- ✅ CORS 支持
- ✅ 环境配置管理
- ✅ 分层架构设计
- ✅ HTTP 客户端工具
- ✅ 健康检查端点

## 技术栈

- Flask 3.0.0
- Flask-CORS
- Python-dotenv
- Requests
- Gunicorn 