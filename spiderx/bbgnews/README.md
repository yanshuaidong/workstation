# 📰 Bloomberg 新闻自动处理系统

一个完整的彭博新闻采集、筛选和存储系统，包含Chrome浏览器扩展插件和Python后端服务。

## 🎯 系统功能

### 谷歌插件（前端采集）
- 每1小时自动刷新Bloomberg网站页面
- 拦截Bloomberg文章列表API数据
- 自动发送新闻数据到本地Python服务

### Python服务（后端处理）
1. **实时接收**: 接收插件发送的新闻数据，存储到本地SQLite数据库 `bloomberg_news` 表
2. **定时处理**: 每天4个时间点（6点、12点、18点、24点）自动处理新闻
3. **AI筛选**: 调用AI接口筛选出期货相关新闻并翻译成中文
4. **MySQL存储**: 将AI筛选结果保存到MySQL数据库 `news_red_telegraph` 和 `news_process_tracking` 表
5. **分析任务**: 将筛选结果保存到本地SQLite数据库 `analysis_task` 表
6. **自动清理**: 处理完成后删除已处理的新闻数据

## 🔄 完整工作流程

```
Chrome插件（每1小时）
    ↓ 定时刷新Bloomberg页面
    ↓ 拦截 /lineup-next/api/stories 接口
    ↓ 发送新闻数据到本地服务
Python服务接收（Flask API）
    ↓ 存储到 bloomberg_news 表
    ↓ 基于 published_at 唯一索引去重
定时任务触发（6/12/18/24点）
    ↓ 查询 bloomberg_news 表（status=0）
    ↓ 筛选对应时间段的新闻（根据 created_at）
    ↓ 调用AI接口（带重试机制）
    ├─ 第1次：60秒超时
    ├─ 第2次：120秒超时
    ├─ 筛选期货相关新闻
    ├─ 翻译成中文
    └─ 规范输出格式
    ↓ 
保存到MySQL数据库（即使"无重要相关新闻"也保存）
    ├─ news_red_telegraph 表（新闻主表）
    └─ news_process_tracking 表（处理跟踪表）
    ↓
构建分析任务（仅有重要新闻时）
    ↓ 标题：【彭博社2025年11月30日0点到6点新闻】
    ↓ 内容：AI筛选结果 + 分析提示词
    ↓ news_time：时间段开始时间
    ↓
保存到 analysis_task 表
    ↓
更新 bloomberg_news 状态（status=1）
    ↓
删除已处理的新闻（status=1）
```

## 📊 数据流转说明

### 1. 插件发送格式
```json
{
  "capturedData": [
    {
      "publishedAt": "2025-11-30T03:59:03.235Z",
      "brand": "politics",
      "headline": "Thousands Mount Renewed Protests Against Philippine Corruption",
      "url": "/news/articles/2025-11-30/..."
    }
  ]
}
```

### 2. 数据库存储

#### SQLite数据库（本地）

##### bloomberg_news 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| published_at | DATETIME | 新闻发布时间（唯一索引，用于去重） |
| headline | TEXT | 新闻标题 |
| brand | TEXT | 新闻类型/品牌 |
| url | TEXT | 新闻链接（自动补全Bloomberg域名） |
| status | INTEGER | 状态：0-未处理，1-已处理 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

##### analysis_task 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键，自增 |
| title | TEXT | 任务标题 |
| prompt | TEXT | AI筛选结果 + 分析提示词 |
| news_time | DATETIME | 新闻时间段开始时间 |
| ai_result | TEXT | AI分析结果（待后续分析填充） |
| is_analyzed | INTEGER | 是否已分析：0-未分析，1-已分析 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

#### MySQL数据库（远程）

##### news_red_telegraph 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键，自增 |
| ctime | BIGINT | 新闻时间段开始时间的时间戳（秒） |
| title | VARCHAR(500) | 标题，如【彭博社2025年11月1日0点到6点新闻】 |
| content | TEXT | AI筛选过滤后的内容 |
| ai_analysis | MEDIUMTEXT | 默认值：暂无分析 |
| message_score | TINYINT | 默认值：6 |
| message_label | ENUM | 默认值：hard |
| message_type | VARCHAR(64) | 默认值：彭博社新闻 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

##### news_process_tracking 表
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键，自增 |
| news_id | BIGINT | 关联 news_red_telegraph 表的 id |
| ctime | BIGINT | 消息创建时间（冗余字段） |
| is_reviewed | TINYINT | 是否已完成标签校验，默认0 |
| track_day3_done | TINYINT | 3天跟踪是否完成，默认0 |
| track_day7_done | TINYINT | 7天跟踪是否完成，默认0 |
| track_day14_done | TINYINT | 14天跟踪是否完成，默认0 |
| track_day28_done | TINYINT | 28天跟踪是否完成，默认0 |
| created_at | TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | 更新时间 |

### 3. 时间段划分
- **0-6点**: 在6点处理
- **6-12点**: 在12点处理
- **12-18点**: 在18点处理
- **18-24点**: 在24点（0点）处理

## 🚀 快速启动

### 前置要求
- Python 3.7+
- Chrome浏览器
- 网络环境（能访问AI API）

### 第一步：初始化数据库
```bash
cd spiderx/db
python init_db.py
```

### 第二步：安装依赖
```bash
cd spiderx/bbgnews
pip3 install -r requirements.txt
```

### 第三步：启动服务

#### Linux/Mac
```bash
# 添加执行权限（首次运行）
chmod +x *.sh

# 启动服务
./start_scheduler.sh

# 停止服务
./stop_scheduler.sh
```

#### Windows
```bash
python main.py
```

#### 脚本说明

| 脚本 | 功能 | 说明 |
|------|------|------|
| `start_scheduler.sh` | 启动服务 | 后台运行，自动检查依赖，保存PID |
| `stop_scheduler.sh` | 停止服务 | 优雅停止，先SIGTERM再SIGKILL |

#### 脚本特性

- ✅ **智能检测**: 自动检查服务是否已运行
- ✅ **防止重复**: 不允许启动多个实例
- ✅ **优雅退出**: 信号处理，安全停止
- ✅ **后台运行**: 使用nohup，关闭终端不影响
- ✅ **macOS优化**: 使用caffeinate防止休眠
- ✅ **健康检查**: 启动后自动验证服务可用性
- ✅ **日志输出**: 详细的启动和运行日志

### 第四步：安装浏览器插件
1. 打开Chrome浏览器
2. 访问 `chrome://extensions/`
3. 开启右上角的"开发者模式"
4. 点击"加载已解压的扩展程序"
5. 选择 `spiderx/bbgnews` 目录
6. 插件安装成功后，点击插件图标启动定时任务

## 📋 服务接口

### 健康检查
```bash
curl http://localhost:1123/api/health
```
返回示例：
```json
{
  "status": "ok",
  "service": "Bloomberg新闻处理服务",
  "port": 1123,
  "time": "2025-12-06T10:00:00",
  "pending_news": 50,
  "database": "/path/to/spiderx/db/crawler.db"
}
```

### 统计信息
```bash
curl http://localhost:1123/api/stats
```
返回示例：
```json
{
  "bloomberg_news": {
    "pending": 50,
    "processed": 0,
    "total": 50
  },
  "analysis_task": {
    "total": 10,
    "pending": 2,
    "analyzed": 8
  },
  "database": "/path/to/spiderx/db/crawler.db"
}
```

### 手动触发处理（测试用）
```bash
curl -X POST http://localhost:1123/api/process_now
```

## 🔧 AI接口说明

### 重试机制
- 第一次尝试：超时60秒
- 第二次尝试：超时120秒
- 两次都失败则放弃本次处理

### AI任务（一次请求完成）
1. 筛选出期货相关新闻
2. 翻译成中文
3. 标注相关期货品种
4. 附带新闻URL

### 输出格式要求
```
【原油期货相关】【中文翻译的新闻标题】新闻URL
【黄金期货相关】【中文翻译的新闻标题】新闻URL
...
```

## 📂 目录结构

```
bbgnews/
├── manifest.json           # Chrome扩展配置
├── background.js           # 扩展后台脚本（定时刷新）
├── content-main.js         # 拦截脚本（MAIN world）
├── content-bridge.js       # 桥接脚本（ISOLATED world）
├── popup.html/popup.js     # 插件弹窗界面
├── icon.png               # 插件图标
├── main.py                # Python后端服务 ⭐
├── requirements.txt       # Python依赖
├── start_scheduler.sh     # 启动脚本（Linux/Mac）
├── stop_scheduler.sh      # 停止脚本（Linux/Mac）
├── bloomberg_service.log  # 服务日志
├── nohup.out             # 后台输出日志
├── scheduler.pid         # 进程ID文件
└── README.md             # 说明文档

../db/
├── crawler.db            # SQLite数据库文件
├── init_db.py           # 数据库初始化脚本
└── README.md            # 数据库说明文档
```

## 📁 核心文件说明

### Chrome扩展部分

1. **`background.js`** - 后台服务
   - 管理定时任务（Chrome Alarms API）
   - 默认每60分钟执行一次
   - 自动刷新Bloomberg标签页
   - 显示拦截成功徽章
   - 浏览器启动时自动恢复定时任务

2. **`content-main.js`** - 拦截脚本
   - 重写 `window.fetch` 和 `XMLHttpRequest`
   - 拦截 `/lineup-next/api/stories` 接口
   - 通过 `postMessage` 发送数据

3. **`content-bridge.js`** - 桥接脚本
   - 接收拦截到的数据
   - 发送到本地Python服务（`http://localhost:1123`）
   - 保存到 `chrome.storage.local`

4. **`popup.html/js`** - 用户界面
   - 显示定时任务状态
   - 提供启动/停止控制按钮
   - 显示执行记录

### Python服务部分

5. **`main.py`** ⭐ 核心服务
   - **Flask API**: 接收插件发送的数据，存入 `bloomberg_news` 表
   - **定时任务**: APScheduler调度器（6/12/18/24点）
   - **AI筛选**: 调用OpenAI兼容接口筛选期货相关新闻
   - **MySQL存储**: 保存AI筛选结果到 `news_red_telegraph` 和 `news_process_tracking` 表
   - **SQLite操作**: 保存分析任务到 `analysis_task` 表
   - **数据清理**: 删除已处理的新闻数据

## 🔍 技术细节

### Chrome插件工作原理

#### 为什么使用两个Content Script？

- **MAIN world** (`content-main.js`):
  - 可以访问页面的原生JavaScript对象
  - 能够重写 `window.fetch` 和 `XMLHttpRequest`
  - 拦截 `/lineup-next/api/stories` 接口
  - 无法访问 Chrome Extension API

- **ISOLATED world** (`content-bridge.js`):
  - 可以访问 Chrome Extension API
  - 接收 MAIN world 发送的数据
  - 发送数据到本地Python服务
  - 通过 `postMessage` 与MAIN world通信

#### 定时刷新机制

使用 Chrome Alarms API 实现定时任务：
```javascript
chrome.alarms.create('bloomberg-auto-refresh', {
  delayInMinutes: 60,
  periodInMinutes: 60
});
```
- 浏览器启动时自动恢复
- 支持通过popup界面控制启停
- 自动记录执行历史

### 定时任务实现

使用 `APScheduler` 的 `BackgroundScheduler`:
```python
scheduler.add_job(process_news_task, 'cron', hour='6,12,18,0', minute=0)
```

### AI接口重试策略

```python
# 第一次：60秒超时
# 第二次：120秒超时
# 失败后等待2秒再重试
```

### 数据去重机制

- 数据库层面：`published_at` 字段唯一索引
- 使用 `INSERT OR IGNORE` 语句
- 重复数据自动忽略

### 时间范围筛选

根据 `created_at` 字段筛选对应时间段的新闻（status=0）

## ⚠️ 注意事项

1. **SQLite数据库**: 本地数据库位于 `spiderx/db/crawler.db`
2. **MySQL数据库**: 远程MySQL需确保网络可达且账号有效
3. **AI接口**: 确保API密钥有效且有足够余额
4. **时区问题**: 服务器时区需要正确设置（系统使用本地时间）
5. **日志监控**: 定期查看 `bloomberg_service.log` 和 `nohup.out`
6. **端口占用**: 确保1123端口未被占用
7. **插件权限**: Bloomberg网站需要授予插件拦截权限

## 🐛 故障排查

### 插件无法拦截数据
- 检查是否在Bloomberg网站
- 查看浏览器控制台是否有错误
- 确认插件已启用
- 检查定时任务是否已启动（popup界面查看）

### Python服务无法启动
```bash
# 检查端口占用
lsof -i :1123  # Mac/Linux
netstat -ano | findstr :1123  # Windows

# 查看日志
tail -f bloomberg_service.log
tail -f nohup.out
```

### 定时任务未执行
- 检查系统时间是否正确
- 查看日志文件确认调度器状态
- 确认有待处理的新闻数据
- 使用 `/api/stats` 接口检查数据状态

### AI接口调用失败
- 检查API密钥是否有效
- 确认网络连接正常
- 查看日志了解具体错误信息

### SQLite数据库问题
```bash
# 重新初始化数据库
cd spiderx/db
python init_db.py
```

### MySQL数据库问题
- 检查MySQL服务器是否可达
- 确认账号密码正确
- 查看日志中的具体错误信息
- MySQL保存失败不会阻断后续流程（会继续执行analysis_task保存）

## 📊 监控与维护

### 查看服务状态

#### 方式1：查看日志
```bash
# 查看实时日志
tail -f bloomberg_service.log

# 查看后台输出
tail -f nohup.out
```

#### 方式2：API接口
```bash
# 健康检查
curl http://localhost:1123/api/health

# 统计信息
curl http://localhost:1123/api/stats
```

#### 方式3：进程状态
```bash
# 查看进程
cat scheduler.pid
ps aux | grep main.py
```

### 查看数据库数据
```bash
cd spiderx/db
sqlite3 crawler.db

# 查看待处理新闻数量
SELECT COUNT(*) FROM bloomberg_news WHERE status = 0;

# 查看分析任务
SELECT id, title, news_time FROM analysis_task ORDER BY id DESC LIMIT 10;

# 退出
.quit
```

### 测试定时任务
```bash
# 手动触发处理任务
curl -X POST http://localhost:1123/api/process_now
```

## 📝 日志文件

- `bloomberg_service.log`: 服务主日志（程序内部日志）
- `nohup.out`: 标准输出日志（后台运行输出）
- `scheduler.pid`: 进程ID文件

## 🔐 安全说明

代码中包含的敏感信息（API密钥）仅用于开发环境。生产环境建议：

1. 使用环境变量存储敏感信息
2. 配置文件不要提交到代码仓库
3. 定期更换密钥和密码

## 📞 技术支持

如有问题，请查看：
1. 日志文件：`bloomberg_service.log`
2. 数据库状态：`/api/stats` 接口
3. 插件控制台：Chrome开发者工具

## 🎉 总结

这是一个完整的自动化新闻处理系统，实现了从采集到存储的全流程自动化：

✅ 自动采集（Chrome插件定时刷新）  
✅ 实时接收（Flask API）  
✅ 本地存储（SQLite数据库）  
✅ 定时处理（APScheduler）  
✅ AI筛选（OpenAI兼容接口）  
✅ MySQL存储（news_red_telegraph + news_process_tracking）  
✅ 分析任务（analysis_task表）  
✅ 自动清理（删除已处理数据）

系统可以24小时无人值守运行，自动完成新闻的采集、筛选、翻译和存储工作。
