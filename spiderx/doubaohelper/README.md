# 豆包 自动提问助手

这是一个 Chrome 浏览器插件，用于自动向豆包 AI 提问并保存结果到数据库。

## 功能特点

- ✅ 自动从本地数据库获取待分析任务
- ✅ 定时向豆包 AI 提问（每天6次：1点、5点、9点、13点、17点、21点）
- ✅ 自动保存结果到阿里云 MySQL 数据库
- ✅ 支持测试执行（不影响正式任务计数）
- ✅ 完整的执行记录和状态管理

## 系统架构

```
┌─────────────────────┐
│  Chrome 插件界面     │ (popup.html)
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Background Worker  │ (background.js)
│  - 定时任务调度      │
│  - 任务状态管理      │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Content Script     │ (content-script.js)
│  - 操作豆包页面      │
│  - 自动提问/获取回答 │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Python 后端服务    │ (main.py)
│  - 读取本地数据库    │
│  - 保存到云端数据库  │
└─────────────────────┘
```

## 安装步骤

### 1. 安装 Python 依赖

```bash
cd spiderx/doubaohelper
pip install -r requirements.txt
```

### 2. 启动后端服务

```bash
python main.py
```

服务将在 `http://localhost:1127` 启动。

### 3. 安装 Chrome 插件

1. 打开 Chrome 浏览器
2. 访问 `chrome://extensions/`
3. 开启右上角的"开发者模式"
4. 点击"加载已解压的扩展程序"
5. 选择 `spiderx/doubaohelper` 文件夹

### 4. 配置插件

1. 点击浏览器工具栏中的插件图标
2. 点击"启动任务"按钮
3. 插件会自动在指定时间执行任务

## 使用说明

### 定时任务

- **执行频率**: 每天6次（1点、5点、9点、13点、17点、21点）
- **总次数**: 120次（运行20天）
- **时间安排**: 与 ChatGPT 插件错开1小时，避免冲突

### 测试执行

点击"🧪 测试执行一次"按钮可以立即执行一次任务，用于测试插件是否正常工作。测试执行不会计入正式任务的次数。

### 查看日志

- 插件日志：打开 Chrome DevTools (F12) 查看控制台
- 后端日志：查看 `doubao_helper.log` 文件

## 豆包页面结构

插件通过以下 DOM 元素与豆包页面交互：

- 创建新对话按钮：`div[data-testid="create_conversation_button"]`
- 输入框：`textarea[data-testid="chat_input_input"]`
- 发送按钮：`button[data-testid="chat_input_send_button"]`
- 中断按钮（AI生成中）：`div[data-testid="chat_input_local_break_button"]`
- AI回答内容：`div[data-testid="message_text_content"]`

## 数据库结构

### 本地数据库 (SQLite)

表名：`analysis_task`

- `id`: 任务ID
- `title`: 标题
- `prompt`: 提示词
- `doubao_analyzed`: 豆包是否已分析（0/1）
- `doubao_result`: 豆包分析结果
- `news_time`: 新闻时间
- `created_at`: 创建时间
- `updated_at`: 更新时间

### 云端数据库 (MySQL)

表名：`news_red_telegraph`

- `id`: 新闻ID
- `ctime`: 创建时间戳
- `title`: 标题
- `content`: 内容
- `ai_analysis`: AI分析
- `message_type`: 消息类型（豆包新闻）

表名：`news_process_tracking`

- `news_id`: 新闻ID（外键）
- `ctime`: 创建时间戳

## 注意事项

1. 确保后端服务在使用插件前已启动
2. 确保本地数据库 `../db/crawler.db` 存在
3. 确保网络连接正常，能访问阿里云数据库
4. 使用插件时需要登录豆包账号
5. 建议在豆包页面 (https://www.doubao.com/chat/) 打开插件

## 故障排查

### 插件无法连接后端

- 检查后端服务是否启动：访问 `http://localhost:1127/health`
- 检查端口是否被占用

### 任务执行失败

- 打开 Chrome DevTools 查看详细错误信息
- 检查豆包页面结构是否变化
- 查看后端日志 `doubao_helper.log`

### 数据库连接失败

- 检查本地数据库文件是否存在
- 检查阿里云数据库配置是否正确
- 检查网络连接

## 开发说明

### 文件结构

```
doubaohelper/
├── manifest.json          # 插件配置文件
├── background.js          # 后台服务 worker
├── content-script.js      # 内容脚本（页面操作）
├── popup.html            # 弹出窗口界面
├── popup.js              # 弹出窗口主控制器
├── popup-ui.js           # UI 管理模块
├── popup-storage.js      # 存储管理模块
├── main.py               # Python 后端服务
├── requirements.txt      # Python 依赖
├── README.md             # 说明文档
└── icon.png              # 插件图标
```

### 修改定时时间

在 `background.js` 中修改 `executionHours` 数组：

```javascript
const executionHours = [1, 5, 9, 13, 17, 21];
```

### 修改后端端口

1. 在 `main.py` 中修改端口号（最后一行）
2. 在 `background.js` 和 `content-script.js` 中修改 `BACKEND_URL`

## 版本信息

- **版本**: 1.0.0
- **作者**: YSD
- **创建日期**: 2026-02-07

## 许可证

MIT License
