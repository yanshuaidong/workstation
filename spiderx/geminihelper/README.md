# Gemini Helper

Chrome 扩展，用于自动化向 Gemini AI 提问并保存结果到数据库。

## 项目文件结构

```
geminihelper/
├── manifest.json          # Chrome 扩展配置
├── background.js          # 后台调度器（定时任务，每天6次）
├── content-script.js      # 页面操作脚本（DOM 交互，传递 task_id）
├── popup.html/js          # 弹窗界面
├── popup-ui.js            # UI 渲染模块
├── popup-storage.js       # 存储管理模块
├── main.py                # Flask 后端服务（端口 1124，双写数据库）
├── prompts.json           # 提问配置
└── requirements.txt       # Python 依赖
```

## 功能逻辑

1. 插件定时执行（每天6次：4点、8点、12点、16点、20点、24点）
2. 调用 Flask `/get-tasks` 接口查询本地数据库 crawler.db
3. Flask 筛选未分析任务（analysis_task 表中 is_analyzed=0）
4. 返回任务列表，无任务则跳过，有任务则继续
5. 插件调用 Gemini AI 分析每个任务
6. AI 结果返回 Flask（携带 task_id）
7. Flask 双写数据库：
   - 保存到阿里云 MySQL（news_red_telegraph 和 news_process_tracking 表）
   - 更新本地数据库状态（is_analyzed=1，ai_result=内容）

## 快速开始

1. **安装依赖**：`pip install -r requirements.txt`
2. **启动后端**：`python main.py`
3. **安装扩展**：chrome://extensions/ → 开发者模式 → 加载已解压的扩展程序
4. **使用**：点击扩展图标，点击"启动任务"

## API 接口

- `GET /get-tasks` - 获取本地数据库未分析任务
- `POST /save-result` - 保存 AI 结果并更新任务状态
- `GET /health` - 健康检查
