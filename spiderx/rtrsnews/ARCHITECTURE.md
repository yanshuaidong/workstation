# Reuters News Scraper - 架构说明文档

## 架构类型：标准MVC扩展结构

根据Chrome扩展架构知识库，本项目采用**标准MVC扩展结构**，适用于"UI + 后端API请求 + 用户配置与状态存储"的场景。

---

## 四层架构设计

### 1. ❌ MAIN World（不需要）
**决策理由**：本项目不需要劫持页面原生JS或拦截页面请求，因此不使用MAIN world。

---

### 2. ✅ ISOLATED World - Content Script（视图/数据采集层）

**文件**：`content.js`

**职责**：
- ✅ DOM操作和数据提取
- ✅ 页面有效性检查
- ✅ 用户操作反馈（Toast提示）

**核心功能**：
```javascript
// 提取文章内容
extractArticleContent()

// 检查页面有效性
checkPageValidity()

// 显示用户反馈
showSuccessFeedback()
showErrorFeedback()
```

**通信方式**：
- 监听来自 Background 的消息
- 返回提取结果给 Background

**环境特点**：
- 独立的JS上下文（与页面隔离）
- 共享同一个DOM
- 拥有扩展API能力

---

### 3. ✅ Background Service Worker（控制中心/业务逻辑层）

**文件**：`background.js`

**职责**：
- ✅ 消息路由和调度
- ✅ 与Flask后端API通信
- ✅ 状态管理和持久化（chrome.storage）
- ✅ 错误处理和重试机制
- ✅ 统计信息维护

**核心功能**：
```javascript
// 消息路由
handleExtractContent()      // 处理提取请求
handleSaveArticle()          // 处理保存请求
handleGetArticlesList()      // 获取文章列表
handleGetSettings()          // 获取配置
handleUpdateSettings()       // 更新配置
handleGetStats()             // 获取统计
handleCheckServerHealth()    // 检查服务器健康

// 重试机制
saveToServerWithRetry()      // 带重试的保存
```

**配置管理**：
```javascript
CONFIG = {
  API_BASE_URL: 'http://localhost:1125',
  MAX_RETRY_TIMES: 3,
  RETRY_DELAY: 1000,
  STORAGE_KEY: {
    ARTICLES: 'articles_history',
    SETTINGS: 'scraper_settings',
    STATS: 'scraper_stats'
  }
}
```

**环境特点**：
- 事件驱动（被消息唤醒）
- 无界面（不可见）
- 拥有所有扩展API权限

---

### 4. ✅ Popup（展示/配置层）

**文件**：`popup.html` + `popup.js`

**职责**：
- ✅ 用户界面展示
- ✅ 配置管理（API地址设置）
- ✅ 统计信息展示
- ✅ 历史记录查看
- ✅ 服务器状态监控

**三个标签页**：
1. **提取标签页**
   - 提取当前文章按钮
   - 提取进度显示
   - 内容预览

2. **历史标签页**
   - 显示最近50条历史记录
   - 文章标题、段落数、保存时间

3. **设置标签页**
   - API地址配置
   - 测试连接功能
   - 保存设置

**实时状态**：
- 服务器在线/离线状态
- 已保存文章总数
- 每30秒自动检查服务器状态

**环境特点**：
- 独立的小型网页
- 拥有DOM + 扩展API
- 用户点击图标才显示

---

## 数据流向图

```
用户操作 (Popup UI)
    ↓
    | chrome.runtime.sendMessage
    ↓
Background Service Worker (消息路由)
    ↓
    | chrome.tabs.sendMessage
    ↓
Content Script (DOM提取)
    ↓
    | 返回数据
    ↓
Background (数据处理)
    ↓
    | fetch API
    ↓
Flask后端服务 (保存JSON)
    ↓
    | 返回结果
    ↓
Background (更新状态)
    ↓
    | chrome.storage
    ↓
持久化存储
    ↓
    | 通知Popup
    ↓
Popup显示结果
```

---

## 消息通信机制

### 1. Popup → Background
```javascript
// Popup发送
chrome.runtime.sendMessage({
  action: 'extractContent'
}, response => {
  console.log(response);
});

// Background接收
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'extractContent') {
    // 处理逻辑
    sendResponse({ success: true, data: {...} });
  }
  return true; // 异步响应
});
```

### 2. Background → Content Script
```javascript
// Background发送
chrome.tabs.sendMessage(tabId, {
  action: 'doExtractContent'
}, response => {
  console.log(response);
});

// Content Script接收
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'doExtractContent') {
    const result = extractArticleContent();
    sendResponse(result);
  }
  return true;
});
```

---

## 状态管理

### Chrome Storage API
使用 `chrome.storage.local` 进行本地持久化存储：

```javascript
// 存储键
STORAGE_KEY = {
  ARTICLES: 'articles_history',    // 文章历史记录（最多50条）
  SETTINGS: 'scraper_settings',    // 用户配置
  STATS: 'scraper_stats'           // 统计信息
}

// 配置内容
settings = {
  autoSave: true,
  apiUrl: 'http://localhost:1125'
}

// 统计信息
stats = {
  totalArticles: 0,
  lastSaveTime: null,
  lastArticleTitle: ''
}
```

---

## 错误处理与重试机制

### 重试策略
```javascript
async function saveToServerWithRetry(apiUrl, articleData, retryCount = 0) {
  try {
    // 尝试保存
    const response = await fetch(`${apiUrl}/save-article`, {...});
    return { success: true, ...result };
  } catch (error) {
    // 递增延迟重试
    if (retryCount < MAX_RETRY_TIMES - 1) {
      await sleep(RETRY_DELAY * (retryCount + 1));
      return saveToServerWithRetry(apiUrl, articleData, retryCount + 1);
    }
    return { success: false, error: error.message };
  }
}
```

**特点**：
- 最多重试3次
- 递增延迟：1秒、2秒、3秒
- 友好的错误提示

---

## 技术栈

### 前端（Chrome Extension）
- **Manifest V3** - 最新扩展标准
- **Service Worker** - 后台事件处理
- **Chrome Storage API** - 状态持久化
- **Chrome Tabs API** - 标签页操作
- **Chrome Runtime API** - 消息通信

### 后端
- **Flask** - Python Web框架
- **Flask-CORS** - 跨域支持
- **JSON** - 数据存储格式

---

## 为什么选择这个架构？

### ✅ 优势

1. **清晰的职责分离**
   - Content Script：只负责DOM
   - Background：只负责业务逻辑
   - Popup：只负责UI展示

2. **强大的扩展性**
   - 易于添加新功能
   - 易于维护和调试
   - 组件独立，互不干扰

3. **可靠的错误处理**
   - 重试机制保证成功率
   - 详细的错误信息反馈
   - 状态持久化防止丢失

4. **优秀的用户体验**
   - 实时状态反馈
   - 历史记录查看
   - 配置灵活可调

### 🎯 适用场景

本架构特别适合：
- ✅ 需要从网页提取数据
- ✅ 需要与后端API交互
- ✅ 需要用户配置管理
- ✅ 需要状态持久化
- ✅ 需要友好的UI界面

### ❌ 不适用场景

本架构**不适合**：
- 需要劫持页面JS变量（需要MAIN world）
- 需要拦截网页请求（需要MAIN world）
- 纯展示类插件（过度设计）

---

## 文件清单

```
rtrsnews/
├── manifest.json          # 扩展配置（添加background和storage权限）
├── background.js          # 🆕 Background Service Worker（控制中心）
├── content.js             # ♻️ Content Script（重构，专注DOM）
├── popup.html             # ♻️ Popup界面（全新设计）
├── popup.js               # ♻️ Popup逻辑（标签页、配置）
├── main.py                # Flask后端服务（不变）
├── requirements.txt       # Python依赖（不变）
├── data/                  # 数据存储目录
├── icon.png               # 图标文件
├── README.md              # 使用文档
└── ARCHITECTURE.md        # 🆕 本文档
```

---

## 版本变更

### v2.0.0（当前版本）- 架构重构

**重大改进**：
- ✅ 新增 Background Service Worker
- ✅ 重构 Content Script
- ✅ 全新 Popup UI设计
- ✅ 添加配置管理
- ✅ 添加历史记录
- ✅ 添加统计信息
- ✅ 添加重试机制
- ✅ 添加状态持久化

### v1.0.0 - 原始版本

**基础功能**：
- ✅ 提取路透社文章
- ✅ 保存到Flask后端

**架构问题**：
- ❌ 没有Background层
- ❌ Popup直接调用fetch
- ❌ 没有状态管理
- ❌ 没有错误重试
- ❌ UI简陋

---

## 后续优化方向

1. **功能增强**
   - 批量提取多篇文章
   - 导出为Markdown/PDF
   - 关键词搜索和过滤

2. **性能优化**
   - 内容缓存机制
   - 懒加载历史记录
   - 分页显示

3. **用户体验**
   - 快捷键支持
   - 自动提取模式
   - 深色模式

4. **数据分析**
   - 提取趋势图表
   - 文章分类统计
   - 热门话题分析

---

## 总结

本项目完全遵循Chrome扩展架构知识库的**标准MVC扩展结构**，实现了：

- ✅ **Content Script（视图层）**：DOM操作和数据采集
- ✅ **Background（控制器）**：业务逻辑和状态管理
- ✅ **Popup（展示层）**：用户界面和配置

这是一个**生产级别**的Chrome扩展架构，具有良好的可维护性、可扩展性和用户体验！

