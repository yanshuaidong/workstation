# 爬虫调度器示例

使用 APScheduler 创建定时任务的简单示例。

## 📋 环境准备

### 关于虚拟环境

**重要：** Python 3.12+ 仍可用 pip 安装依赖。虚拟环境**不是必须**，但**强烈推荐**。

**推荐原因：** 依赖隔离、避免冲突、环境可复现。

### 快速开始

```bash
# 方式1：虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt

# 方式2：系统Python
pip3 install apscheduler
```

**注意：** 启动脚本会自动检测并激活虚拟环境（如果存在 `venv/` 或 `.venv/` 目录）。

## 🚀 使用

```bash
# 启动
./start_scheduler.sh

# 停止
./stop_scheduler.sh

# 查看日志
tail -f scheduler.log
```

## 📚 调度配置示例

```python
# Cron方式 - 定时执行
scheduler.add_job(task, 'cron', hour='9', minute=0)           # 每天9点
scheduler.add_job(task, 'cron', hour='9,15', minute=0)        # 每天9点、15点
scheduler.add_job(task, 'cron', day_of_week='mon-fri', hour=9)  # 工作日9点
scheduler.add_job(task, 'cron', day=1, hour=0)                # 每月1号0点

# Interval方式 - 间隔执行
scheduler.add_job(task, 'interval', minutes=30)  # 每30分钟
scheduler.add_job(task, 'interval', hours=2)     # 每2小时
```

## 📝 注意事项

- 虚拟环境推荐但不强制
- 启动脚本会自动检测并激活虚拟环境
- macOS 使用 `caffeinate` 防止休眠
- `.gitignore` 已配置忽略 `venv/`

## 🔗 参考

- [APScheduler文档](https://apscheduler.readthedocs.io/)

