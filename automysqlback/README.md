# 期货数据更新系统

## 系统概述

这是一个完整的期货数据更新可视化系统，用于从公开接口获取期货合约数据并存储到MySQL数据库中。系统包含前端界面、后端API、数据库存储、定时任务等完整功能。

## 技术架构

### 后端技术栈
- **Flask**: Web框架，端口7002
- **akshare**: 期货数据获取库
- **pandas**: 数据处理
- **PyMySQL**: MySQL数据库连接
- **APScheduler**: 定时任务调度
- **MySQL**: 阿里云RDS数据库

### 前端技术栈
- **Vue 3**: 前端框架
- **Element Plus**: UI组件库
- **Axios**: HTTP请求库

## 数据库设计

### 1. 主连合约表 (contracts_main)
```sql
CREATE TABLE contracts_main (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL UNIQUE COMMENT '合约代码，如cum',
    name VARCHAR(50) NOT NULL COMMENT '合约中文名称，如沪铜主连',
    exchange VARCHAR(20) NOT NULL COMMENT '交易所简称',
    is_active TINYINT(1) DEFAULT 1 COMMENT '是否活跃',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

### 2. 更新运行记录表 (update_runs)
```sql
CREATE TABLE update_runs (
    run_id VARCHAR(50) PRIMARY KEY,
    triggered_by ENUM('manual', 'auto') NOT NULL COMMENT '触发方式',
    scheduled_at TIMESTAMP NULL COMMENT '计划执行时间',
    started_at TIMESTAMP NULL COMMENT '实际开始时间',
    finished_at TIMESTAMP NULL COMMENT '完成时间',
    date_start DATE NOT NULL COMMENT '数据起始日期',
    date_end DATE NOT NULL COMMENT '数据结束日期',
    timeout_ms INT DEFAULT 60000 COMMENT '超时时间(毫秒)',
    concurrency INT DEFAULT 5 COMMENT '并发数',
    is_multithread_on TINYINT(1) DEFAULT 1 COMMENT '是否启用多线程',
    total_contracts INT DEFAULT 0 COMMENT '总合约数',
    success_count INT DEFAULT 0 COMMENT '成功数量',
    fail_count INT DEFAULT 0 COMMENT '失败数量',
    status ENUM('running', 'success', 'failure', 'partial') DEFAULT 'running',
    notes TEXT COMMENT '备注信息'
);
```

### 3. 更新项目明细表 (update_items)
```sql
CREATE TABLE update_items (
    item_id VARCHAR(50) PRIMARY KEY,
    run_id VARCHAR(50) NOT NULL,
    contract_symbol VARCHAR(20) NOT NULL COMMENT '合约代码',
    target_table VARCHAR(50) NOT NULL COMMENT '目标表名',
    started_at TIMESTAMP NULL,
    finished_at TIMESTAMP NULL,
    duration_ms INT DEFAULT 0 COMMENT '耗时(毫秒)',
    status ENUM('success', 'failure', 'running') DEFAULT 'running',
    error_stage ENUM('fetch', 'store', 'timeout', 'unknown') NULL,
    error_message TEXT NULL,
    retry_of_item_id VARCHAR(50) NULL COMMENT '重试的原item_id',
    FOREIGN KEY (run_id) REFERENCES update_runs(run_id) ON DELETE CASCADE
);
```

### 4. 历史数据表 (hist_{symbol})
每个主连合约一张表，表名格式为 `hist_{合约代码}`
```sql
CREATE TABLE hist_{symbol} (
    trade_date DATE PRIMARY KEY COMMENT '交易日期',
    open_price INT NOT NULL COMMENT '开盘价',
    high_price INT NOT NULL COMMENT '最高价',
    low_price INT NOT NULL COMMENT '最低价',
    close_price INT NOT NULL COMMENT '收盘价',
    volume BIGINT NOT NULL DEFAULT 0 COMMENT '成交量',
    open_interest BIGINT NOT NULL DEFAULT 0 COMMENT '持仓量',
    turnover BIGINT NOT NULL DEFAULT 0 COMMENT '成交额',
    price_change INT DEFAULT 0 COMMENT '价格变动',
    change_pct DECIMAL(8,2) DEFAULT 0.00 COMMENT '涨跌幅',
    source_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '数据源时间戳',
    ingest_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '入库时间戳'
);
```

## API接口文档

### 1. 获取公开合约列表
**GET** `/api/contracts/fetch-public`

响应示例：
```json
{
    "code": 0,
    "message": "获取成功",
    "data": {
        "total": 1500,
        "main_contracts": 70,
        "contracts": [...]
    }
}
```

### 2. 更新合约列表
**POST** `/api/contracts/upsert-list`

响应示例：
```json
{
    "code": 0,
    "message": "更新成功",
    "data": {
        "new_count": 5,
        "updated_count": 65,
        "total_processed": 70
    }
}
```

### 3. 批量更新历史数据
**POST** `/api/contracts/update-history`

请求参数：
```json
{
    "symbols": [],
    "date_start": "2025-01-01",
    "date_end": "2025-01-31",
    "timeout_ms": 60000,
    "concurrency": 5,
    "multithread": true,
    "triggered_by": "manual"
}
```

### 4. 重试失败项目
**POST** `/api/runs/retry-item`

请求参数：
```json
{
    "item_id": "item_run_1234567890_cu"
}
```

### 5. 获取运行摘要
**GET** `/api/runs/{run_id}`

### 6. 获取运行明细
**GET** `/api/runs/{run_id}/items?page=1&page_size=20`

### 7. 系统设置
**GET/POST** `/api/settings`

## 前端界面功能

### 1. 全局控制区
- 自动更新开关及时间设置
- 多线程并发控制
- 请求超时设置
- 数据日期范围选择

### 2. 合约列表维护
- 显示上次更新状态
- 手动更新合约列表
- 新增合约自动建表

### 3. 历史数据更新
- 批量更新所有主连历史数据
- 实时显示更新进度
- 单个合约重试功能
- 失败原因详细显示

### 4. 运行摘要
- 显示最近运行统计
- 失败项目批量重试
- 平均耗时统计

## 部署说明

### 1. 安装依赖
```bash
cd automysqlback
pip install -r requirements.txt
```

### 2. 配置数据库
确保数据库连接信息正确：
- 主机：rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com
- 端口：3306
- 数据库：futures
- 用户：ysd
- 密码：Yan1234567

### 3. 启动后端服务
```bash
python app.py
```
服务将在 http://localhost:7002 启动

### 4. 启动前端（在workfront目录）
```bash
npm install
npm run serve
```

## 错误处理与重试机制

### 错误分类
- **fetch**: 数据获取阶段错误（网络、接口异常）
- **store**: 数据存储阶段错误（数据库异常）
- **timeout**: 请求超时错误
- **unknown**: 未知错误

### 重试策略
- 支持单个合约重试
- 支持批量重试失败项目
- 重试记录关联原始记录
- 保持完整的错误追踪链

## 并发与性能

### 并发控制
- 可配置并发数：5/10/15/20
- 多线程开关控制
- 单个请求超时控制
- 线程池资源管理

### 性能优化
- 数据库连接池
- 批量插入优化
- 索引优化
- 分页查询支持

## 定时任务

### 自动更新配置
- 支持每日固定时间自动更新
- 默认更新近30天数据
- 自动更新记录标记为 `triggered_by: auto`
- 定时任务状态监控

## 监控与日志

### 系统监控
- 实时显示系统状态
- 运行进度可视化
- 成功/失败统计
- 平均耗时分析

### 日志记录
- 详细的错误信息记录
- 完整的操作审计
- 性能指标统计
- 可追溯的操作历史

## 可复现实验案例

### 1. 接口超时测试
- 设置较短超时时间（30秒）
- 观察超时错误处理
- 验证重试机制

### 2. 合约不存在测试
- 手动添加不存在的合约代码
- 观察错误分类和处理

### 3. 重复日期覆盖测试
- 多次更新同一日期范围
- 验证upsert机制正确性

### 4. 数据库连接失败测试
- 临时修改数据库配置
- 测试连接失败恢复机制

### 5. 新增品种自动建表测试
- 观察新合约发现时的自动建表功能
- 验证表结构一致性

## 维护建议

1. **定期清理日志表**：建议每月清理超过3个月的运行记录
2. **监控数据库空间**：历史数据表会持续增长，需要定期监控
3. **备份重要配置**：定期备份系统设置和重要配置
4. **性能监控**：关注并发更新时的系统性能
5. **数据验证**：定期验证数据完整性和准确性 