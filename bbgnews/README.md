# 📰 Bloomberg News API 拦截器

一个Chrome浏览器扩展插件，用于自动拦截并显示Bloomberg网站的文章列表API响应数据。

## ✨ 功能特点

- 🚀 **自动拦截**: 打开 Bloomberg 页面时自动开始监控，无需手动操作
- 🔄 **双重拦截**: 同时支持 Fetch 和 XMLHttpRequest 请求拦截
- 📦 **精准捕获**: 专门捕获 `/lineup-next/api/stories` 接口的响应数据
- 📊 **格式化展示**: 美观地展示JSON数据，包含拦截时间戳
- 💾 **数据持久化**: 自动保存拦截到的数据，关闭浏览器后仍可查看
- 🎯 **徽章通知**: 成功拦截时插件图标会短暂显示 ✓ 标记
- 🗑️ **一键清除**: 轻松清除已保存的数据

## 安装方法

1. 打开Chrome浏览器，访问 `chrome://extensions/`
2. 开启右上角的"开发者模式"
3. 点击"加载已解压的扩展程序"
4. 选择 `bbgnews` 文件夹
5. 插件安装完成！

## 📖 使用方法

### 快速开始

1. 访问 Bloomberg 网站 (如 https://www.bloomberg.com/latest)
2. 插件会**自动开始拦截**（无需任何操作！）
3. 点击浏览器工具栏上的插件图标查看拦截的数据
4. 如果还没有数据，点击"🔄 刷新页面"按钮，然后等待页面加载完成

### 查看拦截日志

按 F12 打开开发者工具，在 Console 中可以看到：
- 🚀 Bloomberg API拦截器已加载
- ✅ Fetch 和 XHR 拦截器已安装  
- 🎯 拦截到 Bloomberg Stories API
- 📦 API响应数据

## ⚠️ 注意事项

- ✅ 仅在 `bloomberg.com` 域名下工作
- ✅ 需要访问会调用文章列表API的页面（如 `/latest`、`/asia` 等）
- ✅ 数据会保存在本地存储，关闭浏览器后仍然可见
- ✅ 这是开发版插件，仅供个人学习和使用
- ⚠️ 如果修改了代码，需要在 `chrome://extensions/` 页面刷新插件

## 📂 文件说明

- `manifest.json` - 扩展清单文件，配置权限和 Content Scripts
- `popup.html` - 弹出窗口界面
- `popup.js` - 弹出窗口逻辑代码（读取和显示数据）
- `content.js` - **内容脚本**，自动注入到页面中拦截API请求 ⭐
- `background.js` - 后台服务脚本（处理消息和通知）
- `icon.png` - 插件图标（需要自行添加）
- `安装使用说明.md` - 详细的安装和使用指南

## 🔧 技术实现

- ✅ 使用 **Manifest V3** 规范
- ✅ 使用 **Content Scripts** 在 `document_start` 时自动注入
- ✅ 重写 `window.fetch` 和 `XMLHttpRequest` 来拦截API请求
- ✅ 使用 `chrome.storage.local` 存储拦截到的数据
- ✅ 使用 `chrome.storage.onChanged` 监听数据变化，实时更新显示
- ✅ 使用 `chrome.action.setBadgeText` 显示拦截成功的徽章通知

## 📝 拦截的API示例

```
https://www.bloomberg.com/lineup-next/api/stories?types=ARTICLE%2CFEATURE%2CINTERACTIVE%2CLETTER%2CEXPLAINERS&locale=en&pageNumber=1&limit=25
```

返回的数据包含文章列表、标题、作者、发布时间等信息。

## 📄 许可

仅供学习和个人使用。

## 🔗 相关链接

- [Chrome Extension 开发文档](https://developer.chrome.com/docs/extensions/)
- [Manifest V3 迁移指南](https://developer.chrome.com/docs/extensions/migrating/)

