# 财联社新闻爬虫

本地运行的财联社加红电报新闻爬虫，支持新闻爬取和AI分析功能。

## 功能特性

- 🕷️ **新闻爬取**: 自动爬取财联社加红电报新闻
- 🗄️ **数据入库**: 将新闻数据保存到远程MySQL数据库
- 🤖 **AI分析**: 使用AI对新闻内容进行分析分类
- 📊 **去重处理**: 自动检测并跳过重复新闻
- ⚡ **异步处理**: AI分析支持批量异步处理

## 环境要求

- Python 3.8+
- Chrome/Chromium 浏览器
- ChromeDriver

## 安装依赖

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 只爬取新闻
```bash
python main.py crawl
```

### 2. 只进行AI分析
```bash
# 分析最新10条未分析的新闻
python main.py analyze

# 分析指定数量的新闻
python main.py analyze 20
```

### 3. 完整流程（爬取 + AI分析）
```bash
python main.py full
```

### 4. 默认模式（等同于full）
```bash
python main.py
```

## 项目结构

```
spiderx/
├── main.py          # 主程序入口
├── crawler.py       # 爬虫核心逻辑
├── database.py      # 数据库操作
├── ai_analyzer.py   # AI分析功能
├── requirements.txt # 依赖包列表
└── README.md        # 本文档
```

## 配置说明

### 数据库配置
数据库配置在 `database.py` 中，默认连接到阿里云RDS MySQL：
```python
DB_CONFIG = {
    'host': 'rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'ysd',
    'password': 'Yan1234567',
    'database': 'futures',
    'charset': 'utf8mb4'
}
```

### AI API配置
AI分析功能使用的是PoloAI的GPT-4o-mini模型，配置在 `ai_analyzer.py` 中。

## 注意事项

1. **浏览器依赖**: 需要本地安装Chrome或Chromium浏览器
2. **网络环境**: 需要能够访问财联社网站和AI API
3. **运行频率**: 建议适度使用，避免对目标网站造成过大压力
4. **数据库权限**: 确保有数据库的读写权限

## 常见问题

### Chrome驱动问题
如果遇到ChromeDriver相关错误：
1. 确保已安装Chrome浏览器
2. 下载对应版本的ChromeDriver并放到PATH中
3. 或者使用webdriver-manager自动管理驱动

### 网络连接问题
1. 检查网络连接
2. 确认能够访问财联社网站
3. 检查数据库连接配置

### AI分析失败
1. 检查AI API密钥是否有效
2. 确认API额度是否充足
3. 检查网络连接到AI服务
