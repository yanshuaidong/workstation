# 📰 Bloomberg News API 拦截器

一个Chrome浏览器扩展插件，用于自动拦截并显示Bloomberg网站的文章列表API响应数据。

我来帮你分析整个 bbgnews 插件的运行逻辑。让我先读取关键文件来理解整体架构。

根据我对代码的分析,这是一个 **Chrome 浏览器扩展插件**,用于拦截 Bloomberg 网站的文章列表 API 并保存数据。让我详细解释各个文件的作用和完整运行逻辑:

## 📁 文件结构说明

### 核心代码文件:

1. **`manifest.json`** - Chrome 扩展配置文件
   - 定义插件名称、版本、权限
   - 配置了两个 content script:
     - `content-main.js` (运行在 MAIN world)
     - `content-bridge.js` (运行在 ISOLATED world)
   - 指定只在 `bloomberg.com` 域名下工作

2. **`content-main.js`** ⭐ 核心拦截脚本
   - 运行在**主页面环境** (MAIN world)
   - 重写 `window.fetch` 和 `XMLHttpRequest` 原生方法
   - 拦截目标: `/lineup-next/api/stories` 接口
   - 过滤条件: 包含 `types=` 参数且不包含 `id=` 参数(只拦截列表请求,不拦截详情请求)
   - 拦截到数据后通过 `postMessage` 发送给 bridge 脚本

3. **`content-bridge.js`** ⭐ 桥接脚本
   - 运行在**隔离环境** (ISOLATED world,可访问 Chrome API)
   - 监听来自 `content-main.js` 的 `postMessage` 消息
   - 执行三个操作:
     - 保存数据到 `chrome.storage.local`
     - 发送数据到本地 Python 服务器 (`http://localhost:1123`)
     - 通知 background script

4. **`background.js`** - 后台服务
   - 监听来自 content script 的消息
   - 显示绿色徽章 ✓ 表示拦截成功
   - 3秒后自动清除徽章

5. **`popup.html/popup.js`** - 用户界面
   - 点击插件图标显示的弹出窗口
   - 显示拦截到的 JSON 数据
   - 提供"刷新页面"和"清除数据"按钮
   - 实时监听 `chrome.storage` 变化并更新显示

6. **`main.py`** - Python Flask 后端服务
   - 监听端口 1123
   - 接收 POST 请求: `/api/capture`
   - 将数据保存为 JSON 文件到 `captured_data/` 目录
   - 提供健康检查和文件列表接口

7. **`content.js`** ❌ 已废弃
   - 早期版本的拦截脚本
   - 现在已被 `content-main.js` 和 `content-bridge.js` 替代

## 🔄 完整运行流程

```
用户访问 Bloomberg 网站
         ↓
[1] Chrome 自动注入 content-main.js (MAIN world)
    - 在 document_start 时刻(页面加载前)
    - 重写 window.fetch 和 XMLHttpRequest
         ↓
[2] Chrome 自动注入 content-bridge.js (ISOLATED world)
    - 监听来自 MAIN world 的消息
         ↓
[3] 页面发起网络请求
    - Bloomberg 页面加载时会请求文章列表 API
         ↓
[4] content-main.js 拦截请求
    - 检查 URL 是否包含 /lineup-next/api/stories
    - 检查是否是列表请求 (有 types= 且无 id=)
    - 克隆响应并解析 JSON
    - 通过 postMessage 发送数据
         ↓
[5] content-bridge.js 接收消息
    - 保存到 chrome.storage.local
    - 发送到本地服务器 (localhost:1123)
    - 通知 background.js
         ↓
[6] background.js 处理通知
    - 显示绿色徽章 ✓
    - 3秒后清除徽章
         ↓
[7] main.py 接收数据 (如果在运行)
    - 保存为带时间戳的 JSON 文件
    - 同时保存为 latest.json
         ↓
[8] 用户点击插件图标
    - popup.js 从 chrome.storage 读取数据
    - 格式化显示在弹出窗口中
```

## 🎯 技术要点

### 为什么需要两个 content script?

- **MAIN world** (`content-main.js`):
  - 可以访问页面的原生 JavaScript 对象
  - 能够重写 `window.fetch` 和 `XMLHttpRequest`
  - **不能**访问 Chrome Extension API

- **ISOLATED world** (`content-bridge.js`):
  - 可以访问 Chrome Extension API (`chrome.storage`, `chrome.runtime`)
  - **不能**直接访问页面的 JavaScript 环境
  - 通过 `window.postMessage` 与 MAIN world 通信

### 数据流向:

```
Bloomberg API Response
    ↓ (被拦截)
content-main.js
    ↓ (postMessage)
content-bridge.js
    ↓ (分三路)
    ├─→ chrome.storage.local (Chrome本地存储)
    ├─→ localhost:1123 (Python服务器)
    └─→ background.js (显示徽章)
```

## 📝 关键特性

1. **自动拦截**: 页面加载时自动工作,无需手动操作
2. **双重拦截**: 同时支持 Fetch 和 XHR 两种请求方式
3. **精准过滤**: 只拦截列表请求,不拦截详情请求
4. **数据持久化**: 同时保存到浏览器存储和本地文件
5. **实时通知**: 拦截成功后显示徽章,popup 实时更新
6. **⏰ 定时任务**: 支持自动定时刷新页面并拦截数据(新功能)

## ⚙️ 使用方式

### 基础使用

1. 安装插件到 Chrome
2. (可选) 启动 Python 服务: `python main.py`
3. 访问 Bloomberg 网站 (如 https://www.bloomberg.com/latest)
4. 插件自动拦截 API 请求
5. 点击插件图标查看数据

### ⏰ 定时任务功能

插件支持自动定时刷新页面并拦截数据，实现无人值守的数据采集：

#### 使用方法

1. 点击插件图标打开控制面板
2. 设置刷新间隔（1-1440分钟）
3. 点击"▶️ 启动定时任务"按钮
   - 立即执行第一次爬虫任务
   - 然后按设定间隔定时执行
4. 查看执行记录表格了解任务运行情况
5. 点击"⏸️ 停止定时任务"停止自动采集

#### 主要特性

- **立即执行**: 启动后立即执行第一次，无需等待
- **后台运行**: 关闭控制面板后继续运行
- **智能管理**: 自动刷新已有标签页或后台打开新标签页
- **执行记录**: 详细记录每次执行时间和成功/失败状态
- **状态监控**: 实时显示运行状态、启动时间、上次执行和下次执行时间

#### 注意事项

- Chrome浏览器需保持运行（可最小化）
- 建议启动Python服务（`main.py`）保存数据到本地文件
- 推荐间隔：30-60分钟（根据数据更新频率调整）