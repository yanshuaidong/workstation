# Reuters News Scraper

一个用于提取路透社新闻文章内容的 Chrome 浏览器插件，配合 Flask 后端服务保存数据。

## 功能特点

- 🚀 点击按钮即可提取文章内容
- 📝 自动提取所有 `data-testid="paragraph-xx"` 的段落
- 💾 将数据保存为 JSON 文件
- 🌐 支持跨域请求
- 📊 提供文章列表和查询接口

## 项目结构

```
rtrsnews/
├── manifest.json       # Chrome 插件配置文件
├── popup.html          # 插件弹出页面
├── popup.js            # 弹出页面脚本
├── content.js          # 内容脚本（用于提取页面内容）
├── main.py             # Flask 后端服务
├── requirements.txt    # Python 依赖
├── data/               # 数据存储目录（自动创建）
└── README.md           # 项目文档
```

## 安装步骤

### 1. 安装 Python 依赖

```bash
cd spiderx/rtrsnews
pip install -r requirements.txt
```

### 2. 启动 Flask 服务

```bash
python main.py
```

服务将在 `http://localhost:1125` 启动。

### 3. 安装 Chrome 插件

1. 打开 Chrome 浏览器
2. 访问 `chrome://extensions/`
3. 开启右上角的 "开发者模式"
4. 点击 "加载已解压的扩展程序"
5. 选择 `spiderx/rtrsnews` 目录
6. 插件安装完成！

**注意：** 由于插件需要图标文件，你需要准备三个图标文件：
- `icon16.png` (16x16)
- `icon48.png` (48x48)
- `icon128.png` (128x128)

如果没有图标，可以临时注释掉 `manifest.json` 中的 `icons` 和 `action.default_icon` 配置。

## 使用方法

1. 打开路透社新闻文章页面（包含 `data-testid="ArticleBody"` 的页面）
2. 点击浏览器工具栏中的插件图标
3. 在弹出窗口中点击 "提取文章内容" 按钮
4. 插件会自动：
   - 提取所有段落内容
   - 显示预览信息
   - 将数据发送到本地服务器
   - 保存为 JSON 文件

## API 接口

### POST /save-article
保存文章数据

**请求体：**
```json
{
  "url": "文章URL",
  "title": "文章标题",
  "paragraphs": ["段落1", "段落2", ...],
  "timestamp": "ISO时间戳"
}
```

**响应：**
```json
{
  "success": true,
  "message": "文章保存成功",
  "filename": "article_20231203_143025.json",
  "paragraph_count": 15
}
```

### GET /articles
获取所有已保存文章的列表

**响应：**
```json
{
  "success": true,
  "count": 5,
  "articles": [...]
}
```

### GET /article/<filename>
获取指定文章的完整内容

**响应：**
```json
{
  "success": true,
  "article": {...}
}
```

### GET /health
健康检查

**响应：**
```json
{
  "status": "running",
  "message": "Reuters News Scraper API is running"
}
```

## 数据存储

所有提取的文章数据保存在 `data/` 目录下，文件命名格式为：
```
article_YYYYMMDD_HHMMSS.json
```

每个 JSON 文件包含：
- `url`: 文章 URL
- `title`: 文章标题
- `paragraphs`: 段落文本数组
- `paragraph_count`: 段落数量
- `timestamp`: 提取时间
- `saved_at`: 保存时间

## 技术栈

- **前端（插件）**：Chrome Extension Manifest V3
- **后端**：Flask + Flask-CORS
- **数据格式**：JSON

## 注意事项

1. 确保 Flask 服务在使用插件前已启动
2. 插件只在 Reuters 网站（www.reuters.com）上运行
3. 插件只能在包含 `data-testid="ArticleBody"` 的页面上正常工作
4. 需要允许浏览器访问 `http://localhost:1125`

## 故障排查

### 插件无法提取内容
- 检查页面是否包含 `data-testid="ArticleBody"` 元素
- 打开浏览器控制台查看错误信息

### 无法连接到服务器
- 确认 Flask 服务已启动
- 检查端口 1125 是否被占用
- 确认浏览器允许跨域请求

### 插件安装失败
- 确认使用的是 Chrome 浏览器（或基于 Chromium 的浏览器）
- 检查 manifest.json 语法是否正确
- 准备图标文件或临时移除图标配置

## 许可证

MIT License

