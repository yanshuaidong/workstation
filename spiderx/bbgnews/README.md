# 📰 Bloomberg 新闻自动处理系统

一个完整的彭博新闻采集、筛选和存储系统，包含Chrome浏览器扩展插件和Python后端服务。

## 🎯 系统功能

### 谷歌插件（前端采集）
- 每1小时自动拦截Bloomberg网站的文章列表API
- 自动发送新闻数据到本地Python服务

### Python服务（后端处理）
1. **实时接收**: 接收插件发送的新闻数据，存储到本地JSON文件
2. **定时处理**: 每天4个时间点（6点、12点、18点、24点）自动处理新闻
3. **AI筛选**: 调用AI接口筛选出股票/期货相关新闻并翻译成中文
4. **数据库存储**: 将处理后的新闻保存到阿里云MySQL数据库
5. **自动清理**: 处理完成后删除已处理的本地数据

## 🔄 完整工作流程

```
Chrome插件（每1小时）
    ↓ 拦截Bloomberg API
    ↓ 发送新闻数据到本地服务
Python服务接收（Flask API）
    ↓ 存储到 bloomberg_news.json
    ↓ 添加 localReceivedTime 字段
    ↓ 去重（根据publishedAt）
定时任务触发（6/12/18/24点）
    ↓ 加载本地所有新闻
    ↓ 筛选对应时间段的新闻（根据localReceivedTime）
    ↓ 调用AI接口（带重试机制）
    ├─ 第1次：60秒超时
    ├─ 第2次：120秒超时
    ├─ 筛选股票/期货相关新闻
    ├─ 翻译成中文
    └─ 规范输出格式（1、xxx 2、xxx）
    ↓ 
构建标题和内容
    ↓ 标题：【彭博社2025年11月30日0点到6点新闻】
    ↓ 内容：AI返回的筛选结果
    ↓ ctime：时间段开始时间戳
    ↓
保存到数据库（2个表）
    ├─ news_red_telegraph（新闻主表）
    └─ news_process_tracking（跟踪表）
    ↓
删除已处理的本地数据
    └─ 只删除对应时间段的新闻
```

## 📊 数据流转说明

### 1. 插件发送格式
```json
{
  "capturedData": [
    {
      "publishedAt": "2025-11-30T03:59:03.235Z",
      "brand": "politics",
      "headline": "Thousands Mount Renewed Protests Against Philippine Corruption"
    }
  ],
  "serverReceivedTime": "2025-11-30T12:57:05.116034"
}
```

### 2. 本地存储格式
每条新闻会添加 `localReceivedTime` 字段：
```json
{
  "publishedAt": "2025-11-30T03:59:03.235Z",
  "brand": "politics",
  "headline": "Thousands Mount Renewed Protests...",
  "localReceivedTime": "2025-11-30T12:57:05.116034"
}
```

### 3. 时间段划分
- **0-6点**: 在6点处理
- **6-12点**: 在12点处理
- **12-18点**: 在18点处理
- **18-24点**: 在24点（0点）处理

### 4. 数据库存储
**news_red_telegraph 表**:
- `ctime`: 时间段开始时间的时间戳
- `title`: 【彭博社2025年11月1日0点到6点新闻】
- `content`: AI筛选翻译后的内容（1、xxx。2、xxx。3、xxx。）
- `ai_analysis`: "暂无分析"
- `message_score`: 6
- `message_label`: "hard"
- `message_type`: "彭博社新闻"

**news_process_tracking 表**:
- 自动添加一条默认值记录

## 🚀 快速启动

### 前置要求
- Python 3.7+
- Chrome浏览器
- MySQL数据库（已配置好）
- 网络环境（能访问AI API和数据库）

### 第一步：安装依赖
```bash
cd spiderx/bbgnews
pip3 install -r requirements.txt
```

### 第二步：启动服务

#### Linux/Mac
```bash
# 添加执行权限（首次运行）
chmod +x *.sh

# 启动服务
./start_scheduler.sh

# 停止服务
./stop_scheduler.sh
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

### 第三步：安装浏览器插件
1. 打开Chrome浏览器
2. 访问 `chrome://extensions/`
3. 开启右上角的"开发者模式"
4. 点击"加载已解压的扩展程序"
5. 选择 `spiderx/bbgnews` 目录
6. 插件安装成功后，访问 Bloomberg 网站即可自动工作

## 📋 服务接口

### 健康检查
```bash
curl http://localhost:1123/api/health
```

### 统计信息
```bash
curl http://localhost:1123/api/stats
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
1. 筛选出股票/期货相关新闻
2. 翻译成中文
3. 规范输出格式

### 输出格式要求
```
1、[中文翻译的新闻标题1]
2、[中文翻译的新闻标题2]
3、[中文翻译的新闻标题3]
...
```

## 📂 目录结构

## 📂 目录结构

```
bbgnews/
├── manifest.json           # Chrome扩展配置
├── background.js           # 扩展后台脚本
├── content-main.js         # 拦截脚本（MAIN world）
├── content-bridge.js       # 桥接脚本（ISOLATED world）
├── popup.html/popup.js     # 插件弹窗界面
├── icon.png               # 插件图标
├── main.py                # Python后端服务 ⭐
├── requirements.txt       # Python依赖
├── start_scheduler.sh     # 启动脚本（Linux/Mac）
├── stop_scheduler.sh      # 停止脚本（Linux/Mac）
├── captured_data/         # 数据存储目录
│   └── bloomberg_news.json  # 单一数据文件
├── bloomberg_service.log  # 服务日志
├── nohup.out             # 后台输出日志
├── scheduler.pid         # 进程ID文件
└── README.md             # 说明文档
```

## 📁 核心文件说明

### Chrome扩展部分

1. **`content-main.js`** - 拦截脚本
   - 重写 `window.fetch` 和 `XMLHttpRequest`
   - 拦截 `/lineup-next/api/stories` 接口
   - 通过 `postMessage` 发送数据

2. **`content-bridge.js`** - 桥接脚本
   - 接收拦截到的数据
   - 发送到本地Python服务（`http://localhost:1123`）
   - 保存到 `chrome.storage.local`

3. **`background.js`** - 后台服务
   - 显示拦截成功徽章

4. **`popup.html/js`** - 用户界面
   - 显示拦截数据
   - 提供控制按钮

### Python服务部分

5. **`main.py`** ⭐ 核心服务
   - **Flask API**: 接收插件发送的数据
   - **定时任务**: APScheduler调度器（6/12/18/24点）
   - **AI筛选**: 调用OpenAI兼容接口
   - **数据库操作**: 保存到MySQL两个表
   - **数据清理**: 删除已处理的本地数据

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

- 根据 `publishedAt` 字段去重
- 存储时检查是否已存在

### 时间范围筛选

根据 `localReceivedTime` 字段筛选对应时间段的新闻

## ⚠️ 注意事项

1. **数据库配置**: 确保数据库可访问且表结构正确（见 `1example/database_example.py`）
2. **AI接口**: 确保API密钥有效且有足够余额
3. **时区问题**: 服务器时区需要正确设置（系统使用本地时间）
4. **日志监控**: 定期查看 `bloomberg_service.log` 和 `nohup.out`
5. **数据备份**: 定期备份数据库和 `captured_data/bloomberg_news.json`
6. **端口占用**: 确保1123端口未被占用
7. **插件权限**: Bloomberg网站需要授予插件拦截权限

## 🐛 故障排查

### 插件无法拦截数据
- 检查是否在Bloomberg网站
- 查看浏览器控制台是否有错误
- 确认插件已启用

### Python服务无法启动
```bash
# 检查端口占用
lsof -i :1123  # Mac/Linux

# 查看日志
tail -f bloomberg_service.log
tail -f nohup.out
```

### 定时任务未执行
- 检查系统时间是否正确
- 查看日志文件确认调度器状态
- 确认有待处理的新闻数据

### AI接口调用失败
- 检查API密钥是否有效
- 确认网络连接正常
- 查看日志了解具体错误信息

### 数据库连接失败
- 检查数据库配置是否正确
- 确认数据库服务运行正常
- 验证网络连通性

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

### 查看数据文件
```bash
# 查看本地存储的新闻数量
cat captured_data/bloomberg_news.json | python -m json.tool
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

代码中包含的敏感信息（数据库密码、API密钥）仅用于开发环境。生产环境建议：

1. 使用环境变量存储敏感信息
2. 配置文件不要提交到代码仓库
3. 定期更换密钥和密码
4. 限制数据库访问IP白名单

## 📞 技术支持

如有问题，请查看：
1. 日志文件：`bloomberg_service.log`
2. 数据文件：`captured_data/bloomberg_news.json`
3. 插件控制台：Chrome开发者工具

## 🎉 总结

这是一个完整的自动化新闻处理系统，实现了从采集到存储的全流程自动化：

✅ 自动采集（Chrome插件）  
✅ 实时接收（Flask API）  
✅ 定时处理（APScheduler）  
✅ AI筛选（OpenAI接口）  
✅ 数据存储（MySQL）  
✅ 自动清理（本地数据）

系统可以24小时无人值守运行，自动完成新闻的采集、筛选、翻译和存储工作。

### 第一步：安装依赖
```bash
cd spiderx/bbgnews
pip3 install -r requirements.txt
```

### 第二步：启动服务

#### Linux/Mac
```bash
# 添加执行权限（首次运行）
chmod +x *.sh

# 启动服务
./start_scheduler.sh

# 停止服务
./stop_scheduler.sh
```

1cesh