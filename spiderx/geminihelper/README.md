# Gemini Helper

Chrome 扩展，用于自动化向 Gemini AI 提问并保存结果到数据库。

## 功能

- 每天早上 7 点自动执行提问任务
- 支持多个 prompt 批量执行
- 结果自动保存到阿里云 MySQL 数据库和本地文件
- 30 天任务周期，可随时启动/停止

## 项目结构

```
geminihelper/
├── manifest.json          # Chrome 扩展配置
├── background.js          # 后台调度器（定时任务）
├── content-script.js      # 页面操作脚本（DOM 交互）
├── popup.html/js          # 弹窗界面
├── popup-ui.js            # UI 渲染模块
├── popup-storage.js       # 存储管理模块
├── main.py                # Flask 后端服务（端口 1124）
├── prompts.json           # 提问配置
└── requirements.txt       # Python 依赖
```

## 快速开始

1. **安装依赖**：`pip install -r requirements.txt`

2. **启动后端**：`python main.py`（确保运行在 `http://localhost:1124`）

3. **安装扩展**：
   - 打开 `chrome://extensions/`
   - 开启开发者模式
   - 点击"加载已解压的扩展程序"，选择 `geminihelper` 目录

4. **使用**：点击扩展图标，点击"启动任务"即可

## API 接口

- `GET /get-prompts` - 获取待执行的 prompt 列表
- `POST /save-result` - 保存 AI 响应结果
- `GET /health` - 健康检查

## 配置说明

- `prompts.json`：配置提问内容，支持多个 prompt
- 数据库配置：在 `main.py` 中修改 `DB_CONFIG`
- 任务周期：默认 30 天，可在代码中调整
