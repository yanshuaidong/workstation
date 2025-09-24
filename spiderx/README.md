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
python3 main.py crawl
```

### 2. 只进行AI分析
```bash
# 分析最新10条未分析的新闻
python3 main.py analyze

# 分析指定数量的新闻
python3 main.py analyze 20
```

### 3. 完整流程（爬取 + AI分析）
```bash
python main.py full
```

### 4. 调度模式（10天长期运行）
```bash
python main.py schedule
```
**调度模式特性：**
- 运行时长：10天（240小时）
- 执行间隔：每4小时执行一次完整流程
- 每次执行：爬取新闻20条 + AI分析20条
- 心跳监控：每4小时打印心跳信息（共60次）
- 日志轮转：按日期生成日志文件，每天一个
- 异常处理：遇到错误立即停止并输出详细信息

### 5. 默认模式（等同于full）
```bash
python main.py
```

## 项目结构

```
spiderx/
├── main.py            # 主程序入口（包含所有核心功能）
├── scheduler.py       # 调度器模块（10天长期运行）
├── start_scheduler.sh # 启动脚本（自动适配macOS系统）
├── stop_scheduler.sh  # 停止脚本（安全停止调度器）
├── requirements.txt   # 依赖包列表
├── README.md          # 本文档
├── scheduler.pid      # 进程ID文件（运行时自动生成）
├── nohup.out          # 控制台输出文件（运行时自动生成）
└── logs/              # 日志目录（调度模式自动生成）
    ├── news_crawler_2025-09-24.log
    ├── news_crawler_2025-09-25.log
    └── ...            # 每天一个日志文件
```

## 配置说明

### 数据库配置
数据库配置在 `main.py` 中，默认连接到阿里云RDS MySQL：
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
AI分析功能使用的是PoloAI的GPT-4o-mini模型，配置在 `main.py` 中。

## 调度模式详细说明

### 运行特性
- **运行时长**: 10天（240小时）不间断运行
- **执行频率**: 每4小时执行一次完整流程（共60次）
- **每次任务**: 爬取新闻20条 + AI分析20条
- **心跳监控**: 每4小时在控制台输出心跳信息
- **日志管理**: 按日期自动轮转日志文件，每天生成一个

### 正常预期
- 控制台累计心跳输出：**60条**
- logs/目录中生成：**10个日志文件**（每天一个）
- 程序运行240小时不间断

### 异常处理
- 任何执行异常都会导致程序立即停止
- 控制台打印"ERROR"并显示错误详情
- 日志文件记录完整错误堆栈信息
- 需要人工干预重启程序

### 启动和停止调度模式

#### 启动调度器

**macOS 系统（推荐）**
```bash
# 进入项目目录
cd spiderx

# 使用caffeinate防止系统休眠，确保程序不被中断
caffeinate -i python3 main.py schedule

# 或者后台运行（推荐用于长期运行）
nohup caffeinate -i python3 main.py schedule > nohup.out 2>&1 &
```

**Linux/Windows 系统**
```bash
# 进入项目目录
cd spiderx

# 直接启动
python3 main.py schedule

# 或者后台运行
nohup python3 main.py schedule > nohup.out 2>&1 &
```

#### 使用启动脚本（自动适配系统）
```bash
# 进入项目目录
cd spiderx

# 启动调度器（自动检测macOS并使用caffeinate）
./start_scheduler.sh

# 停止调度器（安全停止）
./stop_scheduler.sh

# 查看运行状态
ps aux | grep "main.py schedule"
```

#### 停止调度器

**使用停止脚本（推荐）**
```bash
# 安全停止调度器
./stop_scheduler.sh
```

**手动停止方法**
```bash
# 方法1: 使用保存的进程ID
kill $(cat scheduler.pid)

# 方法2: 查找进程并停止
ps aux | grep "main.py schedule"
kill [进程ID]

# 方法3: 强制停止（紧急情况）
kill -9 $(cat scheduler.pid)
```

## 注意事项

1. **浏览器依赖**: 需要本地安装Chrome或Chromium浏览器
2. **网络环境**: 需要能够访问财联社网站和AI API
3. **运行频率**: 调度模式已优化间隔时间，避免对目标网站造成过大压力
4. **数据库权限**: 确保有数据库的读写权限
5. **长期运行**: 调度模式适合服务器环境，建议使用screen或nohup后台运行
6. **macOS 特别注意**: 使用 `caffeinate -i` 命令防止系统休眠导致程序中断
7. **进程监控**: 后台运行时建议定期检查进程状态，确保程序正常运行

## 常见问题

### 脚本权限问题
**问题**: `zsh: permission denied: ./start_scheduler.sh`
**原因**: 脚本文件没有执行权限
**解决方案**:
```bash
# 给脚本添加执行权限
chmod +x start_scheduler.sh
chmod +x stop_scheduler.sh

# 验证权限
ls -la *.sh
```

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

### macOS 系统休眠问题
**问题**: 程序运行一段时间后自动停止
**原因**: macOS 系统进入休眠状态导致程序中断
**解决方案**:
1. 使用 `caffeinate -i` 命令防止系统休眠：
   ```bash
   caffeinate -i python3 main.py schedule
   ```
2. 或者在系统偏好设置中调整节能设置：
   - 打开"系统偏好设置" → "节能"
   - 将"防止电脑自动进入睡眠"选项勾选
   - 或者将睡眠时间设置为"永不"

### 进程状态检查
```bash
# 查看是否有python进程在运行
ps aux | grep python

# 查看特定进程详情
ps aux | grep "main.py schedule"

# 实时查看日志输出
tail -f nohup.out
tail -f logs/news_crawler_$(date +%Y-%m-%d).log
```

### 停止程序运行
```bash
# 方法1: 使用保存的进程ID（推荐）
kill $(cat scheduler.pid)

# 方法2: 手动查找并停止进程
ps aux | grep "main.py schedule"
kill [进程ID]

# 方法3: 强制停止（如果常规停止无效）
kill -9 $(cat scheduler.pid)

# 方法4: 停止所有相关Python进程（谨慎使用）
pkill -f "main.py schedule"

# 验证程序已停止
ps aux | grep "main.py schedule"
```

### 重启程序
```bash
# 停止当前程序
kill $(cat scheduler.pid)

# 等待几秒确保程序完全停止
sleep 3

# 重新启动
./start_scheduler.sh
```

### 完整的启动和停止流程

```bash
# 启动
./start_scheduler.sh

# 查看状态
ps aux | grep "main.py schedule"

# 查看日志
tail -f nohup.out

# 停止
./stop_scheduler.sh

# 重启
./stop_scheduler.sh && sleep 3 && ./start_scheduler.sh

```