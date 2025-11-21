# Routes 路由模块目录

本目录包含所有的 Flask 蓝图（Blueprint）路由模块。

## 模块说明

### `contracts_routes.py` - 合约管理模块
包含以下功能模块的API接口：
- **合约管理** (3个接口)
  - 更新合约列表
  - 获取合约列表
  - 获取合约列表更新记录
  
- **历史数据** (5个接口)
  - 批量更新所有主连历史数据
  - 重试单个合约历史数据更新
  - 获取历史数据更新日志
  - 重新计算技术指标
  - 获取指定合约的历史数据
  
- **分时行情** (2个接口)
  - 获取分时合约列表
  - 获取分时行情数据
  
- **推荐记录** (2个接口)
  - 手动记录当日推荐
  - 获取推荐记录列表

**代码行数：** ~1650 行  
**蓝图名称：** `contracts_bp`

---

### `news_routes.py` - 新闻管理模块
包含以下功能模块的API接口：
- **新闻管理** (13个接口)
  - 获取新闻统计信息
  - 分页查询新闻列表
  - 创建新闻
  - 获取新闻详情
  - 更新新闻
  - 删除新闻
  - 获取待校验的新闻列表
  - 标记新闻为已校验
  - 获取需要跟踪的新闻列表
  - 更新跟踪状态
  - 初始化跟踪记录
  
- **OSS文件管理** (2个接口)
  - 获取OSS上传签名URL
  - 获取OSS访问URL

**代码行数：** ~920 行  
**蓝图名称：** `news_bp`

---

## 使用方式

### 在 app.py 中导入和注册

```python
from routes import contracts_bp, news_bp

app.register_blueprint(contracts_bp, url_prefix='/api')
app.register_blueprint(news_bp, url_prefix='/api')
```

### 访问共享资源

在路由模块中访问数据库连接和OSS连接：

```python
from flask import current_app

# 获取数据库连接函数
get_db_connection = current_app.config['get_db_connection']
conn = get_db_connection()

# 获取OSS bucket
get_oss_bucket = current_app.config['get_oss_bucket']
bucket = get_oss_bucket()
```

---

## 添加新的路由模块

如果需要添加新的路由模块，按以下步骤操作：

1. **创建新的路由文件**
   ```bash
   touch routes/your_new_routes.py
   ```

2. **定义蓝图**
   ```python
   from flask import Blueprint
   
   your_new_bp = Blueprint('your_module', __name__)
   
   @your_new_bp.route('/your-endpoint', methods=['GET'])
   def your_function():
       # 实现逻辑
       pass
   ```

3. **在 `__init__.py` 中导出**
   ```python
   from .your_new_routes import your_new_bp
   
   __all__ = ['contracts_bp', 'news_bp', 'your_new_bp']
   ```

4. **在 `app.py` 中注册**
   ```python
   from routes import contracts_bp, news_bp, your_new_bp
   
   app.register_blueprint(your_new_bp, url_prefix='/api')
   ```

---

## 技术栈

- **Flask Blueprint** - 模块化路由管理
- **PyMySQL** - MySQL数据库连接
- **OSS2** - 阿里云OSS文件管理
- **akshare** - 金融数据获取
- **pandas** - 数据处理
- **ta** - 技术指标计算

---

**最后更新：** 2025-11-20

