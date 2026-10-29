# 股票历史数据（已停止采集）

股票数据已改用其他数据源，本目录的 AkShare 采集、定时调度和启停脚本已移除，`database/runall.sh` 和 `database/stopall.sh` 不再管理此任务。

已有的本地 SQLite 数据库 `stock.db` 保留，不在 Git 版本控制中；日志等运行数据未清理。此目录不再自动更新股票数据。
