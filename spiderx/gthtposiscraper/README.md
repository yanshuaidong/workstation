


1、访问页面
2、获取出增仓比例最大的“进攻”品种的3个。
3、入库。



大方向：
1、将获取到的3个增仓比例最大的“进攻”品种的json，存储到news_red_telegraph表中。
2、同时给news_process_tracking表添加一条记录。

链接数据库直接写在py文件代码里面。
# 数据库配置
DB_CONFIG = {
    'host': 'rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'ysd',
    'password': 'Yan1234567',
    'database': 'futures',
    'charset': 'utf8mb4'
}


3个增仓比例最大的“进攻”品种的json格式如下。
{
  "date": "2025-11-21",
  "top3": [
    {
      "date": "2025-11-21",
      "name": "淀粉",
      "family": "谷物",
      "total_buy": 24607,
      "total_ss": 10010,
      "net_position": 14597,
      "net_change": 4897,
      "change_ratio": 19.90084122404194,
      "is_net_long": true,
      "is_increasing": true
    },
    {
      "date": "2025-11-21",
      "name": "低硫油",
      "family": "原油",
      "total_buy": 10010,
      "total_ss": 5573,
      "net_position": 4437,
      "net_change": 1850,
      "change_ratio": 18.48151848151848,
      "is_net_long": true,
      "is_increasing": true
    },
    {
      "date": "2025-11-21",
      "name": "红枣",
      "family": "农副",
      "total_buy": 13135,
      "total_ss": 23841,
      "net_position": -10706,
      "net_change": -3151,
      "change_ratio": 13.21672748626316,
      "is_net_long": false,
      "is_increasing": false
    }
  ]
}

两个表结构如下：






        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_red_telegraph (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                ctime BIGINT UNIQUE NOT NULL,
                title VARCHAR(500) NOT NULL,
                content TEXT NOT NULL,
                ai_analysis MEDIUMTEXT,
                message_score TINYINT UNSIGNED,
                message_label ENUM('hard','soft','unknown') DEFAULT 'unknown',
                message_type VARCHAR(64),
                market_react VARCHAR(255),
                screenshots JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS news_process_tracking (
                id BIGINT AUTO_INCREMENT PRIMARY KEY,
                news_id BIGINT NOT NULL COMMENT '关联news_red_telegraph表的id',
                ctime BIGINT NOT NULL COMMENT '消息创建时间（冗余字段，方便查询）',
                
                -- 第一阶段：标签校验状态
                is_reviewed TINYINT(1) NOT NULL DEFAULT '0' COMMENT '是否已完成标签校验',
                
                -- 第二阶段：定期跟踪状态（4个关键时间节点）
                track_day3_done TINYINT(1) NOT NULL DEFAULT '0' COMMENT '3天跟踪是否完成',
                track_day7_done TINYINT(1) NOT NULL DEFAULT '0' COMMENT '7天跟踪是否完成',
                track_day14_done TINYINT(1) NOT NULL DEFAULT '0' COMMENT '14天跟踪是否完成',
                track_day28_done TINYINT(1) NOT NULL DEFAULT '0' COMMENT '28天跟踪是否完成',
                
                -- 系统字段
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                
                UNIQUE KEY uk_news_id (news_id),
                KEY idx_ctime (ctime),
                KEY idx_review_status (is_reviewed, ctime),
                KEY idx_track_day3 (track_day3_done, ctime),
                KEY idx_track_day7 (track_day7_done, ctime),
                KEY idx_track_day14 (track_day14_done, ctime),
                KEY idx_track_day28 (track_day28_done, ctime)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='消息处理流程跟踪表'
        """)



细则：
1、存储的时候，
title写2025年11月21日（这个标题上的时间是程序运行时间）国泰君安持仓变化日报
举例：2025年11月21日运行：2025年11月21日国泰君安持仓变化日报
2025年11月22日运行：2025年11月22日国泰君安持仓变化日报
content：就是3个增仓比例最大的“进攻”品种的json的字符串。（后端存储字符串，到时候也会相应前端json格式的字符串。前端需要自己解析。）message_score设置为7这个固定值。message_label固定hard。其他都暂时空着。


2、给news_process_tracking添加记录的时候。news_process_tracking是一个跟踪表。仅需要对添加消息后进行添加基本的字段就可以。方便我后续跟踪。

                





这两个表的用途如下：

## 1. `news_red_telegraph` 表（新闻红电报表）
存储新闻的原始数据与 AI 分析结果：
- 基本信息：标题、内容、创建时间（ctime）
- AI 分析：`ai_analysis`（分析文本）
- 消息评分：`message_score`、`message_label`（hard/soft/unknown）
- 消息类型：`message_type`、`market_react`（市场反应）
- 截图：`screenshots`（JSON）

## 2. `news_process_tracking` 表（新闻处理流程跟踪表）
跟踪每条新闻的处理状态，分为两个阶段：

### 第一阶段：标签校验
- `is_reviewed`：是否已完成标签校验

### 第二阶段：定期跟踪（4 个时间节点）
- `track_day3_done`：3 天跟踪是否完成
- `track_day7_done`：7 天跟踪是否完成
- `track_day14_done`：14 天跟踪是否完成
- `track_day28_done`：28 天跟踪是否完成

**关系**：通过 `news_id` 关联 `news_red_telegraph`，每条新闻对应一条跟踪记录，用于管理新闻的处理流程和定期跟踪任务。



国泰君安，2025年11月21日。

1、淀粉：总买入量为24,607手，总卖出量为10,010手，净持仓量为14,597手，较上一交易日增加了4,897手，增幅为19.9%。净多头，建议加多。

2、低硫油：总买入量为10,010手，总卖出量为5,573手，净持仓量为4,437手，较上一交易日增加了1,850手，增幅为18.5%。净多头，建议加多。

3、红枣：总买入量为13,135手，总卖出量为23,841手，净持仓量为-10,706手，较上一交易日减少了3,151手，减幅为13.2%。净空头，建议加空。




算法：

统计规则总结
会被统计的情况（同时满足）：
净持仓绝对值 ≥ 1000
净多（>0）且净增仓 > 0（多头进攻）
净空（<0）且净增仓 < 0（空头进攻）
不会被统计的情况（满足任一）：
净持仓绝对值 < 1000（持仓量太小）
净多但净增仓 ≤ 0（多头撤退）
净空但净增仓 ≥ 0（空头撤退）
净持仓 = 0（多空平衡）
设计意图
只统计“进攻”情况：
净多时，只统计继续增持多头的情况
净空时，只统计继续增持空头的情况
忽略“撤退”和持仓量过小的情况
这样能识别出“在已有方向基础上继续加仓”的信号。



```bash
# 启动
./start_scheduler.sh


# 停止
./stop_scheduler.sh
```


