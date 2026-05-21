# 数据库对比报告

生成时间：2026-05-21 14:01:10

---

## 概览

| 指标 | 阿里云 (aliyun) | 腾讯云 (tencent) |
|------|----------------|-----------------|
| 表数量 | 102 | 102 |
| 独有表 | 0 | 0 |
| 共有表 | 102 | 102 |

## 各表详情

---

### contract_list_update_log

- **阿里云**: 1 行 | **腾讯云**: 1 行 | **差额**: 相同

- 引擎: InnoDB | 创建时间: 2025-08-31 17:13:29


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | id                             | int                  | NO    | PRI  | 1          |
  | last_update_time               | timestamp            | YES   |      | None       |
  | update_method                  | enum('manual','auto') | YES   |      | manual     |
  | duration_ms                    | int                  | YES   |      | 0          |
  | status                         | enum('success','failure') | YES   |      | success    |
  | error_message                  | text                 | YES   |      | None       |
  | created_at                     | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | updated_at                     | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前1行):**

```
| id | last_update_time | update_method | duration_ms | status | error_message | created_at | updated_at

| 1 | 2025-11-12 09:16:54 | manual | 26904 | success | NULL | 2025-08-31 17:13:29 | 2025-11-12 09:16:54

```


**腾讯云 示例数据 (前1行):**

```
| id | last_update_time | update_method | duration_ms | status | error_message | created_at | updated_at

| 1 | 2025-11-12 09:16:54 | manual | 26904 | success | NULL | 2025-08-31 17:13:29 | 2025-11-12 09:16:54

```

---

### contracts_main

- **阿里云**: 82 行 | **腾讯云**: 82 行 | **差额**: 相同

- 引擎: InnoDB | 创建时间: 2025-08-31 15:11:44


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | id                             | int                  | NO    | PRI  | None       |
  | symbol                         | varchar(20)          | NO    | UNI  | None       |
  | name                           | varchar(50)          | NO    |      | None       |
  | exchange                       | varchar(20)          | NO    | MUL  | None       |
  | is_active                      | tinyint(1)           | YES   |      | 1          |
  | created_at                     | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | updated_at                     | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| id | symbol | name | exchange | is_active | created_at | updated_at

| 322 | cum | 沪铜主连 | 上期所 | 1 | 2025-11-12 09:16:41 | 2025-11-12 09:16:41

| 323 | alm | 沪铝主连 | 上期所 | 1 | 2025-11-12 09:16:41 | 2025-11-12 09:16:41

| 324 | znm | 沪锌主连 | 上期所 | 1 | 2025-11-12 09:16:41 | 2025-11-12 09:16:41

| 325 | pbm | 沪铅主连 | 上期所 | 1 | 2025-11-12 09:16:41 | 2025-11-12 09:16:41

| 326 | aum | 沪金主连 | 上期所 | 1 | 2025-11-12 09:16:41 | 2025-11-12 09:16:41

```


**腾讯云 示例数据 (前5行):**

```
| id | symbol | name | exchange | is_active | created_at | updated_at

| 322 | cum | 沪铜主连 | 上期所 | 1 | 2025-11-12 09:16:41 | 2025-11-12 09:16:41

| 323 | alm | 沪铝主连 | 上期所 | 1 | 2025-11-12 09:16:41 | 2025-11-12 09:16:41

| 324 | znm | 沪锌主连 | 上期所 | 1 | 2025-11-12 09:16:41 | 2025-11-12 09:16:41

| 325 | pbm | 沪铅主连 | 上期所 | 1 | 2025-11-12 09:16:41 | 2025-11-12 09:16:41

| 326 | aum | 沪金主连 | 上期所 | 1 | 2025-11-12 09:16:41 | 2025-11-12 09:16:41

```

---

### fut_daily_close

- **阿里云**: 10120 行 | **腾讯云**: 10945 行 | **差额**: -825

- 引擎: InnoDB | 创建时间: 2026-04-24 11:10:57


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | variety_id                     | int                  | NO    | PRI  | None       |
  | trade_date                     | date                 | NO    | PRI  | None       |
  | close_price                    | float                | NO    |      | None       |
  | collected_at                   | datetime             | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| variety_id | trade_date | close_price | collected_at

| 1 | 2025-07-22 | 823.0 | 2026-04-20 23:41:09

| 1 | 2025-07-23 | 812.0 | 2026-04-20 23:41:09

| 1 | 2025-07-24 | 811.0 | 2026-04-20 23:41:09

| 1 | 2025-07-25 | 802.5 | 2026-04-20 23:41:09

| 1 | 2025-07-28 | 786.0 | 2026-04-20 23:41:09

```


**腾讯云 示例数据 (前5行):**

```
| variety_id | trade_date | close_price | collected_at

| 1 | 2025-07-22 | 823.0 | 2026-04-20 23:41:09

| 1 | 2025-07-23 | 812.0 | 2026-04-20 23:41:09

| 1 | 2025-07-24 | 811.0 | 2026-04-20 23:41:09

| 1 | 2025-07-25 | 802.5 | 2026-04-20 23:41:09

| 1 | 2025-07-28 | 786.0 | 2026-04-20 23:41:09

```

---

### fut_strength

- **阿里云**: 10120 行 | **腾讯云**: 10945 行 | **差额**: -825

- 引擎: InnoDB | 创建时间: 2026-04-24 11:10:57


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | id                             | bigint               | NO    | PRI  | None       |
  | variety_id                     | int                  | NO    | MUL  | None       |
  | trade_date                     | date                 | NO    | MUL  | None       |
  | main_force                     | float                | YES   |      | None       |
  | retail                         | float                | YES   |      | None       |
  | collected_at                   | datetime             | NO    |      | None       |
```


**阿里云 示例数据 (前5行):**

```
| id | variety_id | trade_date | main_force | retail | collected_at

| 1 | 1 | 2025-07-22 | 45.82 | -29.68 | 2026-04-20 01:07:26

| 2 | 2 | 2025-07-22 | 38.83 | -108.27 | 2026-04-20 01:07:26

| 3 | 3 | 2025-07-22 | 47.48 | -46.56 | 2026-04-20 01:07:26

| 4 | 4 | 2025-07-22 | 26.11 | -12.7 | 2026-04-20 01:07:26

| 5 | 5 | 2025-07-22 | 16.01 | 2.38 | 2026-04-20 01:07:26

```


**腾讯云 示例数据 (前5行):**

```
| id | variety_id | trade_date | main_force | retail | collected_at

| 1 | 1 | 2025-07-22 | 45.82 | -29.68 | 2026-04-20 01:07:26

| 2 | 2 | 2025-07-22 | 38.83 | -108.27 | 2026-04-20 01:07:26

| 3 | 3 | 2025-07-22 | 47.48 | -46.56 | 2026-04-20 01:07:26

| 4 | 4 | 2025-07-22 | 26.11 | -12.7 | 2026-04-20 01:07:26

| 5 | 5 | 2025-07-22 | 16.01 | 2.38 | 2026-04-20 01:07:26

```

---

### fut_variety

- **阿里云**: 55 行 | **腾讯云**: 55 行 | **差额**: 相同

- 引擎: InnoDB | 创建时间: 2026-04-17 15:10:01


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | id                             | int                  | NO    | PRI  | None       |
  | name                           | varchar(50)          | NO    |      | None       |
  | key                            | varchar(20)          | NO    | UNI  | None       |
  | contracts_symbol               | varchar(20)          | YES   |      | None       |
```


**阿里云 示例数据 (前5行):**

```
| id | name | key | contracts_symbol

| 1 | 铁矿石 | im | im

| 2 | 螺纹钢 | rbm | rbm

| 3 | 热卷 | hcm | hcm

| 4 | 锰硅 | smm | SMM

| 5 | 沪铜 | cum | cum

```


**腾讯云 示例数据 (前5行):**

```
| id | name | key | contracts_symbol

| 1 | 铁矿石 | im | im

| 2 | 螺纹钢 | rbm | rbm

| 3 | 热卷 | hcm | hcm

| 4 | 锰硅 | smm | SMM

| 5 | 沪铜 | cum | cum

```

---

### futures_events

- **阿里云**: 33 行 | **腾讯云**: 40 行 | **差额**: -7

- 引擎: InnoDB | 创建时间: 2025-12-21 18:56:13


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | id                             | bigint unsigned      | NO    | PRI  | None       |
  | symbol                         | varchar(20)          | NO    | MUL  | None       |
  | event_date                     | date                 | NO    | MUL  | None       |
  | title                          | varchar(200)         | NO    |      | None       |
  | content                        | text                 | YES   |      | None       |
  | outlook                        | enum('bullish','bearish','uncertain','ranging') | YES   | MUL  | None       |
  | strength                       | tinyint unsigned     | YES   |      | None       |
  | created_at                     | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | updated_at                     | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| id | symbol | event_date | title | content | outlook | strength | created_at | updated_at

| 5 | pxm | 2025-12-19 | 供少 | 结论先行：今日TOP10异动更偏“结构性行情”而非单一宏观突发——上行集中在芳烃 | bullish | 8 | 2025-12-21 20:02:11 | 2025-12-21 20:16:37

| 7 | ecm | 2025-12-22 | 红海异动 | [欧线集运主连 ECM]：红海/苏伊士航线“重返”仍不确定，叠加以色列方面再度释 | bullish | 9 | 2025-12-22 20:58:08 | 2025-12-22 21:07:08

| 8 | tam | 2025-12-22 | 低库存+减产 | [PTA主连 TAM]：聚酯链继续走强，核心在于PX/PTA库存处于近三年低位、 | bullish | 8 | 2025-12-22 21:01:22 | 2025-12-22 21:01:22

| 9 | aum | 2025-12-22 | 降息 | 美联储进一步降息预期 + 避险需求 + 美元走弱，并提到市场在交易“2026年两 | bullish | 7 | 2025-12-22 21:11:02 | 2025-12-22 21:11:02

| 10 | aum | 2025-12-23 | 降息 | ▶ 核心驱动：
全球金价创新高（资金涌入避险资产）→ 传导至国内贵金属定价 →  | bullish | 7 | 2025-12-23 20:06:04 | 2025-12-23 20:22:22

```


**腾讯云 示例数据 (前5行):**

```
| id | symbol | event_date | title | content | outlook | strength | created_at | updated_at

| 5 | pxm | 2025-12-19 | 供少 | 结论先行：今日TOP10异动更偏“结构性行情”而非单一宏观突发——上行集中在芳烃 | bullish | 8 | 2025-12-21 20:02:11 | 2025-12-21 20:16:37

| 7 | ecm | 2025-12-22 | 红海异动 | [欧线集运主连 ECM]：红海/苏伊士航线“重返”仍不确定，叠加以色列方面再度释 | bullish | 9 | 2025-12-22 20:58:08 | 2025-12-22 21:07:08

| 8 | tam | 2025-12-22 | 低库存+减产 | [PTA主连 TAM]：聚酯链继续走强，核心在于PX/PTA库存处于近三年低位、 | bullish | 8 | 2025-12-22 21:01:22 | 2025-12-22 21:01:22

| 9 | aum | 2025-12-22 | 降息 | 美联储进一步降息预期 + 避险需求 + 美元走弱，并提到市场在交易“2026年两 | bullish | 7 | 2025-12-22 21:11:02 | 2025-12-22 21:11:02

| 10 | aum | 2025-12-23 | 降息 | ▶ 核心驱动：
全球金价创新高（资金涌入避险资产）→ 传导至国内贵金属定价 →  | bullish | 7 | 2025-12-23 20:06:04 | 2025-12-23 20:22:22

```

---

### futures_positions

- **阿里云**: 2 行 | **腾讯云**: 2 行 | **差额**: 相同

- 引擎: InnoDB | 创建时间: 2025-12-07 18:35:49


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | id                             | bigint unsigned      | NO    | PRI  | None       |
  | symbol                         | varchar(64)          | NO    | MUL  | None       |
  | direction                      | varchar(64)          | NO    | MUL  | None       |
  | status                         | tinyint unsigned     | NO    | MUL  | 1          |
  | created_at                     | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | updated_at                     | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前2行):**

```
| id | symbol | direction | status | created_at | updated_at

| 6 | 镍 | LONG | 1 | 2026-01-05 21:23:24 | 2026-01-05 21:23:24

| 7 | 焦煤 | 多 | 1 | 2026-01-05 21:23:35 | 2026-02-07 15:55:00

```


**腾讯云 示例数据 (前2行):**

```
| id | symbol | direction | status | created_at | updated_at

| 6 | 镍 | LONG | 1 | 2026-01-05 21:23:24 | 2026-01-05 21:23:24

| 7 | 焦煤 | 多 | 1 | 2026-01-05 21:23:35 | 2026-02-07 15:55:00

```

---

### hist_adm

- **阿里云**: 240 行 | **腾讯云**: 254 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:07


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-05-06 | 20875.00 | 20875.00 | 20730.00 | 20735.00 | 803 | 17424 | 167010600.00 | -205.00 | -0.98 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:18:54 | 2025-12-09 22:20:30

| 2025-05-07 | 20875.00 | 20875.00 | 20730.00 | 20745.00 | 809 | 17419 | 168255050.00 | -195.00 | -0.93 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:20:48 | 2025-12-09 22:20:48

| 2025-05-08 | 20875.00 | 20875.00 | 20730.00 | 20750.00 | 814 | 17420 | 169292350.00 | -190.00 | -0.91 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:07 | 2025-12-09 22:21:07

| 2025-05-09 | 20875.00 | 20875.00 | 20730.00 | 20750.00 | 835 | 17431 | 173649050.00 | -190.00 | -0.91 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:25 | 2025-12-09 22:21:25

| 2025-05-12 | 20875.00 | 20875.00 | 20730.00 | 20750.00 | 839 | 17431 | 174478950.00 | -190.00 | -0.91 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:43 | 2025-12-09 22:21:43

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-05-06 | 20875.00 | 20875.00 | 20730.00 | 20735.00 | 803 | 17424 | 167010600.00 | -205.00 | -0.98 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:18:54 | 2025-12-09 22:20:30

| 2025-05-07 | 20875.00 | 20875.00 | 20730.00 | 20745.00 | 809 | 17419 | 168255050.00 | -195.00 | -0.93 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:20:48 | 2025-12-09 22:20:48

| 2025-05-08 | 20875.00 | 20875.00 | 20730.00 | 20750.00 | 814 | 17420 | 169292350.00 | -190.00 | -0.91 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:07 | 2025-12-09 22:21:07

| 2025-05-09 | 20875.00 | 20875.00 | 20730.00 | 20750.00 | 835 | 17431 | 173649050.00 | -190.00 | -0.91 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:25 | 2025-12-09 22:21:25

| 2025-05-12 | 20875.00 | 20875.00 | 20730.00 | 20750.00 | 839 | 17431 | 174478950.00 | -190.00 | -0.91 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:43 | 2025-12-09 22:21:43

```

---

### hist_agm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:07


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 7506.00 | 7627.00 | 7502.00 | 7614.00 | 260072 | 221998 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:21 | 2025-12-09 23:26:21

| 2025-01-03 | 7631.00 | 7678.00 | 7596.00 | 7637.00 | 440188 | 211062 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:21 | 2025-12-09 23:26:21

| 2025-01-06 | 7684.00 | 7715.00 | 7595.00 | 7611.00 | 523396 | 199581 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:21 | 2025-12-09 23:26:21

| 2025-01-07 | 7770.00 | 7778.00 | 7619.00 | 7733.00 | 656966 | 192811 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:21 | 2025-12-09 23:26:21

| 2025-01-08 | 7788.00 | 7797.00 | 7723.00 | 7759.00 | 295994 | 197677 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:21 | 2025-12-09 23:26:21

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 7506.00 | 7627.00 | 7502.00 | 7614.00 | 260072 | 221998 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:21 | 2025-12-09 23:26:21

| 2025-01-03 | 7631.00 | 7678.00 | 7596.00 | 7637.00 | 440188 | 211062 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:21 | 2025-12-09 23:26:21

| 2025-01-06 | 7684.00 | 7715.00 | 7595.00 | 7611.00 | 523396 | 199581 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:21 | 2025-12-09 23:26:21

| 2025-01-07 | 7770.00 | 7778.00 | 7619.00 | 7733.00 | 656966 | 192811 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:21 | 2025-12-09 23:26:21

| 2025-01-08 | 7788.00 | 7797.00 | 7723.00 | 7759.00 | 295994 | 197677 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:21 | 2025-12-09 23:26:21

```

---

### hist_alm

- **阿里云**: 324 行 | **腾讯云**: 338 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:07


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 19850.00 | 19985.00 | 19790.00 | 19945.00 | 97834 | 151307 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:27 | 2025-12-09 23:24:27

| 2025-01-03 | 19920.00 | 20025.00 | 19780.00 | 19840.00 | 145858 | 139756 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:27 | 2025-12-09 23:24:27

| 2025-01-06 | 19780.00 | 19815.00 | 19530.00 | 19565.00 | 159939 | 146619 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:27 | 2025-12-09 23:24:27

| 2025-01-07 | 19630.00 | 19725.00 | 19615.00 | 19680.00 | 100814 | 138996 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:27 | 2025-12-09 23:24:27

| 2025-01-08 | 19800.00 | 19820.00 | 19715.00 | 19745.00 | 65503 | 145733 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:27 | 2025-12-09 23:24:27

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 19850.00 | 19985.00 | 19790.00 | 19945.00 | 97834 | 151307 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:27 | 2025-12-09 23:24:27

| 2025-01-03 | 19920.00 | 20025.00 | 19780.00 | 19840.00 | 145858 | 139756 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:27 | 2025-12-09 23:24:27

| 2025-01-06 | 19780.00 | 19815.00 | 19530.00 | 19565.00 | 159939 | 146619 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:27 | 2025-12-09 23:24:27

| 2025-01-07 | 19630.00 | 19725.00 | 19615.00 | 19680.00 | 100814 | 138996 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:27 | 2025-12-09 23:24:27

| 2025-01-08 | 19800.00 | 19820.00 | 19715.00 | 19745.00 | 65503 | 145733 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:27 | 2025-12-09 23:24:27

```

---

### hist_am

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:07


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 3929.00 | 3962.00 | 3920.00 | 3931.00 | 86643 | 183331 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:41 | 2025-12-09 23:27:41

| 2025-01-03 | 3942.00 | 3944.00 | 3909.00 | 3917.00 | 104354 | 180381 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:41 | 2025-12-09 23:27:41

| 2025-01-06 | 3910.00 | 3919.00 | 3873.00 | 3892.00 | 152269 | 176065 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:41 | 2025-12-09 23:27:41

| 2025-01-07 | 3901.00 | 3906.00 | 3829.00 | 3848.00 | 153748 | 179825 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:41 | 2025-12-09 23:27:41

| 2025-01-08 | 3847.00 | 3851.00 | 3825.00 | 3837.00 | 89960 | 176435 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:41 | 2025-12-09 23:27:41

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 3929.00 | 3962.00 | 3920.00 | 3931.00 | 86643 | 183331 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:41 | 2025-12-09 23:27:41

| 2025-01-03 | 3942.00 | 3944.00 | 3909.00 | 3917.00 | 104354 | 180381 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:41 | 2025-12-09 23:27:41

| 2025-01-06 | 3910.00 | 3919.00 | 3873.00 | 3892.00 | 152269 | 176065 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:41 | 2025-12-09 23:27:41

| 2025-01-07 | 3901.00 | 3906.00 | 3829.00 | 3848.00 | 153748 | 179825 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:41 | 2025-12-09 23:27:41

| 2025-01-08 | 3847.00 | 3851.00 | 3825.00 | 3837.00 | 89960 | 176435 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:41 | 2025-12-09 23:27:41

```

---

### hist_aom

- **阿里云**: 324 行 | **腾讯云**: 338 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:08


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 4755.00 | 4780.00 | 4679.00 | 4700.00 | 110730 | 128328 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:52 | 2025-12-09 23:26:52

| 2025-01-03 | 4688.00 | 4688.00 | 4368.00 | 4402.00 | 309910 | 112157 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:52 | 2025-12-09 23:26:52

| 2025-01-06 | 4397.00 | 4397.00 | 4250.00 | 4254.00 | 270600 | 109433 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:52 | 2025-12-09 23:26:52

| 2025-01-07 | 4280.00 | 4344.00 | 4194.00 | 4294.00 | 212995 | 104209 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:52 | 2025-12-09 23:26:52

| 2025-01-08 | 4278.00 | 4312.00 | 4095.00 | 4128.00 | 237088 | 103849 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:52 | 2025-12-09 23:26:52

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 4755.00 | 4780.00 | 4679.00 | 4700.00 | 110730 | 128328 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:52 | 2025-12-09 23:26:52

| 2025-01-03 | 4688.00 | 4688.00 | 4368.00 | 4402.00 | 309910 | 112157 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:52 | 2025-12-09 23:26:52

| 2025-01-06 | 4397.00 | 4397.00 | 4250.00 | 4254.00 | 270600 | 109433 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:52 | 2025-12-09 23:26:52

| 2025-01-07 | 4280.00 | 4344.00 | 4194.00 | 4294.00 | 212995 | 104209 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:52 | 2025-12-09 23:26:52

| 2025-01-08 | 4278.00 | 4312.00 | 4095.00 | 4128.00 | 237088 | 103849 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:52 | 2025-12-09 23:26:52

```

---

### hist_apm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:08


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 7090.00 | 7115.00 | 7029.00 | 7080.00 | 69017 | 106997 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:06 | 2025-12-09 23:34:06

| 2025-01-03 | 7080.00 | 7096.00 | 6723.00 | 6884.00 | 220503 | 134690 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:06 | 2025-12-09 23:34:06

| 2025-01-06 | 6900.00 | 7048.00 | 6900.00 | 6935.00 | 135161 | 112813 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:06 | 2025-12-09 23:34:06

| 2025-01-07 | 6981.00 | 6994.00 | 6910.00 | 6939.00 | 69696 | 108588 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:06 | 2025-12-09 23:34:06

| 2025-01-08 | 6930.00 | 6942.00 | 6733.00 | 6782.00 | 105351 | 118231 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:06 | 2025-12-09 23:34:06

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 7090.00 | 7115.00 | 7029.00 | 7080.00 | 69017 | 106997 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:06 | 2025-12-09 23:34:06

| 2025-01-03 | 7080.00 | 7096.00 | 6723.00 | 6884.00 | 220503 | 134690 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:06 | 2025-12-09 23:34:06

| 2025-01-06 | 6900.00 | 7048.00 | 6900.00 | 6935.00 | 135161 | 112813 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:06 | 2025-12-09 23:34:06

| 2025-01-07 | 6981.00 | 6994.00 | 6910.00 | 6939.00 | 69696 | 108588 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:06 | 2025-12-09 23:34:06

| 2025-01-08 | 6930.00 | 6942.00 | 6733.00 | 6782.00 | 105351 | 118231 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:06 | 2025-12-09 23:34:06

```

---

### hist_aum

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:08


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 623.44 | 625.80 | 622.98 | 624.14 | 40001 | 138525 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:11 | 2025-12-09 23:26:11

| 2025-01-03 | 627.04 | 630.16 | 625.00 | 629.22 | 85643 | 143601 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:11 | 2025-12-09 23:26:11

| 2025-01-06 | 630.00 | 630.38 | 625.74 | 626.20 | 89184 | 142162 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:11 | 2025-12-09 23:26:11

| 2025-01-07 | 628.00 | 628.24 | 620.40 | 626.20 | 121750 | 144412 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:11 | 2025-12-09 23:26:11

| 2025-01-08 | 628.58 | 629.84 | 626.12 | 629.20 | 96480 | 144703 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:11 | 2025-12-09 23:26:11

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 623.44 | 625.80 | 622.98 | 624.14 | 40001 | 138525 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:11 | 2025-12-09 23:26:11

| 2025-01-03 | 627.04 | 630.16 | 625.00 | 629.22 | 85643 | 143601 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:11 | 2025-12-09 23:26:11

| 2025-01-06 | 630.00 | 630.38 | 625.74 | 626.20 | 89184 | 142162 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:11 | 2025-12-09 23:26:11

| 2025-01-07 | 628.00 | 628.24 | 620.40 | 626.20 | 121750 | 144412 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:11 | 2025-12-09 23:26:11

| 2025-01-08 | 628.58 | 629.84 | 626.12 | 629.20 | 96480 | 144703 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:11 | 2025-12-09 23:26:11

```

---

### hist_bbm

- **阿里云**: 271 行 | **腾讯云**: 283 行 | **差额**: -12

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:08


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 168.00 | 168.00 | 158.45 | 165.05 | 8 | 10 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:59 | 2025-12-09 23:29:59

| 2025-01-03 | 159.20 | 161.95 | 159.20 | 161.95 | 3 | 12 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:59 | 2025-12-09 23:29:59

| 2025-01-06 | 155.15 | 161.45 | 155.15 | 161.45 | 2 | 11 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:59 | 2025-12-09 23:29:59

| 2025-01-07 | 158.40 | 158.40 | 158.40 | 158.40 | 1 | 11 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:59 | 2025-12-09 23:29:59

| 2025-01-08 | 158.35 | 158.35 | 154.10 | 154.10 | 2 | 12 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:59 | 2025-12-09 23:29:59

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 168.00 | 168.00 | 158.45 | 165.05 | 8 | 10 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:59 | 2025-12-09 23:29:59

| 2025-01-03 | 159.20 | 161.95 | 159.20 | 161.95 | 3 | 12 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:59 | 2025-12-09 23:29:59

| 2025-01-06 | 155.15 | 161.45 | 155.15 | 161.45 | 2 | 11 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:59 | 2025-12-09 23:29:59

| 2025-01-07 | 158.40 | 158.40 | 158.40 | 158.40 | 1 | 11 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:59 | 2025-12-09 23:29:59

| 2025-01-08 | 158.35 | 158.35 | 154.10 | 154.10 | 2 | 12 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:59 | 2025-12-09 23:29:59

```

---

### hist_bcm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:08


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 64910.00 | 64930.00 | 64570.00 | 64810.00 | 4399 | 7237 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:58 | 2025-12-09 23:35:58

| 2025-01-03 | 64560.00 | 64890.00 | 64330.00 | 64500.00 | 7868 | 7356 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:58 | 2025-12-09 23:35:58

| 2025-01-06 | 64660.00 | 65640.00 | 64660.00 | 65180.00 | 8391 | 6391 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:58 | 2025-12-09 23:35:58

| 2025-01-07 | 66390.00 | 66390.00 | 65710.00 | 66070.00 | 9769 | 5554 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:58 | 2025-12-09 23:35:58

| 2025-01-08 | 66260.00 | 66260.00 | 65930.00 | 66160.00 | 5903 | 5095 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:58 | 2025-12-09 23:35:58

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 64910.00 | 64930.00 | 64570.00 | 64810.00 | 4399 | 7237 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:58 | 2025-12-09 23:35:58

| 2025-01-03 | 64560.00 | 64890.00 | 64330.00 | 64500.00 | 7868 | 7356 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:58 | 2025-12-09 23:35:58

| 2025-01-06 | 64660.00 | 65640.00 | 64660.00 | 65180.00 | 8391 | 6391 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:58 | 2025-12-09 23:35:58

| 2025-01-07 | 66390.00 | 66390.00 | 65710.00 | 66070.00 | 9769 | 5554 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:58 | 2025-12-09 23:35:58

| 2025-01-08 | 66260.00 | 66260.00 | 65930.00 | 66160.00 | 5903 | 5095 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:58 | 2025-12-09 23:35:58

```

---

### hist_bm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:08


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 3360.00 | 3398.00 | 3353.00 | 3357.00 | 112266 | 116305 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:55 | 2025-12-09 23:27:55

| 2025-01-03 | 3350.00 | 3371.00 | 3300.00 | 3311.00 | 131041 | 118016 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:55 | 2025-12-09 23:27:55

| 2025-01-06 | 3302.00 | 3334.00 | 3264.00 | 3301.00 | 143439 | 118366 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:55 | 2025-12-09 23:27:55

| 2025-01-07 | 3319.00 | 3322.00 | 3235.00 | 3263.00 | 133987 | 123264 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:55 | 2025-12-09 23:27:55

| 2025-01-08 | 3261.00 | 3284.00 | 3243.00 | 3249.00 | 99234 | 124967 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:55 | 2025-12-09 23:27:55

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 3360.00 | 3398.00 | 3353.00 | 3357.00 | 112266 | 116305 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:55 | 2025-12-09 23:27:55

| 2025-01-03 | 3350.00 | 3371.00 | 3300.00 | 3311.00 | 131041 | 118016 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:55 | 2025-12-09 23:27:55

| 2025-01-06 | 3302.00 | 3334.00 | 3264.00 | 3301.00 | 143439 | 118366 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:55 | 2025-12-09 23:27:55

| 2025-01-07 | 3319.00 | 3322.00 | 3235.00 | 3263.00 | 133987 | 123264 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:55 | 2025-12-09 23:27:55

| 2025-01-08 | 3261.00 | 3284.00 | 3243.00 | 3249.00 | 99234 | 124967 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:55 | 2025-12-09 23:27:55

```

---

### hist_brm

- **阿里云**: 324 行 | **腾讯云**: 338 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:08


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 13000.00 | 13265.00 | 13000.00 | 13160.00 | 33517 | 59813 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:02 | 2025-12-09 23:27:02

| 2025-01-03 | 13195.00 | 13385.00 | 12875.00 | 13330.00 | 95581 | 61964 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:02 | 2025-12-09 23:27:02

| 2025-01-06 | 13240.00 | 13555.00 | 13205.00 | 13485.00 | 78072 | 61508 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:02 | 2025-12-09 23:27:02

| 2025-01-07 | 13630.00 | 13790.00 | 13520.00 | 13730.00 | 86109 | 67947 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:02 | 2025-12-09 23:27:02

| 2025-01-08 | 13750.00 | 13765.00 | 13470.00 | 13510.00 | 75812 | 67243 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:03 | 2025-12-09 23:27:03

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 13000.00 | 13265.00 | 13000.00 | 13160.00 | 33517 | 59813 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:02 | 2025-12-09 23:27:02

| 2025-01-03 | 13195.00 | 13385.00 | 12875.00 | 13330.00 | 95581 | 61964 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:02 | 2025-12-09 23:27:02

| 2025-01-06 | 13240.00 | 13555.00 | 13205.00 | 13485.00 | 78072 | 61508 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:02 | 2025-12-09 23:27:02

| 2025-01-07 | 13630.00 | 13790.00 | 13520.00 | 13730.00 | 86109 | 67947 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:02 | 2025-12-09 23:27:02

| 2025-01-08 | 13750.00 | 13765.00 | 13470.00 | 13510.00 | 75812 | 67243 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:03 | 2025-12-09 23:27:03

```

---

### hist_bum

- **阿里云**: 324 行 | **腾讯云**: 338 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:08


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 3720.00 | 3735.00 | 3673.00 | 3692.00 | 106801 | 240734 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:20 | 2025-12-09 23:25:20

| 2025-01-03 | 3722.00 | 3730.00 | 3694.00 | 3702.00 | 124336 | 252522 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:20 | 2025-12-09 23:25:20

| 2025-01-06 | 3694.00 | 3711.00 | 3635.00 | 3638.00 | 151246 | 239411 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:20 | 2025-12-09 23:25:20

| 2025-01-07 | 3657.00 | 3661.00 | 3599.00 | 3603.00 | 142831 | 232698 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:20 | 2025-12-09 23:25:20

| 2025-01-08 | 3615.00 | 3638.00 | 3580.00 | 3615.00 | 219123 | 243165 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:20 | 2025-12-09 23:25:20

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 3720.00 | 3735.00 | 3673.00 | 3692.00 | 106801 | 240734 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:20 | 2025-12-09 23:25:20

| 2025-01-03 | 3722.00 | 3730.00 | 3694.00 | 3702.00 | 124336 | 252522 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:20 | 2025-12-09 23:25:20

| 2025-01-06 | 3694.00 | 3711.00 | 3635.00 | 3638.00 | 151246 | 239411 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:20 | 2025-12-09 23:25:20

| 2025-01-07 | 3657.00 | 3661.00 | 3599.00 | 3603.00 | 142831 | 232698 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:20 | 2025-12-09 23:25:20

| 2025-01-08 | 3615.00 | 3638.00 | 3580.00 | 3615.00 | 219123 | 243165 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:20 | 2025-12-09 23:25:20

```

---

### hist_bzm

- **阿里云**: 220 行 | **腾讯云**: 234 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-11-12 09:16:43


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-05-06 | 5492.00 | 5503.00 | 5428.00 | 5436.00 | 6875 | 22569 | 1125759984.00 | -84.00 | -1.52 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:20:38 | 2025-12-09 22:20:38

| 2025-05-07 | 5492.00 | 5503.00 | 5428.00 | 5438.00 | 6881 | 22572 | 1126738800.00 | -82.00 | -1.49 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:20:56 | 2025-12-09 22:20:56

| 2025-05-08 | 5492.00 | 5503.00 | 5428.00 | 5439.00 | 6888 | 22568 | 1127880992.00 | -81.00 | -1.47 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:15 | 2025-12-09 22:21:15

| 2025-05-09 | 5492.00 | 5503.00 | 5428.00 | 5440.00 | 6894 | 22567 | 1128859952.00 | -80.00 | -1.45 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:33 | 2025-12-09 22:21:33

| 2025-05-12 | 5492.00 | 5503.00 | 5428.00 | 5439.00 | 6896 | 22567 | 1129186256.00 | -81.00 | -1.47 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:50 | 2025-12-09 22:21:50

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-05-06 | 5492.00 | 5503.00 | 5428.00 | 5436.00 | 6875 | 22569 | 1125759984.00 | -84.00 | -1.52 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:20:38 | 2025-12-09 22:20:38

| 2025-05-07 | 5492.00 | 5503.00 | 5428.00 | 5438.00 | 6881 | 22572 | 1126738800.00 | -82.00 | -1.49 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:20:56 | 2025-12-09 22:20:56

| 2025-05-08 | 5492.00 | 5503.00 | 5428.00 | 5439.00 | 6888 | 22568 | 1127880992.00 | -81.00 | -1.47 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:15 | 2025-12-09 22:21:15

| 2025-05-09 | 5492.00 | 5503.00 | 5428.00 | 5440.00 | 6894 | 22567 | 1128859952.00 | -80.00 | -1.45 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:33 | 2025-12-09 22:21:33

| 2025-05-12 | 5492.00 | 5503.00 | 5428.00 | 5439.00 | 6896 | 22567 | 1129186256.00 | -81.00 | -1.47 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:50 | 2025-12-09 22:21:50

```

---

### hist_cfm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:08


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 13485.00 | 13555.00 | 13455.00 | 13535.00 | 140235 | 648164 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:23 | 2025-12-09 23:32:23

| 2025-01-03 | 13560.00 | 13600.00 | 13400.00 | 13405.00 | 281386 | 649378 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:23 | 2025-12-09 23:32:23

| 2025-01-06 | 13400.00 | 13445.00 | 13330.00 | 13345.00 | 246382 | 664200 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:23 | 2025-12-09 23:32:23

| 2025-01-07 | 13415.00 | 13500.00 | 13370.00 | 13425.00 | 271779 | 653807 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:23 | 2025-12-09 23:32:23

| 2025-01-08 | 13425.00 | 13475.00 | 13390.00 | 13445.00 | 171237 | 654229 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:23 | 2025-12-09 23:32:23

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 13485.00 | 13555.00 | 13455.00 | 13535.00 | 140235 | 648164 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:23 | 2025-12-09 23:32:23

| 2025-01-03 | 13560.00 | 13600.00 | 13400.00 | 13405.00 | 281386 | 649378 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:23 | 2025-12-09 23:32:23

| 2025-01-06 | 13400.00 | 13445.00 | 13330.00 | 13345.00 | 246382 | 664200 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:23 | 2025-12-09 23:32:23

| 2025-01-07 | 13415.00 | 13500.00 | 13370.00 | 13425.00 | 271779 | 653807 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:23 | 2025-12-09 23:32:23

| 2025-01-08 | 13425.00 | 13475.00 | 13390.00 | 13445.00 | 171237 | 654229 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:23 | 2025-12-09 23:32:23

```

---

### hist_cjm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:09


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 9230.00 | 9300.00 | 9160.00 | 9220.00 | 48485 | 114499 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:16 | 2025-12-09 23:34:16

| 2025-01-03 | 9235.00 | 9235.00 | 9010.00 | 9100.00 | 79039 | 117218 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:16 | 2025-12-09 23:34:16

| 2025-01-06 | 9115.00 | 9175.00 | 9070.00 | 9100.00 | 38126 | 114947 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:16 | 2025-12-09 23:34:16

| 2025-01-07 | 9130.00 | 9130.00 | 9025.00 | 9095.00 | 39505 | 114189 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:16 | 2025-12-09 23:34:16

| 2025-01-08 | 9070.00 | 9120.00 | 9045.00 | 9085.00 | 29426 | 113529 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:16 | 2025-12-09 23:34:16

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 9230.00 | 9300.00 | 9160.00 | 9220.00 | 48485 | 114499 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:16 | 2025-12-09 23:34:16

| 2025-01-03 | 9235.00 | 9235.00 | 9010.00 | 9100.00 | 79039 | 117218 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:16 | 2025-12-09 23:34:16

| 2025-01-06 | 9115.00 | 9175.00 | 9070.00 | 9100.00 | 38126 | 114947 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:16 | 2025-12-09 23:34:16

| 2025-01-07 | 9130.00 | 9130.00 | 9025.00 | 9095.00 | 39505 | 114189 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:16 | 2025-12-09 23:34:16

| 2025-01-08 | 9070.00 | 9120.00 | 9045.00 | 9085.00 | 29426 | 113529 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:16 | 2025-12-09 23:34:16

```

---

### hist_cm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:09


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 2231.00 | 2243.00 | 2226.00 | 2228.00 | 410340 | 1115258 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:28 | 2025-12-09 23:27:28

| 2025-01-03 | 2230.00 | 2236.00 | 2219.00 | 2228.00 | 526813 | 1135305 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:28 | 2025-12-09 23:27:28

| 2025-01-06 | 2224.00 | 2235.00 | 2209.00 | 2228.00 | 600308 | 1176272 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:28 | 2025-12-09 23:27:28

| 2025-01-07 | 2225.00 | 2235.00 | 2215.00 | 2225.00 | 483242 | 1191075 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:28 | 2025-12-09 23:27:28

| 2025-01-08 | 2226.00 | 2234.00 | 2222.00 | 2230.00 | 396767 | 1197450 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:28 | 2025-12-09 23:27:28

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 2231.00 | 2243.00 | 2226.00 | 2228.00 | 410340 | 1115258 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:28 | 2025-12-09 23:27:28

| 2025-01-03 | 2230.00 | 2236.00 | 2219.00 | 2228.00 | 526813 | 1135305 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:28 | 2025-12-09 23:27:28

| 2025-01-06 | 2224.00 | 2235.00 | 2209.00 | 2228.00 | 600308 | 1176272 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:28 | 2025-12-09 23:27:28

| 2025-01-07 | 2225.00 | 2235.00 | 2215.00 | 2225.00 | 483242 | 1191075 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:28 | 2025-12-09 23:27:28

| 2025-01-08 | 2226.00 | 2234.00 | 2222.00 | 2230.00 | 396767 | 1197450 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:27:28 | 2025-12-09 23:27:28

```

---

### hist_csm

- **阿里云**: 324 行 | **腾讯云**: 338 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:09


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 2479.00 | 2486.00 | 2463.00 | 2467.00 | 71717 | 178076 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:37 | 2025-12-09 23:30:37

| 2025-01-03 | 2461.00 | 2466.00 | 2437.00 | 2447.00 | 126779 | 181619 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:37 | 2025-12-09 23:30:37

| 2025-01-06 | 2447.00 | 2463.00 | 2435.00 | 2460.00 | 92804 | 175960 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:37 | 2025-12-09 23:30:37

| 2025-01-07 | 2461.00 | 2471.00 | 2450.00 | 2470.00 | 91950 | 167820 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:37 | 2025-12-09 23:30:37

| 2025-01-08 | 2470.00 | 2484.00 | 2468.00 | 2482.00 | 90966 | 165286 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:37 | 2025-12-09 23:30:37

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 2479.00 | 2486.00 | 2463.00 | 2467.00 | 71717 | 178076 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:37 | 2025-12-09 23:30:37

| 2025-01-03 | 2461.00 | 2466.00 | 2437.00 | 2447.00 | 126779 | 181619 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:37 | 2025-12-09 23:30:37

| 2025-01-06 | 2447.00 | 2463.00 | 2435.00 | 2460.00 | 92804 | 175960 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:37 | 2025-12-09 23:30:37

| 2025-01-07 | 2461.00 | 2471.00 | 2450.00 | 2470.00 | 91950 | 167820 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:37 | 2025-12-09 23:30:37

| 2025-01-08 | 2470.00 | 2484.00 | 2468.00 | 2482.00 | 90966 | 165286 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:37 | 2025-12-09 23:30:37

```

---

### hist_cum

- **阿里云**: 324 行 | **腾讯云**: 339 行 | **差额**: -15

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:09


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 73310.00 | 73440.00 | 73030.00 | 73280.00 | 48466 | 156644 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:17 | 2025-12-09 23:24:17

| 2025-01-03 | 73130.00 | 73360.00 | 72780.00 | 72920.00 | 78918 | 160879 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:17 | 2025-12-09 23:24:17

| 2025-01-06 | 73230.00 | 74130.00 | 73130.00 | 73600.00 | 75358 | 151602 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:17 | 2025-12-09 23:24:17

| 2025-01-07 | 74530.00 | 74680.00 | 74110.00 | 74470.00 | 86609 | 145731 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:17 | 2025-12-09 23:24:17

| 2025-01-08 | 74500.00 | 74580.00 | 74260.00 | 74480.00 | 44907 | 140801 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:17 | 2025-12-09 23:24:17

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 73310.00 | 73440.00 | 73030.00 | 73280.00 | 48466 | 156644 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:17 | 2025-12-09 23:24:17

| 2025-01-03 | 73130.00 | 73360.00 | 72780.00 | 72920.00 | 78918 | 160879 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:17 | 2025-12-09 23:24:17

| 2025-01-06 | 73230.00 | 74130.00 | 73130.00 | 73600.00 | 75358 | 151602 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:17 | 2025-12-09 23:24:17

| 2025-01-07 | 74530.00 | 74680.00 | 74110.00 | 74470.00 | 86609 | 145731 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:17 | 2025-12-09 23:24:17

| 2025-01-08 | 74500.00 | 74580.00 | 74260.00 | 74480.00 | 44907 | 140801 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:17 | 2025-12-09 23:24:17

```

---

### hist_cym

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:09


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 19435.00 | 19460.00 | 19365.00 | 19400.00 | 3210 | 11775 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:56 | 2025-12-09 23:33:56

| 2025-01-03 | 19430.00 | 19470.00 | 19250.00 | 19275.00 | 5252 | 14512 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:56 | 2025-12-09 23:33:56

| 2025-01-06 | 19275.00 | 19300.00 | 19185.00 | 19195.00 | 3882 | 16377 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:56 | 2025-12-09 23:33:56

| 2025-01-07 | 19265.00 | 19335.00 | 19200.00 | 19235.00 | 4077 | 17967 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:56 | 2025-12-09 23:33:56

| 2025-01-08 | 19225.00 | 19285.00 | 19200.00 | 19270.00 | 3000 | 19045 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:56 | 2025-12-09 23:33:56

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 19435.00 | 19460.00 | 19365.00 | 19400.00 | 3210 | 11775 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:56 | 2025-12-09 23:33:56

| 2025-01-03 | 19430.00 | 19470.00 | 19250.00 | 19275.00 | 5252 | 14512 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:56 | 2025-12-09 23:33:56

| 2025-01-06 | 19275.00 | 19300.00 | 19185.00 | 19195.00 | 3882 | 16377 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:56 | 2025-12-09 23:33:56

| 2025-01-07 | 19265.00 | 19335.00 | 19200.00 | 19235.00 | 4077 | 17967 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:56 | 2025-12-09 23:33:56

| 2025-01-08 | 19225.00 | 19285.00 | 19200.00 | 19270.00 | 3000 | 19045 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:56 | 2025-12-09 23:33:56

```

---

### hist_ebm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:09


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 8131.00 | 8230.00 | 8131.00 | 8196.00 | 174729 | 230030 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:07 | 2025-12-09 23:31:07

| 2025-01-03 | 8230.00 | 8259.00 | 8200.00 | 8207.00 | 191344 | 219489 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:07 | 2025-12-09 23:31:07

| 2025-01-06 | 8204.00 | 8276.00 | 8171.00 | 8189.00 | 173584 | 202475 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:07 | 2025-12-09 23:31:07

| 2025-01-07 | 8213.00 | 8225.00 | 8123.00 | 8145.00 | 174855 | 196414 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:08 | 2025-12-09 23:31:08

| 2025-01-08 | 8158.00 | 8160.00 | 8007.00 | 8117.00 | 219697 | 184185 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:08 | 2025-12-09 23:31:08

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 8131.00 | 8230.00 | 8131.00 | 8196.00 | 174729 | 230030 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:07 | 2025-12-09 23:31:07

| 2025-01-03 | 8230.00 | 8259.00 | 8200.00 | 8207.00 | 191344 | 219489 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:07 | 2025-12-09 23:31:07

| 2025-01-06 | 8204.00 | 8276.00 | 8171.00 | 8189.00 | 173584 | 202475 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:07 | 2025-12-09 23:31:07

| 2025-01-07 | 8213.00 | 8225.00 | 8123.00 | 8145.00 | 174855 | 196414 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:08 | 2025-12-09 23:31:08

| 2025-01-08 | 8158.00 | 8160.00 | 8007.00 | 8117.00 | 219697 | 184185 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:08 | 2025-12-09 23:31:08

```

---

### hist_ecm

- **阿里云**: 323 行 | **腾讯云**: 338 行 | **差额**: -15

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:09


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 2269.00 | 2332.90 | 2188.00 | 2224.70 | 28378 | 26812 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:18 | 2025-12-09 23:36:18

| 2025-01-03 | 2218.00 | 2224.40 | 2050.00 | 2131.00 | 32370 | 25810 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:18 | 2025-12-09 23:36:18

| 2025-01-06 | 2109.00 | 2129.20 | 2007.60 | 2032.50 | 23838 | 25477 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:18 | 2025-12-09 23:36:18

| 2025-01-07 | 2013.90 | 2070.00 | 1975.00 | 2026.10 | 23318 | 25100 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:18 | 2025-12-09 23:36:18

| 2025-01-08 | 2041.00 | 2059.60 | 1943.50 | 1980.00 | 21429 | 24879 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:18 | 2025-12-09 23:36:18

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 2269.00 | 2332.90 | 2188.00 | 2224.70 | 28378 | 26812 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:18 | 2025-12-09 23:36:18

| 2025-01-03 | 2218.00 | 2224.40 | 2050.00 | 2131.00 | 32370 | 25810 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:18 | 2025-12-09 23:36:18

| 2025-01-06 | 2109.00 | 2129.20 | 2007.60 | 2032.50 | 23838 | 25477 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:18 | 2025-12-09 23:36:18

| 2025-01-07 | 2013.90 | 2070.00 | 1975.00 | 2026.10 | 23318 | 25100 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:18 | 2025-12-09 23:36:18

| 2025-01-08 | 2041.00 | 2059.60 | 1943.50 | 1980.00 | 21429 | 24879 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:18 | 2025-12-09 23:36:18

```

---

### hist_egm

- **阿里云**: 324 行 | **腾讯云**: 338 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:09


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 4855.00 | 4875.00 | 4822.00 | 4859.00 | 157154 | 332563 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:47 | 2025-12-09 23:30:47

| 2025-01-03 | 4860.00 | 4862.00 | 4720.00 | 4744.00 | 299543 | 285325 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:47 | 2025-12-09 23:30:47

| 2025-01-06 | 4749.00 | 4779.00 | 4703.00 | 4710.00 | 189984 | 273915 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:47 | 2025-12-09 23:30:47

| 2025-01-07 | 4710.00 | 4727.00 | 4685.00 | 4694.00 | 153617 | 275830 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:47 | 2025-12-09 23:30:47

| 2025-01-08 | 4700.00 | 4731.00 | 4690.00 | 4706.00 | 141969 | 273088 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:48 | 2025-12-09 23:30:48

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 4855.00 | 4875.00 | 4822.00 | 4859.00 | 157154 | 332563 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:47 | 2025-12-09 23:30:47

| 2025-01-03 | 4860.00 | 4862.00 | 4720.00 | 4744.00 | 299543 | 285325 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:47 | 2025-12-09 23:30:47

| 2025-01-06 | 4749.00 | 4779.00 | 4703.00 | 4710.00 | 189984 | 273915 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:47 | 2025-12-09 23:30:47

| 2025-01-07 | 4710.00 | 4727.00 | 4685.00 | 4694.00 | 153617 | 275830 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:47 | 2025-12-09 23:30:47

| 2025-01-08 | 4700.00 | 4731.00 | 4690.00 | 4706.00 | 141969 | 273088 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:48 | 2025-12-09 23:30:48

```

---

### hist_fbm

- **阿里云**: 324 行 | **腾讯云**: 338 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:09


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 1315.00 | 1319.50 | 1314.00 | 1315.00 | 96 | 119 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:49 | 2025-12-09 23:29:49

| 2025-01-03 | 1314.00 | 1316.50 | 1313.00 | 1314.00 | 114 | 124 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:49 | 2025-12-09 23:29:49

| 2025-01-06 | 1315.00 | 1324.50 | 1313.00 | 1314.50 | 323 | 156 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:49 | 2025-12-09 23:29:49

| 2025-01-07 | 1314.50 | 1321.50 | 1312.00 | 1318.00 | 297 | 199 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:49 | 2025-12-09 23:29:49

| 2025-01-08 | 1316.50 | 1337.50 | 1316.50 | 1331.00 | 586 | 289 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:49 | 2025-12-09 23:29:49

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 1315.00 | 1319.50 | 1314.00 | 1315.00 | 96 | 119 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:49 | 2025-12-09 23:29:49

| 2025-01-03 | 1314.00 | 1316.50 | 1313.00 | 1314.00 | 114 | 124 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:49 | 2025-12-09 23:29:49

| 2025-01-06 | 1315.00 | 1324.50 | 1313.00 | 1314.50 | 323 | 156 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:49 | 2025-12-09 23:29:49

| 2025-01-07 | 1314.50 | 1321.50 | 1312.00 | 1318.00 | 297 | 199 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:49 | 2025-12-09 23:29:49

| 2025-01-08 | 1316.50 | 1337.50 | 1316.50 | 1331.00 | 586 | 289 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:49 | 2025-12-09 23:29:49

```

---

### hist_fgm

- **阿里云**: 323 行 | **腾讯云**: 338 行 | **差额**: -15

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:10


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 1326.00 | 1347.00 | 1323.00 | 1338.00 | 491619 | 747308 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:16 | 2025-12-09 23:33:16

| 2025-01-03 | 1335.00 | 1346.00 | 1323.00 | 1342.00 | 807114 | 784969 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:16 | 2025-12-09 23:33:16

| 2025-01-06 | 1344.00 | 1362.00 | 1327.00 | 1336.00 | 1159630 | 770757 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:16 | 2025-12-09 23:33:16

| 2025-01-07 | 1344.00 | 1354.00 | 1329.00 | 1335.00 | 756743 | 796285 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:16 | 2025-12-09 23:33:16

| 2025-01-08 | 1332.00 | 1338.00 | 1292.00 | 1294.00 | 1075813 | 872244 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:16 | 2025-12-09 23:33:16

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 1326.00 | 1347.00 | 1323.00 | 1338.00 | 491619 | 747308 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:16 | 2025-12-09 23:33:16

| 2025-01-03 | 1335.00 | 1346.00 | 1323.00 | 1342.00 | 807114 | 784969 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:16 | 2025-12-09 23:33:16

| 2025-01-06 | 1344.00 | 1362.00 | 1327.00 | 1336.00 | 1159630 | 770757 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:16 | 2025-12-09 23:33:16

| 2025-01-07 | 1344.00 | 1354.00 | 1329.00 | 1335.00 | 756743 | 796285 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:16 | 2025-12-09 23:33:16

| 2025-01-08 | 1332.00 | 1338.00 | 1292.00 | 1294.00 | 1075813 | 872244 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:16 | 2025-12-09 23:33:16

```

---

### hist_fum

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:10


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 3342.00 | 3352.00 | 3302.00 | 3306.00 | 374022 | 247944 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:31 | 2025-12-09 23:26:31

| 2025-01-03 | 3340.00 | 3355.00 | 3329.00 | 3329.00 | 528717 | 246968 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:31 | 2025-12-09 23:26:31

| 2025-01-06 | 3346.00 | 3390.00 | 3337.00 | 3346.00 | 574998 | 245800 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:31 | 2025-12-09 23:26:31

| 2025-01-07 | 3366.00 | 3368.00 | 3301.00 | 3324.00 | 563264 | 230657 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:31 | 2025-12-09 23:26:31

| 2025-01-08 | 3335.00 | 3363.00 | 3304.00 | 3353.00 | 641959 | 240648 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:31 | 2025-12-09 23:26:31

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 3342.00 | 3352.00 | 3302.00 | 3306.00 | 374022 | 247944 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:31 | 2025-12-09 23:26:31

| 2025-01-03 | 3340.00 | 3355.00 | 3329.00 | 3329.00 | 528717 | 246968 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:31 | 2025-12-09 23:26:31

| 2025-01-06 | 3346.00 | 3390.00 | 3337.00 | 3346.00 | 574998 | 245800 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:31 | 2025-12-09 23:26:31

| 2025-01-07 | 3366.00 | 3368.00 | 3301.00 | 3324.00 | 563264 | 230657 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:31 | 2025-12-09 23:26:31

| 2025-01-08 | 3335.00 | 3363.00 | 3304.00 | 3353.00 | 641959 | 240648 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:31 | 2025-12-09 23:26:31

```

---

### hist_hcm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:10


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 3413.00 | 3440.00 | 3394.00 | 3424.00 | 387570 | 1023358 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:42 | 2025-12-09 23:26:42

| 2025-01-03 | 3420.00 | 3424.00 | 3365.00 | 3377.00 | 504445 | 1094432 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:42 | 2025-12-09 23:26:42

| 2025-01-06 | 3374.00 | 3397.00 | 3354.00 | 3358.00 | 478148 | 1143090 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:42 | 2025-12-09 23:26:42

| 2025-01-07 | 3375.00 | 3382.00 | 3336.00 | 3343.00 | 376100 | 1160450 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:42 | 2025-12-09 23:26:42

| 2025-01-08 | 3343.00 | 3354.00 | 3311.00 | 3321.00 | 372128 | 1166111 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:42 | 2025-12-09 23:26:42

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 3413.00 | 3440.00 | 3394.00 | 3424.00 | 387570 | 1023358 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:42 | 2025-12-09 23:26:42

| 2025-01-03 | 3420.00 | 3424.00 | 3365.00 | 3377.00 | 504445 | 1094432 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:42 | 2025-12-09 23:26:42

| 2025-01-06 | 3374.00 | 3397.00 | 3354.00 | 3358.00 | 478148 | 1143090 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:42 | 2025-12-09 23:26:42

| 2025-01-07 | 3375.00 | 3382.00 | 3336.00 | 3343.00 | 376100 | 1160450 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:42 | 2025-12-09 23:26:42

| 2025-01-08 | 3343.00 | 3354.00 | 3311.00 | 3321.00 | 372128 | 1166111 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:42 | 2025-12-09 23:26:42

```

---

### hist_icm

- **阿里云**: 233 行 | **腾讯云**: 236 行 | **差额**: -3

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:10


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 5650.00 | 5663.80 | 5426.60 | 5485.20 | 44309 | 108408 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:28 | 2025-12-09 23:36:28

| 2025-01-03 | 5500.00 | 5520.00 | 5361.60 | 5387.60 | 47718 | 111013 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:28 | 2025-12-09 23:36:28

| 2025-01-06 | 5386.00 | 5427.60 | 5338.00 | 5370.20 | 35343 | 105352 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:28 | 2025-12-09 23:36:28

| 2025-01-07 | 5372.20 | 5433.00 | 5349.20 | 5423.00 | 31433 | 105370 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:28 | 2025-12-09 23:36:28

| 2025-01-08 | 5407.60 | 5451.60 | 5260.20 | 5402.80 | 44697 | 109217 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:28 | 2025-12-09 23:36:28

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 5650.00 | 5663.80 | 5426.60 | 5485.20 | 44309 | 108408 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:28 | 2025-12-09 23:36:28

| 2025-01-03 | 5500.00 | 5520.00 | 5361.60 | 5387.60 | 47718 | 111013 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:28 | 2025-12-09 23:36:28

| 2025-01-06 | 5386.00 | 5427.60 | 5338.00 | 5370.20 | 35343 | 105352 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:28 | 2025-12-09 23:36:28

| 2025-01-07 | 5372.20 | 5433.00 | 5349.20 | 5423.00 | 31433 | 105370 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:28 | 2025-12-09 23:36:28

| 2025-01-08 | 5407.60 | 5451.60 | 5260.20 | 5402.80 | 44697 | 109217 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:28 | 2025-12-09 23:36:28

```

---

### hist_ifm

- **阿里云**: 233 行 | **腾讯云**: 235 行 | **差额**: -2

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:10


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 3921.00 | 3931.00 | 3784.40 | 3817.80 | 82958 | 151506 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:38 | 2025-12-09 23:36:38

| 2025-01-03 | 3826.00 | 3834.00 | 3758.00 | 3779.00 | 74342 | 150331 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:38 | 2025-12-09 23:36:38

| 2025-01-06 | 3780.20 | 3785.40 | 3740.80 | 3762.00 | 63581 | 148863 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:38 | 2025-12-09 23:36:38

| 2025-01-07 | 3757.00 | 3793.40 | 3750.00 | 3789.60 | 52260 | 144935 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:38 | 2025-12-09 23:36:38

| 2025-01-08 | 3780.00 | 3810.00 | 3720.60 | 3781.20 | 74894 | 151394 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:38 | 2025-12-09 23:36:38

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 3921.00 | 3931.00 | 3784.40 | 3817.80 | 82958 | 151506 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:38 | 2025-12-09 23:36:38

| 2025-01-03 | 3826.00 | 3834.00 | 3758.00 | 3779.00 | 74342 | 150331 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:38 | 2025-12-09 23:36:38

| 2025-01-06 | 3780.20 | 3785.40 | 3740.80 | 3762.00 | 63581 | 148863 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:38 | 2025-12-09 23:36:38

| 2025-01-07 | 3757.00 | 3793.40 | 3750.00 | 3789.60 | 52260 | 144935 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:38 | 2025-12-09 23:36:38

| 2025-01-08 | 3780.00 | 3810.00 | 3720.60 | 3781.20 | 74894 | 151394 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:38 | 2025-12-09 23:36:38

```

---

### hist_ihm

- **阿里云**: 232 行 | **腾讯云**: 234 行 | **差额**: -2

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:10


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 2680.00 | 2690.00 | 2590.00 | 2619.80 | 33442 | 57740 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:48 | 2025-12-09 23:36:48

| 2025-01-03 | 2625.00 | 2625.00 | 2578.00 | 2592.20 | 26459 | 55653 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:48 | 2025-12-09 23:36:48

| 2025-01-06 | 2592.60 | 2598.00 | 2557.60 | 2580.20 | 23772 | 56036 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:48 | 2025-12-09 23:36:48

| 2025-01-07 | 2582.00 | 2600.20 | 2571.00 | 2596.60 | 19638 | 54348 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:48 | 2025-12-09 23:36:48

| 2025-01-08 | 2587.80 | 2618.00 | 2566.20 | 2598.40 | 28846 | 58592 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:48 | 2025-12-09 23:36:48

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 2680.00 | 2690.00 | 2590.00 | 2619.80 | 33442 | 57740 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:48 | 2025-12-09 23:36:48

| 2025-01-03 | 2625.00 | 2625.00 | 2578.00 | 2592.20 | 26459 | 55653 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:48 | 2025-12-09 23:36:48

| 2025-01-06 | 2592.60 | 2598.00 | 2557.60 | 2580.20 | 23772 | 56036 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:48 | 2025-12-09 23:36:48

| 2025-01-07 | 2582.00 | 2600.20 | 2571.00 | 2596.60 | 19638 | 54348 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:48 | 2025-12-09 23:36:48

| 2025-01-08 | 2587.80 | 2618.00 | 2566.20 | 2598.40 | 28846 | 58592 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:48 | 2025-12-09 23:36:48

```

---

### hist_im

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:10


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 777.00 | 788.00 | 771.00 | 782.00 | 253304 | 390429 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:07 | 2025-12-09 23:30:07

| 2025-01-03 | 782.00 | 783.00 | 760.00 | 764.00 | 374360 | 385498 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:07 | 2025-12-09 23:30:07

| 2025-01-06 | 766.00 | 769.50 | 751.00 | 751.50 | 392284 | 404650 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:07 | 2025-12-09 23:30:07

| 2025-01-07 | 760.00 | 761.00 | 745.50 | 750.00 | 311676 | 406812 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:07 | 2025-12-09 23:30:07

| 2025-01-08 | 753.00 | 756.50 | 743.50 | 747.50 | 300334 | 417474 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:07 | 2025-12-09 23:30:07

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 777.00 | 788.00 | 771.00 | 782.00 | 253304 | 390429 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:07 | 2025-12-09 23:30:07

| 2025-01-03 | 782.00 | 783.00 | 760.00 | 764.00 | 374360 | 385498 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:07 | 2025-12-09 23:30:07

| 2025-01-06 | 766.00 | 769.50 | 751.00 | 751.50 | 392284 | 404650 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:07 | 2025-12-09 23:30:07

| 2025-01-07 | 760.00 | 761.00 | 745.50 | 750.00 | 311676 | 406812 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:07 | 2025-12-09 23:30:07

| 2025-01-08 | 753.00 | 756.50 | 743.50 | 747.50 | 300334 | 417474 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:07 | 2025-12-09 23:30:07

```

---

### hist_imm

- **阿里云**: 232 行 | **腾讯云**: 235 行 | **差额**: -3

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:10


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 5850.20 | 5887.80 | 5638.00 | 5699.40 | 166462 | 168141 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:58 | 2025-12-09 23:36:58

| 2025-01-03 | 5721.00 | 5727.00 | 5529.00 | 5553.40 | 176952 | 172211 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:58 | 2025-12-09 23:36:58

| 2025-01-06 | 5550.80 | 5606.80 | 5490.80 | 5527.20 | 151560 | 168619 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:58 | 2025-12-09 23:36:58

| 2025-01-07 | 5536.00 | 5608.60 | 5496.20 | 5599.00 | 140353 | 166007 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:58 | 2025-12-09 23:36:58

| 2025-01-08 | 5570.00 | 5622.00 | 5402.60 | 5565.40 | 200605 | 180375 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:58 | 2025-12-09 23:36:58

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 5850.20 | 5887.80 | 5638.00 | 5699.40 | 166462 | 168141 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:58 | 2025-12-09 23:36:58

| 2025-01-03 | 5721.00 | 5727.00 | 5529.00 | 5553.40 | 176952 | 172211 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:58 | 2025-12-09 23:36:58

| 2025-01-06 | 5550.80 | 5606.80 | 5490.80 | 5527.20 | 151560 | 168619 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:58 | 2025-12-09 23:36:58

| 2025-01-07 | 5536.00 | 5608.60 | 5496.20 | 5599.00 | 140353 | 166007 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:58 | 2025-12-09 23:36:58

| 2025-01-08 | 5570.00 | 5622.00 | 5402.60 | 5565.40 | 200605 | 180375 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:58 | 2025-12-09 23:36:58

```

---

### hist_jdm

- **阿里云**: 324 行 | **腾讯云**: 338 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:10


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 3368.00 | 3391.00 | 3358.00 | 3376.00 | 66177 | 79236 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:17 | 2025-12-09 23:30:17

| 2025-01-03 | 3364.00 | 3364.00 | 3273.00 | 3287.00 | 125311 | 72942 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:17 | 2025-12-09 23:30:17

| 2025-01-06 | 3257.00 | 3285.00 | 3244.00 | 3270.00 | 67478 | 73620 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:17 | 2025-12-09 23:30:17

| 2025-01-07 | 3270.00 | 3285.00 | 3249.00 | 3273.00 | 64579 | 69368 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:17 | 2025-12-09 23:30:17

| 2025-01-08 | 3204.00 | 3212.00 | 3171.00 | 3208.00 | 49223 | 88637 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:17 | 2025-12-09 23:30:17

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 3368.00 | 3391.00 | 3358.00 | 3376.00 | 66177 | 79236 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:17 | 2025-12-09 23:30:17

| 2025-01-03 | 3364.00 | 3364.00 | 3273.00 | 3287.00 | 125311 | 72942 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:17 | 2025-12-09 23:30:17

| 2025-01-06 | 3257.00 | 3285.00 | 3244.00 | 3270.00 | 67478 | 73620 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:17 | 2025-12-09 23:30:17

| 2025-01-07 | 3270.00 | 3285.00 | 3249.00 | 3273.00 | 64579 | 69368 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:17 | 2025-12-09 23:30:17

| 2025-01-08 | 3204.00 | 3212.00 | 3171.00 | 3208.00 | 49223 | 88637 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:17 | 2025-12-09 23:30:17

```

---

### hist_jm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:11


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 1805.00 | 1843.50 | 1795.00 | 1825.00 | 17372 | 28338 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:23 | 2025-12-09 23:29:23

| 2025-01-03 | 1836.00 | 1836.00 | 1755.00 | 1760.50 | 24244 | 31244 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:24 | 2025-12-09 23:29:24

| 2025-01-06 | 1768.50 | 1774.50 | 1744.00 | 1745.50 | 17164 | 32527 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:24 | 2025-12-09 23:29:24

| 2025-01-07 | 1757.50 | 1763.00 | 1720.00 | 1722.50 | 16446 | 35065 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:24 | 2025-12-09 23:29:24

| 2025-01-08 | 1723.50 | 1729.50 | 1689.50 | 1690.00 | 16357 | 36081 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:24 | 2025-12-09 23:29:24

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 1805.00 | 1843.50 | 1795.00 | 1825.00 | 17372 | 28338 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:23 | 2025-12-09 23:29:23

| 2025-01-03 | 1836.00 | 1836.00 | 1755.00 | 1760.50 | 24244 | 31244 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:24 | 2025-12-09 23:29:24

| 2025-01-06 | 1768.50 | 1774.50 | 1744.00 | 1745.50 | 17164 | 32527 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:24 | 2025-12-09 23:29:24

| 2025-01-07 | 1757.50 | 1763.00 | 1720.00 | 1722.50 | 16446 | 35065 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:24 | 2025-12-09 23:29:24

| 2025-01-08 | 1723.50 | 1729.50 | 1689.50 | 1690.00 | 16357 | 36081 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:24 | 2025-12-09 23:29:24

```

---

### hist_jmm

- **阿里云**: 323 行 | **腾讯云**: 338 行 | **差额**: -15

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:11


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 1162.50 | 1187.50 | 1154.00 | 1174.00 | 174740 | 259254 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:39 | 2025-12-09 23:29:39

| 2025-01-03 | 1174.50 | 1176.50 | 1140.00 | 1148.50 | 212419 | 268507 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:39 | 2025-12-09 23:29:39

| 2025-01-06 | 1144.50 | 1170.00 | 1131.50 | 1156.00 | 206940 | 263786 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:39 | 2025-12-09 23:29:39

| 2025-01-07 | 1162.00 | 1169.50 | 1123.00 | 1128.00 | 210354 | 283622 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:39 | 2025-12-09 23:29:39

| 2025-01-08 | 1132.00 | 1135.00 | 1100.00 | 1103.00 | 227315 | 306145 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:39 | 2025-12-09 23:29:39

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 1162.50 | 1187.50 | 1154.00 | 1174.00 | 174740 | 259254 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:39 | 2025-12-09 23:29:39

| 2025-01-03 | 1174.50 | 1176.50 | 1140.00 | 1148.50 | 212419 | 268507 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:39 | 2025-12-09 23:29:39

| 2025-01-06 | 1144.50 | 1170.00 | 1131.50 | 1156.00 | 206940 | 263786 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:39 | 2025-12-09 23:29:39

| 2025-01-07 | 1162.00 | 1169.50 | 1123.00 | 1128.00 | 210354 | 283622 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:39 | 2025-12-09 23:29:39

| 2025-01-08 | 1132.00 | 1135.00 | 1100.00 | 1103.00 | 227315 | 306145 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:39 | 2025-12-09 23:29:39

```

---

### hist_lcm

- **阿里云**: 323 行 | **腾讯云**: 338 行 | **差额**: -15

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:11


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 77120.00 | 78580.00 | 77120.00 | 77800.00 | 163323 | 183460 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:40 | 2025-12-09 23:37:40

| 2025-01-03 | 77560.00 | 77720.00 | 76000.00 | 76380.00 | 188527 | 188017 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:40 | 2025-12-09 23:37:40

| 2025-01-06 | 76680.00 | 79340.00 | 76600.00 | 77660.00 | 298136 | 183347 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:40 | 2025-12-09 23:37:40

| 2025-01-07 | 77860.00 | 79700.00 | 77000.00 | 78820.00 | 262723 | 204995 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:40 | 2025-12-09 23:37:40

| 2025-01-08 | 78920.00 | 79000.00 | 77080.00 | 77180.00 | 202254 | 195768 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:40 | 2025-12-09 23:37:40

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 77120.00 | 78580.00 | 77120.00 | 77800.00 | 163323 | 183460 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:40 | 2025-12-09 23:37:40

| 2025-01-03 | 77560.00 | 77720.00 | 76000.00 | 76380.00 | 188527 | 188017 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:40 | 2025-12-09 23:37:40

| 2025-01-06 | 76680.00 | 79340.00 | 76600.00 | 77660.00 | 298136 | 183347 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:40 | 2025-12-09 23:37:40

| 2025-01-07 | 77860.00 | 79700.00 | 77000.00 | 78820.00 | 262723 | 204995 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:40 | 2025-12-09 23:37:40

| 2025-01-08 | 78920.00 | 79000.00 | 77080.00 | 77180.00 | 202254 | 195768 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:40 | 2025-12-09 23:37:40

```

---

### hist_lfm

- **阿里云**: 312 行 | **腾讯云**: 324 行 | **差额**: -12

- 引擎: InnoDB | 创建时间: 2025-11-12 09:16:42


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 8188.00 | 8206.00 | 8135.00 | 8164.00 | 291566 | 555395 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:38 | 2025-12-09 23:31:38

| 2025-01-03 | 8164.00 | 8179.00 | 8082.00 | 8083.00 | 404749 | 545046 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:38 | 2025-12-09 23:31:38

| 2025-01-06 | 8080.00 | 8096.00 | 7936.00 | 7943.00 | 574773 | 571299 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:38 | 2025-12-09 23:31:38

| 2025-01-07 | 7956.00 | 7980.00 | 7885.00 | 7893.00 | 414567 | 553584 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:38 | 2025-12-09 23:31:38

| 2025-01-08 | 7903.00 | 7925.00 | 7856.00 | 7867.00 | 325698 | 533648 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:38 | 2025-12-09 23:31:38

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 8188.00 | 8206.00 | 8135.00 | 8164.00 | 291566 | 555395 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:38 | 2025-12-09 23:31:38

| 2025-01-03 | 8164.00 | 8179.00 | 8082.00 | 8083.00 | 404749 | 545046 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:38 | 2025-12-09 23:31:38

| 2025-01-06 | 8080.00 | 8096.00 | 7936.00 | 7943.00 | 574773 | 571299 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:38 | 2025-12-09 23:31:38

| 2025-01-07 | 7956.00 | 7980.00 | 7885.00 | 7893.00 | 414567 | 553584 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:38 | 2025-12-09 23:31:38

| 2025-01-08 | 7903.00 | 7925.00 | 7856.00 | 7867.00 | 325698 | 533648 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:38 | 2025-12-09 23:31:38

```

---

### hist_lgm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:11


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 829.00 | 837.50 | 825.00 | 829.00 | 25704 | 18483 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:27 | 2025-12-09 23:31:27

| 2025-01-03 | 829.00 | 832.00 | 823.00 | 829.00 | 14157 | 17173 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:27 | 2025-12-09 23:31:27

| 2025-01-06 | 831.50 | 846.00 | 828.00 | 840.50 | 42290 | 24438 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:27 | 2025-12-09 23:31:27

| 2025-01-07 | 839.50 | 849.00 | 836.00 | 848.00 | 35604 | 27689 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:27 | 2025-12-09 23:31:27

| 2025-01-08 | 849.00 | 858.50 | 844.00 | 849.50 | 42102 | 28772 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:28 | 2025-12-09 23:31:28

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 829.00 | 837.50 | 825.00 | 829.00 | 25704 | 18483 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:27 | 2025-12-09 23:31:27

| 2025-01-03 | 829.00 | 832.00 | 823.00 | 829.00 | 14157 | 17173 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:27 | 2025-12-09 23:31:27

| 2025-01-06 | 831.50 | 846.00 | 828.00 | 840.50 | 42290 | 24438 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:27 | 2025-12-09 23:31:27

| 2025-01-07 | 839.50 | 849.00 | 836.00 | 848.00 | 35604 | 27689 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:27 | 2025-12-09 23:31:27

| 2025-01-08 | 849.00 | 858.50 | 844.00 | 849.50 | 42102 | 28772 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:28 | 2025-12-09 23:31:28

```

---

### hist_lhm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:11


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 12840.00 | 13095.00 | 12830.00 | 13090.00 | 64121 | 78702 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:17 | 2025-12-09 23:31:17

| 2025-01-03 | 13085.00 | 13105.00 | 12885.00 | 12950.00 | 49475 | 75008 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:17 | 2025-12-09 23:31:17

| 2025-01-06 | 13045.00 | 13195.00 | 12935.00 | 13005.00 | 54796 | 78468 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:17 | 2025-12-09 23:31:17

| 2025-01-07 | 12970.00 | 12970.00 | 12760.00 | 12770.00 | 46539 | 75089 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:18 | 2025-12-09 23:31:18

| 2025-01-08 | 12830.00 | 12900.00 | 12755.00 | 12895.00 | 32082 | 72767 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:18 | 2025-12-09 23:31:18

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 12840.00 | 13095.00 | 12830.00 | 13090.00 | 64121 | 78702 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:17 | 2025-12-09 23:31:17

| 2025-01-03 | 13085.00 | 13105.00 | 12885.00 | 12950.00 | 49475 | 75008 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:17 | 2025-12-09 23:31:17

| 2025-01-06 | 13045.00 | 13195.00 | 12935.00 | 13005.00 | 54796 | 78468 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:17 | 2025-12-09 23:31:17

| 2025-01-07 | 12970.00 | 12970.00 | 12760.00 | 12770.00 | 46539 | 75089 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:18 | 2025-12-09 23:31:18

| 2025-01-08 | 12830.00 | 12900.00 | 12755.00 | 12895.00 | 32082 | 72767 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:18 | 2025-12-09 23:31:18

```

---

### hist_lm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:11


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 8188.00 | 8206.00 | 8135.00 | 8164.00 | 291566 | 555395 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:59 | 2025-12-09 23:28:59

| 2025-01-03 | 8164.00 | 8179.00 | 8082.00 | 8083.00 | 404749 | 545046 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:59 | 2025-12-09 23:28:59

| 2025-01-06 | 8080.00 | 8096.00 | 7936.00 | 7943.00 | 574773 | 571299 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:59 | 2025-12-09 23:28:59

| 2025-01-07 | 7956.00 | 7980.00 | 7885.00 | 7893.00 | 414567 | 553584 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:59 | 2025-12-09 23:28:59

| 2025-01-08 | 7903.00 | 7925.00 | 7856.00 | 7867.00 | 325698 | 533648 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:59 | 2025-12-09 23:28:59

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 8188.00 | 8206.00 | 8135.00 | 8164.00 | 291566 | 555395 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:59 | 2025-12-09 23:28:59

| 2025-01-03 | 8164.00 | 8179.00 | 8082.00 | 8083.00 | 404749 | 545046 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:59 | 2025-12-09 23:28:59

| 2025-01-06 | 8080.00 | 8096.00 | 7936.00 | 7943.00 | 574773 | 571299 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:59 | 2025-12-09 23:28:59

| 2025-01-07 | 7956.00 | 7980.00 | 7885.00 | 7893.00 | 414567 | 553584 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:59 | 2025-12-09 23:28:59

| 2025-01-08 | 7903.00 | 7925.00 | 7856.00 | 7867.00 | 325698 | 533648 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:59 | 2025-12-09 23:28:59

```

---

### hist_lum

- **阿里云**: 324 行 | **腾讯云**: 339 行 | **差额**: -15

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:11


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 4023.00 | 4038.00 | 3985.00 | 3992.00 | 59315 | 79555 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:08 | 2025-12-09 23:36:08

| 2025-01-03 | 4018.00 | 4061.00 | 4018.00 | 4042.00 | 87419 | 77120 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:08 | 2025-12-09 23:36:08

| 2025-01-06 | 4042.00 | 4109.00 | 4037.00 | 4085.00 | 78291 | 76558 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:08 | 2025-12-09 23:36:08

| 2025-01-07 | 4115.00 | 4118.00 | 4043.00 | 4058.00 | 81002 | 74564 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:08 | 2025-12-09 23:36:08

| 2025-01-08 | 4084.00 | 4122.00 | 4060.00 | 4099.00 | 101749 | 74073 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:08 | 2025-12-09 23:36:08

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 4023.00 | 4038.00 | 3985.00 | 3992.00 | 59315 | 79555 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:08 | 2025-12-09 23:36:08

| 2025-01-03 | 4018.00 | 4061.00 | 4018.00 | 4042.00 | 87419 | 77120 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:08 | 2025-12-09 23:36:08

| 2025-01-06 | 4042.00 | 4109.00 | 4037.00 | 4085.00 | 78291 | 76558 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:08 | 2025-12-09 23:36:08

| 2025-01-07 | 4115.00 | 4118.00 | 4043.00 | 4058.00 | 81002 | 74564 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:08 | 2025-12-09 23:36:08

| 2025-01-08 | 4084.00 | 4122.00 | 4060.00 | 4099.00 | 101749 | 74073 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:36:08 | 2025-12-09 23:36:08

```

---

### hist_mam

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:12


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 2710.00 | 2725.00 | 2697.00 | 2707.00 | 495720 | 961329 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:04 | 2025-12-09 23:33:04

| 2025-01-03 | 2707.00 | 2714.00 | 2647.00 | 2659.00 | 928903 | 913464 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:04 | 2025-12-09 23:33:04

| 2025-01-06 | 2654.00 | 2659.00 | 2590.00 | 2591.00 | 1071351 | 831577 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:04 | 2025-12-09 23:33:04

| 2025-01-07 | 2592.00 | 2608.00 | 2581.00 | 2584.00 | 650573 | 784428 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:04 | 2025-12-09 23:33:04

| 2025-01-08 | 2589.00 | 2613.00 | 2583.00 | 2601.00 | 688334 | 786925 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:04 | 2025-12-09 23:33:04

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 2710.00 | 2725.00 | 2697.00 | 2707.00 | 495720 | 961329 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:04 | 2025-12-09 23:33:04

| 2025-01-03 | 2707.00 | 2714.00 | 2647.00 | 2659.00 | 928903 | 913464 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:04 | 2025-12-09 23:33:04

| 2025-01-06 | 2654.00 | 2659.00 | 2590.00 | 2591.00 | 1071351 | 831577 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:04 | 2025-12-09 23:33:04

| 2025-01-07 | 2592.00 | 2608.00 | 2581.00 | 2584.00 | 650573 | 784428 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:04 | 2025-12-09 23:33:04

| 2025-01-08 | 2589.00 | 2613.00 | 2583.00 | 2601.00 | 688334 | 786925 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:04 | 2025-12-09 23:33:04

```

---

### hist_mm

- **阿里云**: 324 行 | **腾讯云**: 338 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:12


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 2722.00 | 2731.00 | 2704.00 | 2716.00 | 1145644 | 2321102 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:06 | 2025-12-09 23:28:06

| 2025-01-03 | 2718.00 | 2728.00 | 2671.00 | 2688.00 | 1895027 | 2292291 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:07 | 2025-12-09 23:28:07

| 2025-01-06 | 2678.00 | 2712.00 | 2652.00 | 2697.00 | 1892896 | 2266318 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:07 | 2025-12-09 23:28:07

| 2025-01-07 | 2710.00 | 2712.00 | 2640.00 | 2647.00 | 1691120 | 2299797 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:07 | 2025-12-09 23:28:07

| 2025-01-08 | 2648.00 | 2672.00 | 2636.00 | 2646.00 | 1272905 | 2292826 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:07 | 2025-12-09 23:28:07

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 2722.00 | 2731.00 | 2704.00 | 2716.00 | 1145644 | 2321102 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:06 | 2025-12-09 23:28:06

| 2025-01-03 | 2718.00 | 2728.00 | 2671.00 | 2688.00 | 1895027 | 2292291 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:07 | 2025-12-09 23:28:07

| 2025-01-06 | 2678.00 | 2712.00 | 2652.00 | 2697.00 | 1892896 | 2266318 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:07 | 2025-12-09 23:28:07

| 2025-01-07 | 2710.00 | 2712.00 | 2640.00 | 2647.00 | 1691120 | 2299797 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:07 | 2025-12-09 23:28:07

| 2025-01-08 | 2648.00 | 2672.00 | 2636.00 | 2646.00 | 1272905 | 2292826 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:07 | 2025-12-09 23:28:07

```

---

### hist_nim

- **阿里云**: 323 行 | **腾讯云**: 338 行 | **差额**: -15

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:12


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 124500.00 | 125090.00 | 123500.00 | 123820.00 | 90325 | 79893 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:30 | 2025-12-09 23:25:30

| 2025-01-03 | 122950.00 | 123860.00 | 122270.00 | 122640.00 | 127433 | 86042 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:30 | 2025-12-09 23:25:30

| 2025-01-06 | 122200.00 | 123980.00 | 120400.00 | 122260.00 | 209766 | 83996 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:30 | 2025-12-09 23:25:30

| 2025-01-07 | 123500.00 | 124200.00 | 122530.00 | 122720.00 | 114735 | 80385 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:30 | 2025-12-09 23:25:30

| 2025-01-08 | 123320.00 | 125600.00 | 123100.00 | 125230.00 | 159739 | 68527 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:30 | 2025-12-09 23:25:30

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 124500.00 | 125090.00 | 123500.00 | 123820.00 | 90325 | 79893 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:30 | 2025-12-09 23:25:30

| 2025-01-03 | 122950.00 | 123860.00 | 122270.00 | 122640.00 | 127433 | 86042 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:30 | 2025-12-09 23:25:30

| 2025-01-06 | 122200.00 | 123980.00 | 120400.00 | 122260.00 | 209766 | 83996 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:30 | 2025-12-09 23:25:30

| 2025-01-07 | 123500.00 | 124200.00 | 122530.00 | 122720.00 | 114735 | 80385 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:30 | 2025-12-09 23:25:30

| 2025-01-08 | 123320.00 | 125600.00 | 123100.00 | 125230.00 | 159739 | 68527 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:30 | 2025-12-09 23:25:30

```

---

### hist_nrm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:12


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 14930.00 | 14980.00 | 14660.00 | 14695.00 | 48427 | 65375 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:48 | 2025-12-09 23:35:48

| 2025-01-03 | 14695.00 | 14780.00 | 13925.00 | 14155.00 | 104539 | 63583 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:48 | 2025-12-09 23:35:48

| 2025-01-06 | 14210.00 | 14250.00 | 14020.00 | 14120.00 | 87301 | 62120 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:48 | 2025-12-09 23:35:48

| 2025-01-07 | 14205.00 | 14270.00 | 13705.00 | 13960.00 | 114682 | 65693 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:48 | 2025-12-09 23:35:48

| 2025-01-08 | 14000.00 | 14230.00 | 13990.00 | 14160.00 | 96716 | 65765 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:48 | 2025-12-09 23:35:48

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 14930.00 | 14980.00 | 14660.00 | 14695.00 | 48427 | 65375 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:48 | 2025-12-09 23:35:48

| 2025-01-03 | 14695.00 | 14780.00 | 13925.00 | 14155.00 | 104539 | 63583 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:48 | 2025-12-09 23:35:48

| 2025-01-06 | 14210.00 | 14250.00 | 14020.00 | 14120.00 | 87301 | 62120 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:48 | 2025-12-09 23:35:48

| 2025-01-07 | 14205.00 | 14270.00 | 13705.00 | 13960.00 | 114682 | 65693 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:48 | 2025-12-09 23:35:48

| 2025-01-08 | 14000.00 | 14230.00 | 13990.00 | 14160.00 | 96716 | 65765 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:48 | 2025-12-09 23:35:48

```

---

### hist_oim

- **阿里云**: 324 行 | **腾讯云**: 338 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:12


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 9070.00 | 9179.00 | 8917.00 | 8927.00 | 580131 | 263747 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:54 | 2025-12-09 23:32:54

| 2025-01-03 | 8934.00 | 8986.00 | 8788.00 | 8812.00 | 670716 | 254478 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:54 | 2025-12-09 23:32:54

| 2025-01-06 | 8804.00 | 8887.00 | 8710.00 | 8718.00 | 603568 | 265911 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:54 | 2025-12-09 23:32:54

| 2025-01-07 | 8783.00 | 8783.00 | 8596.00 | 8643.00 | 622562 | 278018 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:54 | 2025-12-09 23:32:54

| 2025-01-08 | 8643.00 | 8688.00 | 8545.00 | 8580.00 | 575656 | 295168 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:54 | 2025-12-09 23:32:54

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 9070.00 | 9179.00 | 8917.00 | 8927.00 | 580131 | 263747 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:54 | 2025-12-09 23:32:54

| 2025-01-03 | 8934.00 | 8986.00 | 8788.00 | 8812.00 | 670716 | 254478 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:54 | 2025-12-09 23:32:54

| 2025-01-06 | 8804.00 | 8887.00 | 8710.00 | 8718.00 | 603568 | 265911 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:54 | 2025-12-09 23:32:54

| 2025-01-07 | 8783.00 | 8783.00 | 8596.00 | 8643.00 | 622562 | 278018 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:54 | 2025-12-09 23:32:54

| 2025-01-08 | 8643.00 | 8688.00 | 8545.00 | 8580.00 | 575656 | 295168 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:54 | 2025-12-09 23:32:54

```

---

### hist_opm

- **阿里云**: 174 行 | **腾讯云**: 188 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:12


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-05-06 | 4002.00 | 4020.00 | 3982.00 | 4018.00 | 711 | 18523 | 113740160.00 | 6.00 | 0.15 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:18:21 | 2025-12-09 22:20:29

| 2025-05-07 | 4002.00 | 4020.00 | 3982.00 | 4018.00 | 711 | 18523 | 113740160.00 | 6.00 | 0.15 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:20:47 | 2025-12-09 22:20:47

| 2025-05-08 | 4002.00 | 4020.00 | 3982.00 | 4018.00 | 711 | 18523 | 113740160.00 | 6.00 | 0.15 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:05 | 2025-12-09 22:21:05

| 2025-05-09 | 4002.00 | 4020.00 | 3982.00 | 4018.00 | 711 | 18523 | 113740160.00 | 6.00 | 0.15 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:23 | 2025-12-09 22:21:23

| 2025-05-12 | 4002.00 | 4020.00 | 3982.00 | 4018.00 | 711 | 18523 | 113740160.00 | 6.00 | 0.15 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:41 | 2025-12-09 22:21:41

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-05-06 | 4002.00 | 4020.00 | 3982.00 | 4018.00 | 711 | 18523 | 113740160.00 | 6.00 | 0.15 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:18:21 | 2025-12-09 22:20:29

| 2025-05-07 | 4002.00 | 4020.00 | 3982.00 | 4018.00 | 711 | 18523 | 113740160.00 | 6.00 | 0.15 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:20:47 | 2025-12-09 22:20:47

| 2025-05-08 | 4002.00 | 4020.00 | 3982.00 | 4018.00 | 711 | 18523 | 113740160.00 | 6.00 | 0.15 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:05 | 2025-12-09 22:21:05

| 2025-05-09 | 4002.00 | 4020.00 | 3982.00 | 4018.00 | 711 | 18523 | 113740160.00 | 6.00 | 0.15 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:23 | 2025-12-09 22:21:23

| 2025-05-12 | 4002.00 | 4020.00 | 3982.00 | 4018.00 | 711 | 18523 | 113740160.00 | 6.00 | 0.15 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:41 | 2025-12-09 22:21:41

```

---

### hist_pbm

- **阿里云**: 323 行 | **腾讯云**: 338 行 | **差额**: -15

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:12


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 16870.00 | 16905.00 | 16740.00 | 16825.00 | 28915 | 49567 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:48 | 2025-12-09 23:24:48

| 2025-01-03 | 16795.00 | 16855.00 | 16620.00 | 16685.00 | 43733 | 49563 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:48 | 2025-12-09 23:24:48

| 2025-01-06 | 16615.00 | 16820.00 | 16615.00 | 16730.00 | 39929 | 47338 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:48 | 2025-12-09 23:24:48

| 2025-01-07 | 16795.00 | 16810.00 | 16660.00 | 16730.00 | 28827 | 43709 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:48 | 2025-12-09 23:24:48

| 2025-01-08 | 16755.00 | 16805.00 | 16710.00 | 16735.00 | 24248 | 41843 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:48 | 2025-12-09 23:24:48

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 16870.00 | 16905.00 | 16740.00 | 16825.00 | 28915 | 49567 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:48 | 2025-12-09 23:24:48

| 2025-01-03 | 16795.00 | 16855.00 | 16620.00 | 16685.00 | 43733 | 49563 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:48 | 2025-12-09 23:24:48

| 2025-01-06 | 16615.00 | 16820.00 | 16615.00 | 16730.00 | 39929 | 47338 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:48 | 2025-12-09 23:24:48

| 2025-01-07 | 16795.00 | 16810.00 | 16660.00 | 16730.00 | 28827 | 43709 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:48 | 2025-12-09 23:24:48

| 2025-01-08 | 16755.00 | 16805.00 | 16710.00 | 16735.00 | 24248 | 41843 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:48 | 2025-12-09 23:24:48

```

---

### hist_pfm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:12


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 6850.00 | 6930.00 | 6830.00 | 6902.00 | 80255 | 92539 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:46 | 2025-12-09 23:34:46

| 2025-01-03 | 6920.00 | 6934.00 | 6872.00 | 6880.00 | 57461 | 127975 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:46 | 2025-12-09 23:34:46

| 2025-01-06 | 6892.00 | 6944.00 | 6850.00 | 6888.00 | 58368 | 141351 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:46 | 2025-12-09 23:34:46

| 2025-01-07 | 6888.00 | 6926.00 | 6828.00 | 6838.00 | 88175 | 155322 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:46 | 2025-12-09 23:34:46

| 2025-01-08 | 6838.00 | 6872.00 | 6808.00 | 6820.00 | 93378 | 170417 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:46 | 2025-12-09 23:34:46

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 6850.00 | 6930.00 | 6830.00 | 6902.00 | 80255 | 92539 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:46 | 2025-12-09 23:34:46

| 2025-01-03 | 6920.00 | 6934.00 | 6872.00 | 6880.00 | 57461 | 127975 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:46 | 2025-12-09 23:34:46

| 2025-01-06 | 6892.00 | 6944.00 | 6850.00 | 6888.00 | 58368 | 141351 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:46 | 2025-12-09 23:34:46

| 2025-01-07 | 6888.00 | 6926.00 | 6828.00 | 6838.00 | 88175 | 155322 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:46 | 2025-12-09 23:34:46

| 2025-01-08 | 6838.00 | 6872.00 | 6808.00 | 6820.00 | 93378 | 170417 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:46 | 2025-12-09 23:34:46

```

---

### hist_pgm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:12


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 4539.00 | 4548.00 | 4470.00 | 4499.00 | 86382 | 68938 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:13 | 2025-12-09 23:32:13

| 2025-01-03 | 4517.00 | 4521.00 | 4441.00 | 4444.00 | 75413 | 60919 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:13 | 2025-12-09 23:32:13

| 2025-01-06 | 4462.00 | 4500.00 | 4413.00 | 4428.00 | 85213 | 56904 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:13 | 2025-12-09 23:32:13

| 2025-01-07 | 4443.00 | 4449.00 | 4323.00 | 4377.00 | 86018 | 45580 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:13 | 2025-12-09 23:32:13

| 2025-01-08 | 4311.00 | 4340.00 | 4288.00 | 4300.00 | 30488 | 54302 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:13 | 2025-12-09 23:32:13

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 4539.00 | 4548.00 | 4470.00 | 4499.00 | 86382 | 68938 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:13 | 2025-12-09 23:32:13

| 2025-01-03 | 4517.00 | 4521.00 | 4441.00 | 4444.00 | 75413 | 60919 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:13 | 2025-12-09 23:32:13

| 2025-01-06 | 4462.00 | 4500.00 | 4413.00 | 4428.00 | 85213 | 56904 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:13 | 2025-12-09 23:32:13

| 2025-01-07 | 4443.00 | 4449.00 | 4323.00 | 4377.00 | 86018 | 45580 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:13 | 2025-12-09 23:32:13

| 2025-01-08 | 4311.00 | 4340.00 | 4288.00 | 4300.00 | 30488 | 54302 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:13 | 2025-12-09 23:32:13

```

---

### hist_pkm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:13


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 7946.00 | 7954.00 | 7904.00 | 7914.00 | 42857 | 115362 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:56 | 2025-12-09 23:34:56

| 2025-01-03 | 7892.00 | 7920.00 | 7812.00 | 7838.00 | 58720 | 117858 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:56 | 2025-12-09 23:34:56

| 2025-01-06 | 7830.00 | 7848.00 | 7800.00 | 7848.00 | 31562 | 121307 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:56 | 2025-12-09 23:34:56

| 2025-01-07 | 7848.00 | 7876.00 | 7814.00 | 7870.00 | 30987 | 119958 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:56 | 2025-12-09 23:34:56

| 2025-01-08 | 7884.00 | 7884.00 | 7818.00 | 7818.00 | 34794 | 120009 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:56 | 2025-12-09 23:34:56

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 7946.00 | 7954.00 | 7904.00 | 7914.00 | 42857 | 115362 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:56 | 2025-12-09 23:34:56

| 2025-01-03 | 7892.00 | 7920.00 | 7812.00 | 7838.00 | 58720 | 117858 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:56 | 2025-12-09 23:34:56

| 2025-01-06 | 7830.00 | 7848.00 | 7800.00 | 7848.00 | 31562 | 121307 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:56 | 2025-12-09 23:34:56

| 2025-01-07 | 7848.00 | 7876.00 | 7814.00 | 7870.00 | 30987 | 119958 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:56 | 2025-12-09 23:34:56

| 2025-01-08 | 7884.00 | 7884.00 | 7818.00 | 7818.00 | 34794 | 120009 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:56 | 2025-12-09 23:34:56

```

---

### hist_pm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:13


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 8660.00 | 8824.00 | 8458.00 | 8474.00 | 1196491 | 511183 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:46 | 2025-12-09 23:28:46

| 2025-01-03 | 8470.00 | 8558.00 | 8372.00 | 8530.00 | 1269242 | 484663 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:46 | 2025-12-09 23:28:46

| 2025-01-06 | 8540.00 | 8646.00 | 8478.00 | 8484.00 | 1039802 | 469855 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:46 | 2025-12-09 23:28:46

| 2025-01-07 | 8534.00 | 8752.00 | 8460.00 | 8722.00 | 1220042 | 497072 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:46 | 2025-12-09 23:28:46

| 2025-01-08 | 8712.00 | 8774.00 | 8608.00 | 8618.00 | 1046988 | 469991 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:46 | 2025-12-09 23:28:46

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 8660.00 | 8824.00 | 8458.00 | 8474.00 | 1196491 | 511183 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:46 | 2025-12-09 23:28:46

| 2025-01-03 | 8470.00 | 8558.00 | 8372.00 | 8530.00 | 1269242 | 484663 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:46 | 2025-12-09 23:28:46

| 2025-01-06 | 8540.00 | 8646.00 | 8478.00 | 8484.00 | 1039802 | 469855 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:46 | 2025-12-09 23:28:46

| 2025-01-07 | 8534.00 | 8752.00 | 8460.00 | 8722.00 | 1220042 | 497072 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:46 | 2025-12-09 23:28:46

| 2025-01-08 | 8712.00 | 8774.00 | 8608.00 | 8618.00 | 1046988 | 469991 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:46 | 2025-12-09 23:28:46

```

---

### hist_ppfm

- **阿里云**: 312 行 | **腾讯云**: 324 行 | **差额**: -12

- 引擎: InnoDB | 创建时间: 2025-11-12 09:16:43


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 7480.00 | 7507.00 | 7465.00 | 7495.00 | 253319 | 476369 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:58 | 2025-12-09 23:31:58

| 2025-01-03 | 7499.00 | 7502.00 | 7430.00 | 7432.00 | 293826 | 457785 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:58 | 2025-12-09 23:31:58

| 2025-01-06 | 7423.00 | 7450.00 | 7351.00 | 7354.00 | 437260 | 443473 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:58 | 2025-12-09 23:31:58

| 2025-01-07 | 7368.00 | 7379.00 | 7315.00 | 7323.00 | 292420 | 451222 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:58 | 2025-12-09 23:31:58

| 2025-01-08 | 7340.00 | 7349.00 | 7305.00 | 7310.00 | 254762 | 482629 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:58 | 2025-12-09 23:31:58

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 7480.00 | 7507.00 | 7465.00 | 7495.00 | 253319 | 476369 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:58 | 2025-12-09 23:31:58

| 2025-01-03 | 7499.00 | 7502.00 | 7430.00 | 7432.00 | 293826 | 457785 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:58 | 2025-12-09 23:31:58

| 2025-01-06 | 7423.00 | 7450.00 | 7351.00 | 7354.00 | 437260 | 443473 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:58 | 2025-12-09 23:31:58

| 2025-01-07 | 7368.00 | 7379.00 | 7315.00 | 7323.00 | 292420 | 451222 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:58 | 2025-12-09 23:31:58

| 2025-01-08 | 7340.00 | 7349.00 | 7305.00 | 7310.00 | 254762 | 482629 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:58 | 2025-12-09 23:31:58

```

---

### hist_ppm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:13


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 7480.00 | 7507.00 | 7465.00 | 7495.00 | 253319 | 476369 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:27 | 2025-12-09 23:30:27

| 2025-01-03 | 7499.00 | 7502.00 | 7430.00 | 7432.00 | 293826 | 457785 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:27 | 2025-12-09 23:30:27

| 2025-01-06 | 7423.00 | 7450.00 | 7351.00 | 7354.00 | 437260 | 443473 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:27 | 2025-12-09 23:30:27

| 2025-01-07 | 7368.00 | 7379.00 | 7315.00 | 7323.00 | 292420 | 451222 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:27 | 2025-12-09 23:30:27

| 2025-01-08 | 7340.00 | 7349.00 | 7305.00 | 7310.00 | 254762 | 482629 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:27 | 2025-12-09 23:30:27

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 7480.00 | 7507.00 | 7465.00 | 7495.00 | 253319 | 476369 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:27 | 2025-12-09 23:30:27

| 2025-01-03 | 7499.00 | 7502.00 | 7430.00 | 7432.00 | 293826 | 457785 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:27 | 2025-12-09 23:30:27

| 2025-01-06 | 7423.00 | 7450.00 | 7351.00 | 7354.00 | 437260 | 443473 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:27 | 2025-12-09 23:30:27

| 2025-01-07 | 7368.00 | 7379.00 | 7315.00 | 7323.00 | 292420 | 451222 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:27 | 2025-12-09 23:30:27

| 2025-01-08 | 7340.00 | 7349.00 | 7305.00 | 7310.00 | 254762 | 482629 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:27 | 2025-12-09 23:30:27

```

---

### hist_prm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:13


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 6162.00 | 6240.00 | 6158.00 | 6238.00 | 11769 | 17073 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:27 | 2025-12-09 23:35:27

| 2025-01-03 | 6242.00 | 6266.00 | 6202.00 | 6212.00 | 10715 | 15816 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:27 | 2025-12-09 23:35:27

| 2025-01-06 | 6218.00 | 6280.00 | 6172.00 | 6174.00 | 15778 | 15615 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:27 | 2025-12-09 23:35:27

| 2025-01-07 | 6184.00 | 6214.00 | 6120.00 | 6134.00 | 12388 | 16356 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:27 | 2025-12-09 23:35:27

| 2025-01-08 | 6134.00 | 6156.00 | 6116.00 | 6138.00 | 11266 | 16683 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:27 | 2025-12-09 23:35:27

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 6162.00 | 6240.00 | 6158.00 | 6238.00 | 11769 | 17073 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:27 | 2025-12-09 23:35:27

| 2025-01-03 | 6242.00 | 6266.00 | 6202.00 | 6212.00 | 10715 | 15816 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:27 | 2025-12-09 23:35:27

| 2025-01-06 | 6218.00 | 6280.00 | 6172.00 | 6174.00 | 15778 | 15615 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:27 | 2025-12-09 23:35:27

| 2025-01-07 | 6184.00 | 6214.00 | 6120.00 | 6134.00 | 12388 | 16356 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:27 | 2025-12-09 23:35:27

| 2025-01-08 | 6134.00 | 6156.00 | 6116.00 | 6138.00 | 11266 | 16683 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:27 | 2025-12-09 23:35:27

```

---

### hist_psm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:13


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 42315.00 | 42680.00 | 42315.00 | 42570.00 | 36858 | 30447 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:50 | 2025-12-09 23:37:50

| 2025-01-03 | 42570.00 | 42780.00 | 42365.00 | 42560.00 | 37079 | 29242 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:50 | 2025-12-09 23:37:50

| 2025-01-06 | 42600.00 | 43600.00 | 42560.00 | 43325.00 | 68310 | 31663 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:50 | 2025-12-09 23:37:50

| 2025-01-07 | 43325.00 | 43450.00 | 42765.00 | 43185.00 | 39615 | 30357 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:50 | 2025-12-09 23:37:50

| 2025-01-08 | 43185.00 | 43390.00 | 42650.00 | 42700.00 | 30253 | 28183 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:50 | 2025-12-09 23:37:50

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 42315.00 | 42680.00 | 42315.00 | 42570.00 | 36858 | 30447 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:50 | 2025-12-09 23:37:50

| 2025-01-03 | 42570.00 | 42780.00 | 42365.00 | 42560.00 | 37079 | 29242 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:50 | 2025-12-09 23:37:50

| 2025-01-06 | 42600.00 | 43600.00 | 42560.00 | 43325.00 | 68310 | 31663 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:50 | 2025-12-09 23:37:50

| 2025-01-07 | 43325.00 | 43450.00 | 42765.00 | 43185.00 | 39615 | 30357 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:50 | 2025-12-09 23:37:50

| 2025-01-08 | 43185.00 | 43390.00 | 42650.00 | 42700.00 | 30253 | 28183 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:50 | 2025-12-09 23:37:50

```

---

### hist_pxm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:13


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 7000.00 | 7124.00 | 6992.00 | 7082.00 | 107336 | 93369 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:06 | 2025-12-09 23:35:06

| 2025-01-03 | 7082.00 | 7144.00 | 7058.00 | 7086.00 | 95625 | 92775 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:06 | 2025-12-09 23:35:06

| 2025-01-06 | 7086.00 | 7250.00 | 7032.00 | 7114.00 | 155762 | 96590 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:06 | 2025-12-09 23:35:06

| 2025-01-07 | 7138.00 | 7164.00 | 6972.00 | 6998.00 | 129527 | 97198 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:06 | 2025-12-09 23:35:06

| 2025-01-08 | 7006.00 | 7038.00 | 6960.00 | 7016.00 | 93862 | 101317 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:06 | 2025-12-09 23:35:06

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 7000.00 | 7124.00 | 6992.00 | 7082.00 | 107336 | 93369 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:06 | 2025-12-09 23:35:06

| 2025-01-03 | 7082.00 | 7144.00 | 7058.00 | 7086.00 | 95625 | 92775 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:06 | 2025-12-09 23:35:06

| 2025-01-06 | 7086.00 | 7250.00 | 7032.00 | 7114.00 | 155762 | 96590 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:06 | 2025-12-09 23:35:06

| 2025-01-07 | 7138.00 | 7164.00 | 6972.00 | 6998.00 | 129527 | 97198 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:06 | 2025-12-09 23:35:06

| 2025-01-08 | 7006.00 | 7038.00 | 6960.00 | 7016.00 | 93862 | 101317 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:06 | 2025-12-09 23:35:06

```

---

### hist_rbm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:13


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 3305.00 | 3335.00 | 3284.00 | 3306.00 | 1373928 | 1551112 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:58 | 2025-12-09 23:24:58

| 2025-01-03 | 3305.00 | 3309.00 | 3260.00 | 3272.00 | 1560003 | 1675464 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:58 | 2025-12-09 23:24:58

| 2025-01-06 | 3264.00 | 3287.00 | 3251.00 | 3252.00 | 1614675 | 1746201 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:58 | 2025-12-09 23:24:58

| 2025-01-07 | 3269.00 | 3278.00 | 3232.00 | 3239.00 | 1312041 | 1772105 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:58 | 2025-12-09 23:24:58

| 2025-01-08 | 3239.00 | 3250.00 | 3204.00 | 3211.00 | 1273140 | 1842567 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:59 | 2025-12-09 23:24:59

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 3305.00 | 3335.00 | 3284.00 | 3306.00 | 1373928 | 1551112 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:58 | 2025-12-09 23:24:58

| 2025-01-03 | 3305.00 | 3309.00 | 3260.00 | 3272.00 | 1560003 | 1675464 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:58 | 2025-12-09 23:24:58

| 2025-01-06 | 3264.00 | 3287.00 | 3251.00 | 3252.00 | 1614675 | 1746201 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:58 | 2025-12-09 23:24:58

| 2025-01-07 | 3269.00 | 3278.00 | 3232.00 | 3239.00 | 1312041 | 1772105 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:58 | 2025-12-09 23:24:58

| 2025-01-08 | 3239.00 | 3250.00 | 3204.00 | 3211.00 | 1273140 | 1842567 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:59 | 2025-12-09 23:24:59

```

---

### hist_rmm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:14


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 2420.00 | 2444.00 | 2403.00 | 2409.00 | 759764 | 707506 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:26 | 2025-12-09 23:33:26

| 2025-01-03 | 2408.00 | 2419.00 | 2348.00 | 2357.00 | 1137968 | 683281 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:26 | 2025-12-09 23:33:26

| 2025-01-06 | 2350.00 | 2385.00 | 2333.00 | 2356.00 | 1003866 | 687180 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:26 | 2025-12-09 23:33:26

| 2025-01-07 | 2359.00 | 2367.00 | 2274.00 | 2284.00 | 1174961 | 740432 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:26 | 2025-12-09 23:33:26

| 2025-01-08 | 2282.00 | 2301.00 | 2261.00 | 2263.00 | 752532 | 754536 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:26 | 2025-12-09 23:33:26

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 2420.00 | 2444.00 | 2403.00 | 2409.00 | 759764 | 707506 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:26 | 2025-12-09 23:33:26

| 2025-01-03 | 2408.00 | 2419.00 | 2348.00 | 2357.00 | 1137968 | 683281 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:26 | 2025-12-09 23:33:26

| 2025-01-06 | 2350.00 | 2385.00 | 2333.00 | 2356.00 | 1003866 | 687180 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:26 | 2025-12-09 23:33:26

| 2025-01-07 | 2359.00 | 2367.00 | 2274.00 | 2284.00 | 1174961 | 740432 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:26 | 2025-12-09 23:33:26

| 2025-01-08 | 2282.00 | 2301.00 | 2261.00 | 2263.00 | 752532 | 754536 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:26 | 2025-12-09 23:33:26

```

---

### hist_rrm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:14


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 3438.00 | 3445.00 | 3424.00 | 3441.00 | 2103 | 7147 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:57 | 2025-12-09 23:30:57

| 2025-01-03 | 3439.00 | 3445.00 | 3427.00 | 3442.00 | 2523 | 8348 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:57 | 2025-12-09 23:30:57

| 2025-01-06 | 3442.00 | 3477.00 | 3441.00 | 3464.00 | 2990 | 8829 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:57 | 2025-12-09 23:30:57

| 2025-01-07 | 3465.00 | 3493.00 | 3461.00 | 3480.00 | 2891 | 9419 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:58 | 2025-12-09 23:30:58

| 2025-01-08 | 3480.00 | 3514.00 | 3474.00 | 3507.00 | 3350 | 10053 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:58 | 2025-12-09 23:30:58

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 3438.00 | 3445.00 | 3424.00 | 3441.00 | 2103 | 7147 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:57 | 2025-12-09 23:30:57

| 2025-01-03 | 3439.00 | 3445.00 | 3427.00 | 3442.00 | 2523 | 8348 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:57 | 2025-12-09 23:30:57

| 2025-01-06 | 3442.00 | 3477.00 | 3441.00 | 3464.00 | 2990 | 8829 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:57 | 2025-12-09 23:30:57

| 2025-01-07 | 3465.00 | 3493.00 | 3461.00 | 3480.00 | 2891 | 9419 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:58 | 2025-12-09 23:30:58

| 2025-01-08 | 3480.00 | 3514.00 | 3474.00 | 3507.00 | 3350 | 10053 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:30:58 | 2025-12-09 23:30:58

```

---

### hist_rsm

- **阿里云**: 210 行 | **腾讯云**: 224 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:14


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-05-06 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 7 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:20:40 | 2025-12-09 22:20:40

| 2025-05-07 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 7 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:20:58 | 2025-12-09 22:20:58

| 2025-05-08 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 7 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:17 | 2025-12-09 22:21:17

| 2025-05-09 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 7 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:35 | 2025-12-09 22:21:35

| 2025-05-12 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 7 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:52 | 2025-12-09 22:21:52

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-05-06 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 7 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:20:40 | 2025-12-09 22:20:40

| 2025-05-07 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 7 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:20:58 | 2025-12-09 22:20:58

| 2025-05-08 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 7 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:17 | 2025-12-09 22:21:17

| 2025-05-09 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 7 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:35 | 2025-12-09 22:21:35

| 2025-05-12 | 0.00 | 0.00 | 0.00 | 0.00 | 0 | 7 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:52 | 2025-12-09 22:21:52

```

---

### hist_rum

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:14


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 17780.00 | 17845.00 | 17550.00 | 17575.00 | 359299 | 203191 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:10 | 2025-12-09 23:25:10

| 2025-01-03 | 17590.00 | 17645.00 | 16680.00 | 16840.00 | 842308 | 209778 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:10 | 2025-12-09 23:25:10

| 2025-01-06 | 16925.00 | 16925.00 | 16640.00 | 16750.00 | 487020 | 203936 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:10 | 2025-12-09 23:25:10

| 2025-01-07 | 16825.00 | 16900.00 | 16370.00 | 16630.00 | 587087 | 205247 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:10 | 2025-12-09 23:25:10

| 2025-01-08 | 16700.00 | 16830.00 | 16640.00 | 16795.00 | 381339 | 200530 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:10 | 2025-12-09 23:25:10

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 17780.00 | 17845.00 | 17550.00 | 17575.00 | 359299 | 203191 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:10 | 2025-12-09 23:25:10

| 2025-01-03 | 17590.00 | 17645.00 | 16680.00 | 16840.00 | 842308 | 209778 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:10 | 2025-12-09 23:25:10

| 2025-01-06 | 16925.00 | 16925.00 | 16640.00 | 16750.00 | 487020 | 203936 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:10 | 2025-12-09 23:25:10

| 2025-01-07 | 16825.00 | 16900.00 | 16370.00 | 16630.00 | 587087 | 205247 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:10 | 2025-12-09 23:25:10

| 2025-01-08 | 16700.00 | 16830.00 | 16640.00 | 16795.00 | 381339 | 200530 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:10 | 2025-12-09 23:25:10

```

---

### hist_sam

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:14


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 1438.00 | 1456.00 | 1433.00 | 1444.00 | 525230 | 1001732 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:36 | 2025-12-09 23:34:36

| 2025-01-03 | 1442.00 | 1445.00 | 1407.00 | 1416.00 | 918806 | 1078910 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:36 | 2025-12-09 23:34:36

| 2025-01-06 | 1415.00 | 1432.00 | 1394.00 | 1416.00 | 939487 | 1085899 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:36 | 2025-12-09 23:34:36

| 2025-01-07 | 1421.00 | 1425.00 | 1400.00 | 1404.00 | 651808 | 1117091 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:36 | 2025-12-09 23:34:36

| 2025-01-08 | 1400.00 | 1410.00 | 1383.00 | 1386.00 | 728258 | 1127148 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:36 | 2025-12-09 23:34:36

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 1438.00 | 1456.00 | 1433.00 | 1444.00 | 525230 | 1001732 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:36 | 2025-12-09 23:34:36

| 2025-01-03 | 1442.00 | 1445.00 | 1407.00 | 1416.00 | 918806 | 1078910 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:36 | 2025-12-09 23:34:36

| 2025-01-06 | 1415.00 | 1432.00 | 1394.00 | 1416.00 | 939487 | 1085899 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:36 | 2025-12-09 23:34:36

| 2025-01-07 | 1421.00 | 1425.00 | 1400.00 | 1404.00 | 651808 | 1117091 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:36 | 2025-12-09 23:34:36

| 2025-01-08 | 1400.00 | 1410.00 | 1383.00 | 1386.00 | 728258 | 1127148 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:36 | 2025-12-09 23:34:36

```

---

### hist_scm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:14


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 563.00 | 566.70 | 559.40 | 560.70 | 32063 | 29562 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:37 | 2025-12-09 23:35:37

| 2025-01-03 | 566.50 | 574.30 | 565.30 | 572.10 | 96574 | 32260 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:37 | 2025-12-09 23:35:37

| 2025-01-06 | 572.50 | 582.40 | 570.80 | 577.00 | 89272 | 29887 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:37 | 2025-12-09 23:35:37

| 2025-01-07 | 581.10 | 585.00 | 575.50 | 580.70 | 112019 | 30120 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:37 | 2025-12-09 23:35:37

| 2025-01-08 | 584.40 | 594.80 | 583.00 | 589.10 | 107511 | 31130 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:38 | 2025-12-09 23:35:38

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 563.00 | 566.70 | 559.40 | 560.70 | 32063 | 29562 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:37 | 2025-12-09 23:35:37

| 2025-01-03 | 566.50 | 574.30 | 565.30 | 572.10 | 96574 | 32260 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:37 | 2025-12-09 23:35:37

| 2025-01-06 | 572.50 | 582.40 | 570.80 | 577.00 | 89272 | 29887 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:37 | 2025-12-09 23:35:37

| 2025-01-07 | 581.10 | 585.00 | 575.50 | 580.70 | 112019 | 30120 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:37 | 2025-12-09 23:35:37

| 2025-01-08 | 584.40 | 594.80 | 583.00 | 589.10 | 107511 | 31130 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:38 | 2025-12-09 23:35:38

```

---

### hist_sfm

- **阿里云**: 323 行 | **腾讯云**: 338 行 | **差额**: -15

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:14


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 6252.00 | 6314.00 | 6244.00 | 6298.00 | 83859 | 97613 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:36 | 2025-12-09 23:33:36

| 2025-01-03 | 6328.00 | 6340.00 | 6256.00 | 6292.00 | 66674 | 121917 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:36 | 2025-12-09 23:33:36

| 2025-01-06 | 6294.00 | 6336.00 | 6286.00 | 6312.00 | 53728 | 128842 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:36 | 2025-12-09 23:33:36

| 2025-01-07 | 6312.00 | 6312.00 | 6192.00 | 6216.00 | 93701 | 149947 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:36 | 2025-12-09 23:33:36

| 2025-01-08 | 6216.00 | 6264.00 | 6190.00 | 6242.00 | 82090 | 159701 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:36 | 2025-12-09 23:33:36

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 6252.00 | 6314.00 | 6244.00 | 6298.00 | 83859 | 97613 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:36 | 2025-12-09 23:33:36

| 2025-01-03 | 6328.00 | 6340.00 | 6256.00 | 6292.00 | 66674 | 121917 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:36 | 2025-12-09 23:33:36

| 2025-01-06 | 6294.00 | 6336.00 | 6286.00 | 6312.00 | 53728 | 128842 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:36 | 2025-12-09 23:33:36

| 2025-01-07 | 6312.00 | 6312.00 | 6192.00 | 6216.00 | 93701 | 149947 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:36 | 2025-12-09 23:33:36

| 2025-01-08 | 6216.00 | 6264.00 | 6190.00 | 6242.00 | 82090 | 159701 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:36 | 2025-12-09 23:33:36

```

---

### hist_shm

- **阿里云**: 324 行 | **腾讯云**: 338 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:14


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 2908.00 | 2954.00 | 2875.00 | 2917.00 | 412232 | 152896 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:17 | 2025-12-09 23:35:17

| 2025-01-03 | 2903.00 | 2947.00 | 2880.00 | 2920.00 | 436933 | 161448 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:17 | 2025-12-09 23:35:17

| 2025-01-06 | 2929.00 | 3066.00 | 2914.00 | 3041.00 | 919117 | 195532 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:17 | 2025-12-09 23:35:17

| 2025-01-07 | 3050.00 | 3068.00 | 2988.00 | 3059.00 | 875760 | 224961 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:17 | 2025-12-09 23:35:17

| 2025-01-08 | 3035.00 | 3055.00 | 2999.00 | 3012.00 | 821768 | 212429 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:17 | 2025-12-09 23:35:17

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 2908.00 | 2954.00 | 2875.00 | 2917.00 | 412232 | 152896 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:17 | 2025-12-09 23:35:17

| 2025-01-03 | 2903.00 | 2947.00 | 2880.00 | 2920.00 | 436933 | 161448 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:17 | 2025-12-09 23:35:17

| 2025-01-06 | 2929.00 | 3066.00 | 2914.00 | 3041.00 | 919117 | 195532 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:17 | 2025-12-09 23:35:17

| 2025-01-07 | 3050.00 | 3068.00 | 2988.00 | 3059.00 | 875760 | 224961 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:17 | 2025-12-09 23:35:17

| 2025-01-08 | 3035.00 | 3055.00 | 2999.00 | 3012.00 | 821768 | 212429 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:35:17 | 2025-12-09 23:35:17

```

---

### hist_sim

- **阿里云**: 324 行 | **腾讯云**: 338 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:14


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 11005.00 | 11130.00 | 10980.00 | 11050.00 | 128281 | 115469 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:30 | 2025-12-09 23:37:30

| 2025-01-03 | 11020.00 | 11075.00 | 10725.00 | 10780.00 | 144663 | 115916 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:30 | 2025-12-09 23:37:30

| 2025-01-06 | 10790.00 | 10955.00 | 10735.00 | 10780.00 | 147245 | 113355 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:30 | 2025-12-09 23:37:30

| 2025-01-07 | 10770.00 | 10780.00 | 10555.00 | 10580.00 | 160900 | 114596 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:30 | 2025-12-09 23:37:30

| 2025-01-08 | 10570.00 | 10635.00 | 10505.00 | 10530.00 | 145924 | 116397 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:30 | 2025-12-09 23:37:30

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 11005.00 | 11130.00 | 10980.00 | 11050.00 | 128281 | 115469 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:30 | 2025-12-09 23:37:30

| 2025-01-03 | 11020.00 | 11075.00 | 10725.00 | 10780.00 | 144663 | 115916 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:30 | 2025-12-09 23:37:30

| 2025-01-06 | 10790.00 | 10955.00 | 10735.00 | 10780.00 | 147245 | 113355 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:30 | 2025-12-09 23:37:30

| 2025-01-07 | 10770.00 | 10780.00 | 10555.00 | 10580.00 | 160900 | 114596 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:30 | 2025-12-09 23:37:30

| 2025-01-08 | 10570.00 | 10635.00 | 10505.00 | 10530.00 | 145924 | 116397 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:30 | 2025-12-09 23:37:30

```

---

### hist_smm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:15


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 6090.00 | 6150.00 | 6084.00 | 6118.00 | 109131 | 330074 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:46 | 2025-12-09 23:33:46

| 2025-01-03 | 6120.00 | 6138.00 | 6078.00 | 6090.00 | 97162 | 330694 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:46 | 2025-12-09 23:33:46

| 2025-01-06 | 6080.00 | 6116.00 | 6054.00 | 6068.00 | 85360 | 339397 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:46 | 2025-12-09 23:33:46

| 2025-01-07 | 6080.00 | 6082.00 | 6024.00 | 6030.00 | 87320 | 354984 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:46 | 2025-12-09 23:33:46

| 2025-01-08 | 6046.00 | 6060.00 | 6022.00 | 6028.00 | 60871 | 352984 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:46 | 2025-12-09 23:33:46

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 6090.00 | 6150.00 | 6084.00 | 6118.00 | 109131 | 330074 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:46 | 2025-12-09 23:33:46

| 2025-01-03 | 6120.00 | 6138.00 | 6078.00 | 6090.00 | 97162 | 330694 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:46 | 2025-12-09 23:33:46

| 2025-01-06 | 6080.00 | 6116.00 | 6054.00 | 6068.00 | 85360 | 339397 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:46 | 2025-12-09 23:33:46

| 2025-01-07 | 6080.00 | 6082.00 | 6024.00 | 6030.00 | 87320 | 354984 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:46 | 2025-12-09 23:33:46

| 2025-01-08 | 6046.00 | 6060.00 | 6022.00 | 6028.00 | 60871 | 352984 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:33:46 | 2025-12-09 23:33:46

```

---

### hist_snm

- **阿里云**: 324 行 | **腾讯云**: 339 行 | **差额**: -15

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:15


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 242700.00 | 244970.00 | 242050.00 | 244640.00 | 43325 | 26658 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:41 | 2025-12-09 23:25:41

| 2025-01-03 | 243070.00 | 245620.00 | 241010.00 | 244180.00 | 84133 | 26981 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:41 | 2025-12-09 23:25:41

| 2025-01-06 | 245320.00 | 248950.00 | 244840.00 | 246660.00 | 82641 | 27790 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:41 | 2025-12-09 23:25:41

| 2025-01-07 | 249800.00 | 249800.00 | 246320.00 | 248320.00 | 65526 | 27419 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:41 | 2025-12-09 23:25:41

| 2025-01-08 | 249200.00 | 252920.00 | 249000.00 | 251600.00 | 90294 | 29387 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:41 | 2025-12-09 23:25:41

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 242700.00 | 244970.00 | 242050.00 | 244640.00 | 43325 | 26658 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:41 | 2025-12-09 23:25:41

| 2025-01-03 | 243070.00 | 245620.00 | 241010.00 | 244180.00 | 84133 | 26981 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:41 | 2025-12-09 23:25:41

| 2025-01-06 | 245320.00 | 248950.00 | 244840.00 | 246660.00 | 82641 | 27790 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:41 | 2025-12-09 23:25:41

| 2025-01-07 | 249800.00 | 249800.00 | 246320.00 | 248320.00 | 65526 | 27419 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:41 | 2025-12-09 23:25:41

| 2025-01-08 | 249200.00 | 252920.00 | 249000.00 | 251600.00 | 90294 | 29387 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:41 | 2025-12-09 23:25:41

```

---

### hist_spm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:15


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 5958.00 | 6050.00 | 5918.00 | 6046.00 | 197593 | 150039 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:51 | 2025-12-09 23:25:51

| 2025-01-03 | 6042.00 | 6056.00 | 5990.00 | 6026.00 | 247981 | 149669 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:51 | 2025-12-09 23:25:51

| 2025-01-06 | 6026.00 | 6146.00 | 5996.00 | 6070.00 | 325359 | 161686 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:51 | 2025-12-09 23:25:51

| 2025-01-07 | 6070.00 | 6076.00 | 5922.00 | 5958.00 | 297165 | 126846 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:51 | 2025-12-09 23:25:51

| 2025-01-08 | 5960.00 | 6004.00 | 5936.00 | 5944.00 | 151049 | 118007 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:51 | 2025-12-09 23:25:51

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 5958.00 | 6050.00 | 5918.00 | 6046.00 | 197593 | 150039 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:51 | 2025-12-09 23:25:51

| 2025-01-03 | 6042.00 | 6056.00 | 5990.00 | 6026.00 | 247981 | 149669 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:51 | 2025-12-09 23:25:51

| 2025-01-06 | 6026.00 | 6146.00 | 5996.00 | 6070.00 | 325359 | 161686 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:51 | 2025-12-09 23:25:51

| 2025-01-07 | 6070.00 | 6076.00 | 5922.00 | 5958.00 | 297165 | 126846 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:51 | 2025-12-09 23:25:51

| 2025-01-08 | 5960.00 | 6004.00 | 5936.00 | 5944.00 | 151049 | 118007 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:25:51 | 2025-12-09 23:25:51

```

---

### hist_srm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:15


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 5970.00 | 6024.00 | 5970.00 | 6002.00 | 225660 | 387663 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:33 | 2025-12-09 23:32:33

| 2025-01-03 | 6010.00 | 6029.00 | 5960.00 | 5995.00 | 297714 | 396965 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:33 | 2025-12-09 23:32:33

| 2025-01-06 | 5985.00 | 6036.00 | 5936.00 | 5946.00 | 368560 | 394612 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:33 | 2025-12-09 23:32:33

| 2025-01-07 | 5952.00 | 5973.00 | 5905.00 | 5935.00 | 250131 | 380180 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:33 | 2025-12-09 23:32:33

| 2025-01-08 | 5941.00 | 5949.00 | 5913.00 | 5926.00 | 188991 | 376412 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:33 | 2025-12-09 23:32:33

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 5970.00 | 6024.00 | 5970.00 | 6002.00 | 225660 | 387663 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:33 | 2025-12-09 23:32:33

| 2025-01-03 | 6010.00 | 6029.00 | 5960.00 | 5995.00 | 297714 | 396965 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:33 | 2025-12-09 23:32:33

| 2025-01-06 | 5985.00 | 6036.00 | 5936.00 | 5946.00 | 368560 | 394612 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:33 | 2025-12-09 23:32:33

| 2025-01-07 | 5952.00 | 5973.00 | 5905.00 | 5935.00 | 250131 | 380180 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:33 | 2025-12-09 23:32:33

| 2025-01-08 | 5941.00 | 5949.00 | 5913.00 | 5926.00 | 188991 | 376412 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:33 | 2025-12-09 23:32:33

```

---

### hist_ssm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:15


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 12970.00 | 12990.00 | 12835.00 | 12855.00 | 72727 | 131526 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:01 | 2025-12-09 23:26:01

| 2025-01-03 | 12855.00 | 12855.00 | 12760.00 | 12800.00 | 103906 | 144769 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:01 | 2025-12-09 23:26:01

| 2025-01-06 | 12800.00 | 12875.00 | 12780.00 | 12860.00 | 111985 | 151497 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:01 | 2025-12-09 23:26:01

| 2025-01-07 | 12900.00 | 12940.00 | 12840.00 | 12890.00 | 125695 | 160248 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:01 | 2025-12-09 23:26:01

| 2025-01-08 | 12900.00 | 13080.00 | 12875.00 | 13065.00 | 195487 | 164229 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:01 | 2025-12-09 23:26:01

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 12970.00 | 12990.00 | 12835.00 | 12855.00 | 72727 | 131526 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:01 | 2025-12-09 23:26:01

| 2025-01-03 | 12855.00 | 12855.00 | 12760.00 | 12800.00 | 103906 | 144769 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:01 | 2025-12-09 23:26:01

| 2025-01-06 | 12800.00 | 12875.00 | 12780.00 | 12860.00 | 111985 | 151497 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:01 | 2025-12-09 23:26:01

| 2025-01-07 | 12900.00 | 12940.00 | 12840.00 | 12890.00 | 125695 | 160248 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:01 | 2025-12-09 23:26:01

| 2025-01-08 | 12900.00 | 13080.00 | 12875.00 | 13065.00 | 195487 | 164229 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:26:01 | 2025-12-09 23:26:01

```

---

### hist_tam

- **阿里云**: 324 行 | **腾讯云**: 338 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:15


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 4900.00 | 4992.00 | 4898.00 | 4980.00 | 736416 | 1133790 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:43 | 2025-12-09 23:32:43

| 2025-01-03 | 4996.00 | 5010.00 | 4964.00 | 4980.00 | 556019 | 1116748 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:43 | 2025-12-09 23:32:43

| 2025-01-06 | 4970.00 | 5072.00 | 4952.00 | 4976.00 | 962160 | 1135801 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:44 | 2025-12-09 23:32:44

| 2025-01-07 | 5002.00 | 5014.00 | 4890.00 | 4894.00 | 833004 | 1153379 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:44 | 2025-12-09 23:32:44

| 2025-01-08 | 4904.00 | 4920.00 | 4872.00 | 4902.00 | 589283 | 1203931 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:44 | 2025-12-09 23:32:44

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 4900.00 | 4992.00 | 4898.00 | 4980.00 | 736416 | 1133790 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:43 | 2025-12-09 23:32:43

| 2025-01-03 | 4996.00 | 5010.00 | 4964.00 | 4980.00 | 556019 | 1116748 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:43 | 2025-12-09 23:32:43

| 2025-01-06 | 4970.00 | 5072.00 | 4952.00 | 4976.00 | 962160 | 1135801 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:44 | 2025-12-09 23:32:44

| 2025-01-07 | 5002.00 | 5014.00 | 4890.00 | 4894.00 | 833004 | 1153379 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:44 | 2025-12-09 23:32:44

| 2025-01-08 | 4904.00 | 4920.00 | 4872.00 | 4902.00 | 589283 | 1203931 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:32:44 | 2025-12-09 23:32:44

```

---

### hist_tfm

- **阿里云**: 232 行 | **腾讯云**: 235 行 | **差额**: -3

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:15


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 106.60 | 106.66 | 106.51 | 106.61 | 57808 | 123936 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:08 | 2025-12-09 23:37:08

| 2025-01-03 | 106.69 | 106.99 | 106.64 | 106.97 | 110775 | 124110 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:08 | 2025-12-09 23:37:08

| 2025-01-06 | 106.91 | 106.93 | 106.74 | 106.85 | 74661 | 117780 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:08 | 2025-12-09 23:37:08

| 2025-01-07 | 106.85 | 106.85 | 106.64 | 106.74 | 64425 | 120219 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:08 | 2025-12-09 23:37:08

| 2025-01-08 | 106.74 | 106.76 | 106.64 | 106.71 | 65797 | 121006 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:08 | 2025-12-09 23:37:08

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 106.60 | 106.66 | 106.51 | 106.61 | 57808 | 123936 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:08 | 2025-12-09 23:37:08

| 2025-01-03 | 106.69 | 106.99 | 106.64 | 106.97 | 110775 | 124110 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:08 | 2025-12-09 23:37:08

| 2025-01-06 | 106.91 | 106.93 | 106.74 | 106.85 | 74661 | 117780 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:08 | 2025-12-09 23:37:08

| 2025-01-07 | 106.85 | 106.85 | 106.64 | 106.74 | 64425 | 120219 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:08 | 2025-12-09 23:37:08

| 2025-01-08 | 106.74 | 106.76 | 106.64 | 106.71 | 65797 | 121006 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:08 | 2025-12-09 23:37:08

```

---

### hist_tlm

- **阿里云**: 121 行 | **腾讯云**: 124 行 | **差额**: -3

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:15


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-06-04 | 119.62 | 119.69 | 119.29 | 119.57 | 70260 | 94314 | 83932717056.00 | 0.12 | 0.10 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-09-02 10:57:40 | 2025-09-02 10:57:40

| 2025-06-05 | 119.53 | 119.69 | 119.31 | 119.31 | 66642 | 93443 | 79622467584.00 | -0.19 | -0.16 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-09-02 10:57:40 | 2025-09-02 10:57:40

| 2025-06-06 | 119.50 | 119.82 | 119.50 | 119.78 | 70269 | 96837 | 84083773440.00 | 0.42 | 0.35 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-09-02 10:57:40 | 2025-09-04 17:23:36

| 2025-06-09 | 119.90 | 120.20 | 119.75 | 120.14 | 75638 | 101724 | 90779648000.00 | 0.42 | 0.35 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-09-02 10:57:40 | 2025-09-04 17:23:36

| 2025-06-10 | 120.07 | 120.30 | 120.01 | 120.16 | 62753 | 103965 | 75407527936.00 | 0.09 | 0.07 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-09-02 10:57:40 | 2025-09-04 17:23:36

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-06-04 | 119.62 | 119.69 | 119.29 | 119.57 | 70260 | 94314 | 83932717056.00 | 0.12 | 0.10 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-09-02 10:57:40 | 2025-09-02 10:57:40

| 2025-06-05 | 119.53 | 119.69 | 119.31 | 119.31 | 66642 | 93443 | 79622467584.00 | -0.19 | -0.16 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-09-02 10:57:40 | 2025-09-02 10:57:40

| 2025-06-06 | 119.50 | 119.82 | 119.50 | 119.78 | 70269 | 96837 | 84083773440.00 | 0.42 | 0.35 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-09-02 10:57:40 | 2025-09-04 17:23:36

| 2025-06-09 | 119.90 | 120.20 | 119.75 | 120.14 | 75638 | 101724 | 90779648000.00 | 0.42 | 0.35 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-09-02 10:57:40 | 2025-09-04 17:23:36

| 2025-06-10 | 120.07 | 120.30 | 120.01 | 120.16 | 62753 | 103965 | 75407527936.00 | 0.09 | 0.07 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-09-02 10:57:40 | 2025-09-04 17:23:36

```

---

### hist_tm

- **阿里云**: 122 行 | **腾讯云**: 124 行 | **差额**: -2

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:15


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-06-04 | 108.72 | 108.78 | 108.62 | 108.77 | 55709 | 170547 | 60552974848.00 | 0.10 | 0.09 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-09-02 10:57:37 | 2025-09-02 10:57:37

| 2025-06-05 | 108.72 | 108.86 | 108.70 | 108.72 | 64481 | 169240 | 70134968320.00 | -0.01 | -0.01 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-09-02 10:57:37 | 2025-09-02 10:57:37

| 2025-06-06 | 108.82 | 108.93 | 108.81 | 108.93 | 54263 | 177112 | 59089008384.00 | 0.19 | 0.17 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-09-02 10:57:37 | 2025-09-04 17:23:35

| 2025-06-09 | 108.97 | 109.04 | 108.91 | 109.00 | 60635 | 182042 | 66082457344.00 | 0.10 | 0.09 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-09-02 10:57:37 | 2025-09-04 17:23:35

| 2025-06-10 | 109.00 | 109.03 | 108.95 | 109.00 | 47942 | 184969 | 52252683776.00 | 0.02 | 0.01 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-09-02 10:57:37 | 2025-09-04 17:23:35

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-06-04 | 108.72 | 108.78 | 108.62 | 108.77 | 55709 | 170547 | 60552974848.00 | 0.10 | 0.09 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-09-02 10:57:37 | 2025-09-02 10:57:37

| 2025-06-05 | 108.72 | 108.86 | 108.70 | 108.72 | 64481 | 169240 | 70134968320.00 | -0.01 | -0.01 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-09-02 10:57:37 | 2025-09-02 10:57:37

| 2025-06-06 | 108.82 | 108.93 | 108.81 | 108.93 | 54263 | 177112 | 59089008384.00 | 0.19 | 0.17 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-09-02 10:57:37 | 2025-09-04 17:23:35

| 2025-06-09 | 108.97 | 109.04 | 108.91 | 109.00 | 60635 | 182042 | 66082457344.00 | 0.10 | 0.09 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-09-02 10:57:37 | 2025-09-04 17:23:35

| 2025-06-10 | 109.00 | 109.03 | 108.95 | 109.00 | 47942 | 184969 | 52252683776.00 | 0.02 | 0.01 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-09-02 10:57:37 | 2025-09-04 17:23:35

```

---

### hist_tsm

- **阿里云**: 232 行 | **腾讯云**: 234 行 | **差额**: -2

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:16


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 103.00 | 103.03 | 102.97 | 102.98 | 36083 | 60411 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:20 | 2025-12-09 23:37:20

| 2025-01-03 | 103.00 | 103.15 | 103.00 | 103.15 | 51767 | 59837 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:20 | 2025-12-09 23:37:20

| 2025-01-06 | 103.13 | 103.14 | 103.04 | 103.09 | 39689 | 57141 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:20 | 2025-12-09 23:37:20

| 2025-01-07 | 103.08 | 103.09 | 103.01 | 103.04 | 32694 | 57254 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:20 | 2025-12-09 23:37:20

| 2025-01-08 | 103.04 | 103.05 | 102.98 | 103.00 | 28934 | 57431 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:20 | 2025-12-09 23:37:20

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 103.00 | 103.03 | 102.97 | 102.98 | 36083 | 60411 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:20 | 2025-12-09 23:37:20

| 2025-01-03 | 103.00 | 103.15 | 103.00 | 103.15 | 51767 | 59837 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:20 | 2025-12-09 23:37:20

| 2025-01-06 | 103.13 | 103.14 | 103.04 | 103.09 | 39689 | 57141 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:20 | 2025-12-09 23:37:20

| 2025-01-07 | 103.08 | 103.09 | 103.01 | 103.04 | 32694 | 57254 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:20 | 2025-12-09 23:37:20

| 2025-01-08 | 103.04 | 103.05 | 102.98 | 103.00 | 28934 | 57431 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:37:20 | 2025-12-09 23:37:20

```

---

### hist_urm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:16


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 1700.00 | 1714.00 | 1695.00 | 1697.00 | 144901 | 256014 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:26 | 2025-12-09 23:34:26

| 2025-01-03 | 1680.00 | 1688.00 | 1651.00 | 1659.00 | 216493 | 273380 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:26 | 2025-12-09 23:34:26

| 2025-01-06 | 1651.00 | 1669.00 | 1632.00 | 1658.00 | 226407 | 277840 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:26 | 2025-12-09 23:34:26

| 2025-01-07 | 1654.00 | 1661.00 | 1644.00 | 1647.00 | 109299 | 276313 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:26 | 2025-12-09 23:34:26

| 2025-01-08 | 1645.00 | 1650.00 | 1628.00 | 1631.00 | 138882 | 279880 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:26 | 2025-12-09 23:34:26

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 1700.00 | 1714.00 | 1695.00 | 1697.00 | 144901 | 256014 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:26 | 2025-12-09 23:34:26

| 2025-01-03 | 1680.00 | 1688.00 | 1651.00 | 1659.00 | 216493 | 273380 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:26 | 2025-12-09 23:34:26

| 2025-01-06 | 1651.00 | 1669.00 | 1632.00 | 1658.00 | 226407 | 277840 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:26 | 2025-12-09 23:34:26

| 2025-01-07 | 1654.00 | 1661.00 | 1644.00 | 1647.00 | 109299 | 276313 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:26 | 2025-12-09 23:34:26

| 2025-01-08 | 1645.00 | 1650.00 | 1628.00 | 1631.00 | 138882 | 279880 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:34:26 | 2025-12-09 23:34:26

```

---

### hist_vfm

- **阿里云**: 312 行 | **腾讯云**: 324 行 | **差额**: -12

- 引擎: InnoDB | 创建时间: 2025-11-12 09:16:43


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 5288.00 | 5301.00 | 5231.00 | 5237.00 | 739944 | 999244 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:48 | 2025-12-09 23:31:48

| 2025-01-03 | 5237.00 | 5245.00 | 5133.00 | 5145.00 | 1116837 | 1070838 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:48 | 2025-12-09 23:31:48

| 2025-01-06 | 5150.00 | 5178.00 | 5142.00 | 5150.00 | 775016 | 1062194 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:48 | 2025-12-09 23:31:48

| 2025-01-07 | 5159.00 | 5178.00 | 5084.00 | 5087.00 | 915183 | 1096682 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:48 | 2025-12-09 23:31:48

| 2025-01-08 | 5089.00 | 5113.00 | 5043.00 | 5067.00 | 834512 | 1109727 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:48 | 2025-12-09 23:31:48

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 5288.00 | 5301.00 | 5231.00 | 5237.00 | 739944 | 999244 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:48 | 2025-12-09 23:31:48

| 2025-01-03 | 5237.00 | 5245.00 | 5133.00 | 5145.00 | 1116837 | 1070838 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:48 | 2025-12-09 23:31:48

| 2025-01-06 | 5150.00 | 5178.00 | 5142.00 | 5150.00 | 775016 | 1062194 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:48 | 2025-12-09 23:31:48

| 2025-01-07 | 5159.00 | 5178.00 | 5084.00 | 5087.00 | 915183 | 1096682 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:48 | 2025-12-09 23:31:48

| 2025-01-08 | 5089.00 | 5113.00 | 5043.00 | 5067.00 | 834512 | 1109727 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:31:48 | 2025-12-09 23:31:48

```

---

### hist_vm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:16


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 5288.00 | 5301.00 | 5231.00 | 5237.00 | 739944 | 999244 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:12 | 2025-12-09 23:29:12

| 2025-01-03 | 5237.00 | 5245.00 | 5133.00 | 5145.00 | 1116837 | 1070838 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:12 | 2025-12-09 23:29:12

| 2025-01-06 | 5150.00 | 5178.00 | 5142.00 | 5150.00 | 775016 | 1062194 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:12 | 2025-12-09 23:29:12

| 2025-01-07 | 5159.00 | 5178.00 | 5084.00 | 5087.00 | 915183 | 1096682 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:12 | 2025-12-09 23:29:12

| 2025-01-08 | 5089.00 | 5113.00 | 5043.00 | 5067.00 | 834512 | 1109727 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:12 | 2025-12-09 23:29:12

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 5288.00 | 5301.00 | 5231.00 | 5237.00 | 739944 | 999244 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:12 | 2025-12-09 23:29:12

| 2025-01-03 | 5237.00 | 5245.00 | 5133.00 | 5145.00 | 1116837 | 1070838 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:12 | 2025-12-09 23:29:12

| 2025-01-06 | 5150.00 | 5178.00 | 5142.00 | 5150.00 | 775016 | 1062194 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:12 | 2025-12-09 23:29:12

| 2025-01-07 | 5159.00 | 5178.00 | 5084.00 | 5087.00 | 915183 | 1096682 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:12 | 2025-12-09 23:29:12

| 2025-01-08 | 5089.00 | 5113.00 | 5043.00 | 5067.00 | 834512 | 1109727 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:29:12 | 2025-12-09 23:29:12

```

---

### hist_wrm

- **阿里云**: 224 行 | **腾讯云**: 236 行 | **差额**: -12

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:16


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-05-06 | 3403.00 | 3414.00 | 3381.00 | 3414.00 | 122 | 68 | 4137720.00 | 13.00 | 0.38 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:18:20 | 2025-12-09 22:20:29

| 2025-05-07 | 3403.00 | 3414.00 | 3381.00 | 3414.00 | 122 | 68 | 4137720.00 | 13.00 | 0.38 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:20:46 | 2025-12-09 22:20:46

| 2025-05-08 | 3403.00 | 3414.00 | 3381.00 | 3414.00 | 122 | 68 | 4137720.00 | 13.00 | 0.38 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:05 | 2025-12-09 22:21:05

| 2025-05-09 | 3403.00 | 3414.00 | 3381.00 | 3414.00 | 122 | 68 | 4137720.00 | 13.00 | 0.38 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:23 | 2025-12-09 22:21:23

| 2025-05-12 | 3403.00 | 3414.00 | 3381.00 | 3414.00 | 122 | 68 | 4137720.00 | 13.00 | 0.38 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:41 | 2025-12-09 22:21:41

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-05-06 | 3403.00 | 3414.00 | 3381.00 | 3414.00 | 122 | 68 | 4137720.00 | 13.00 | 0.38 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:18:20 | 2025-12-09 22:20:29

| 2025-05-07 | 3403.00 | 3414.00 | 3381.00 | 3414.00 | 122 | 68 | 4137720.00 | 13.00 | 0.38 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:20:46 | 2025-12-09 22:20:46

| 2025-05-08 | 3403.00 | 3414.00 | 3381.00 | 3414.00 | 122 | 68 | 4137720.00 | 13.00 | 0.38 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:05 | 2025-12-09 22:21:05

| 2025-05-09 | 3403.00 | 3414.00 | 3381.00 | 3414.00 | 122 | 68 | 4137720.00 | 13.00 | 0.38 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:23 | 2025-12-09 22:21:23

| 2025-05-12 | 3403.00 | 3414.00 | 3381.00 | 3414.00 | 122 | 68 | 4137720.00 | 13.00 | 0.38 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 22:21:41 | 2025-12-09 22:21:41

```

---

### hist_ym

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:16


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 7734.00 | 7894.00 | 7712.00 | 7724.00 | 566122 | 649476 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:33 | 2025-12-09 23:28:33

| 2025-01-03 | 7730.00 | 7758.00 | 7590.00 | 7612.00 | 537549 | 656822 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:33 | 2025-12-09 23:28:33

| 2025-01-06 | 7600.00 | 7658.00 | 7552.00 | 7560.00 | 444319 | 667454 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:33 | 2025-12-09 23:28:33

| 2025-01-07 | 7602.00 | 7632.00 | 7524.00 | 7596.00 | 472949 | 668424 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:33 | 2025-12-09 23:28:33

| 2025-01-08 | 7582.00 | 7602.00 | 7520.00 | 7552.00 | 463855 | 665638 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:33 | 2025-12-09 23:28:33

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 7734.00 | 7894.00 | 7712.00 | 7724.00 | 566122 | 649476 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:33 | 2025-12-09 23:28:33

| 2025-01-03 | 7730.00 | 7758.00 | 7590.00 | 7612.00 | 537549 | 656822 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:33 | 2025-12-09 23:28:33

| 2025-01-06 | 7600.00 | 7658.00 | 7552.00 | 7560.00 | 444319 | 667454 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:33 | 2025-12-09 23:28:33

| 2025-01-07 | 7602.00 | 7632.00 | 7524.00 | 7596.00 | 472949 | 668424 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:33 | 2025-12-09 23:28:33

| 2025-01-08 | 7582.00 | 7602.00 | 7520.00 | 7552.00 | 463855 | 665638 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:28:33 | 2025-12-09 23:28:33

```

---

### hist_znm

- **阿里云**: 323 行 | **腾讯云**: 337 行 | **差额**: -14

- 引擎: InnoDB | 创建时间: 2025-09-16 16:45:16


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | trade_date                     | date                 | NO    | PRI  | None       |
  | open_price                     | decimal(10,2)        | NO    |      | None       |
  | high_price                     | decimal(10,2)        | NO    |      | None       |
  | low_price                      | decimal(10,2)        | NO    |      | None       |
  | close_price                    | decimal(10,2)        | NO    |      | None       |
  | volume                         | bigint               | NO    |      | 0          |
  | open_interest                  | bigint               | NO    |      | 0          |
  | turnover                       | decimal(20,2)        | NO    |      | 0.00       |
  | price_change                   | decimal(10,2)        | YES   |      | 0.00       |
  | change_pct                     | decimal(10,2)        | YES   |      | 0.00       |
  | macd_dif                       | decimal(10,4)        | YES   |      | None       |
  | macd_dea                       | decimal(10,4)        | YES   |      | None       |
  | macd_histogram                 | decimal(10,4)        | YES   |      | None       |
  | rsi_14                         | decimal(6,2)         | YES   |      | None       |
  | kdj_k                          | decimal(6,2)         | YES   |      | None       |
  | kdj_d                          | decimal(6,2)         | YES   |      | None       |
  | kdj_j                          | decimal(6,2)         | YES   |      | None       |
  | bb_upper                       | decimal(10,2)        | YES   |      | None       |
  | bb_middle                      | decimal(10,2)        | YES   |      | None       |
  | bb_lower                       | decimal(10,2)        | YES   |      | None       |
  | bb_width                       | decimal(10,2)        | YES   |      | None       |
  | recommendation                 | varchar(20)          | YES   |      | None       |
  | source_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | ingest_ts                      | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 25240.00 | 25305.00 | 25100.00 | 25265.00 | 116495 | 130684 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:38 | 2025-12-09 23:24:38

| 2025-01-03 | 24920.00 | 25040.00 | 24535.00 | 24665.00 | 207727 | 114750 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:38 | 2025-12-09 23:24:38

| 2025-01-06 | 24495.00 | 24595.00 | 24390.00 | 24490.00 | 158904 | 109182 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:38 | 2025-12-09 23:24:38

| 2025-01-07 | 24670.00 | 24760.00 | 24310.00 | 24395.00 | 156531 | 104494 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:38 | 2025-12-09 23:24:38

| 2025-01-08 | 24340.00 | 24420.00 | 24085.00 | 24225.00 | 138138 | 102938 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:38 | 2025-12-09 23:24:38

```


**腾讯云 示例数据 (前5行):**

```
| trade_date | open_price | high_price | low_price | close_price | volume | open_interest | turnover | price_change | change_pct | macd_dif | macd_dea | macd_histogram | rsi_14 | kdj_k | kdj_d | kdj_j | bb_upper | bb_middle | bb_lower | bb_width | recommendation | source_ts | ingest_ts

| 2025-01-02 | 25240.00 | 25305.00 | 25100.00 | 25265.00 | 116495 | 130684 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:38 | 2025-12-09 23:24:38

| 2025-01-03 | 24920.00 | 25040.00 | 24535.00 | 24665.00 | 207727 | 114750 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:38 | 2025-12-09 23:24:38

| 2025-01-06 | 24495.00 | 24595.00 | 24390.00 | 24490.00 | 158904 | 109182 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:38 | 2025-12-09 23:24:38

| 2025-01-07 | 24670.00 | 24760.00 | 24310.00 | 24395.00 | 156531 | 104494 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:38 | 2025-12-09 23:24:38

| 2025-01-08 | 24340.00 | 24420.00 | 24085.00 | 24225.00 | 138138 | 102938 | 0.00 | 0.00 | 0.00 | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | NULL | 2025-12-09 23:24:38 | 2025-12-09 23:24:38

```

---

### history_update_log

- **阿里云**: 0 行 | **腾讯云**: 0 行 | **差额**: 相同

- 引擎: InnoDB | 创建时间: 2025-12-21 10:53:50


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | id                             | int                  | NO    | PRI  | None       |
  | contract_symbol                | varchar(20)          | NO    | UNI  | None       |
  | name                           | varchar(50)          | NO    |      | None       |
  | target_table                   | varchar(50)          | NO    |      | None       |
  | start_time                     | timestamp            | YES   |      | None       |
  | end_time                       | timestamp            | YES   |      | None       |
  | data_start_date                | date                 | YES   |      | None       |
  | data_end_date                  | date                 | YES   |      | None       |
  | status                         | enum('success','failure') | YES   | MUL  | failure    |
  | error_message                  | text                 | YES   |      | None       |
  | retry_count                    | int                  | YES   |      | 0          |
  | created_at                     | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | updated_at                     | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```

---

### news_process_tracking

- **阿里云**: 13885 行 | **腾讯云**: 15593 行 | **差额**: -1708

- 引擎: InnoDB | 创建时间: 2025-09-30 17:16:13


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | id                             | bigint               | NO    | PRI  | None       |
  | news_id                        | bigint               | NO    | UNI  | None       |
  | ctime                          | bigint               | NO    | MUL  | None       |
  | is_reviewed                    | tinyint(1)           | NO    | MUL  | 0          |
  | review_time                    | timestamp            | YES   |      | None       |
  | track_day3_done                | tinyint(1)           | NO    | MUL  | 0          |
  | track_day3_time                | timestamp            | YES   |      | None       |
  | track_day7_done                | tinyint(1)           | NO    |      | 0          |
  | track_day7_time                | timestamp            | YES   |      | None       |
  | track_day14_done               | tinyint(1)           | NO    |      | 0          |
  | track_day14_time               | timestamp            | YES   |      | None       |
  | track_day28_done               | tinyint(1)           | NO    |      | 0          |
  | track_day28_time               | timestamp            | YES   |      | None       |
  | created_at                     | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | updated_at                     | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| id | news_id | ctime | is_reviewed | review_time | track_day3_done | track_day3_time | track_day7_done | track_day7_time | track_day14_done | track_day14_time | track_day28_done | track_day28_time | created_at | updated_at

| 1 | 20 | 1758293626 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 18:18:05 | 1 | 2025-09-30 22:11:16 | 1 | 2025-10-04 08:12:31 | 1 | 2025-10-20 16:55:29 | 2025-09-30 17:19:44 | 2025-10-20 16:55:29

| 2 | 19 | 1758312031 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 2025-09-30 17:19:44 | 2025-09-30 17:31:31

| 3 | 18 | 1758319224 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 2025-09-30 17:19:44 | 2025-09-30 17:31:31

| 4 | 17 | 1758320430 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 2025-09-30 17:19:45 | 2025-09-30 17:31:31

| 5 | 16 | 1758334598 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 2025-09-30 17:19:45 | 2025-09-30 17:31:31

```


**腾讯云 示例数据 (前5行):**

```
| id | news_id | ctime | is_reviewed | review_time | track_day3_done | track_day3_time | track_day7_done | track_day7_time | track_day14_done | track_day14_time | track_day28_done | track_day28_time | created_at | updated_at

| 1 | 20 | 1758293626 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 18:18:05 | 1 | 2025-09-30 22:11:16 | 1 | 2025-10-04 08:12:31 | 1 | 2025-10-20 16:55:29 | 2025-09-30 17:19:44 | 2025-10-20 16:55:29

| 2 | 19 | 1758312031 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 2025-09-30 17:19:44 | 2025-09-30 17:31:31

| 3 | 18 | 1758319224 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 2025-09-30 17:19:44 | 2025-09-30 17:31:31

| 4 | 17 | 1758320430 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 2025-09-30 17:19:45 | 2025-09-30 17:31:31

| 5 | 16 | 1758334598 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 1 | 2025-09-30 17:31:31 | 2025-09-30 17:19:45 | 2025-09-30 17:31:31

```

---

### news_red_telegraph

- **阿里云**: 13885 行 | **腾讯云**: 15593 行 | **差额**: -1708

- 引擎: InnoDB | 创建时间: 2025-09-25 09:49:29


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | id                             | bigint               | NO    | PRI  | None       |
  | ctime                          | bigint               | NO    | UNI  | None       |
  | title                          | varchar(500)         | NO    |      | None       |
  | content                        | text                 | NO    |      | None       |
  | ai_analysis                    | mediumtext           | YES   |      | None       |
  | message_score                  | tinyint unsigned     | YES   | MUL  | None       |
  | message_label                  | enum('hard','soft','unknown') | NO    | MUL  | unknown    |
  | message_type                   | varchar(64)          | YES   |      | None       |
  | market_react                   | varchar(255)         | YES   |      | None       |
  | screenshots                    | json                 | YES   |      | None       |
  | created_at                     | timestamp            | NO    | MUL  | CURRENT_TIMESTAMP |
  | updated_at                     | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | message_score_rationale        | varchar(500)         | YES   |      | None       |
  | message_type_rationale         | varchar(500)         | YES   |      | None       |
```


**阿里云 示例数据 (前5行):**

```
| id | ctime | title | content | ai_analysis | message_score | message_label | message_type | market_react | screenshots | created_at | updated_at | message_score_rationale | message_type_rationale

| 1 | 1758457187 | 9月21周日《新闻联播》要闻25条 | 【9月21周日《新闻联播》要闻25条】财联社9月21日电，今天《新闻联播》主要内 | - 股票市场，分类：软消息  
- 理由：该消息主要涉及政治、文化及社会发展等内 | 45 | hard | 其他 | NULL | NULL | 2025-09-21 21:02:34 | 2025-09-30 17:53:57 | 虽然新闻中包含了一些经济和国际关系的内容，但大部分信息较为笼统，缺乏具体的可验证 | 该新闻内容主要是对《新闻联播》要闻的汇总，不符合上述任何特定财经消息类型。

| 2 | 1758456047 | 国务院食安办等部门积极推进预制菜国家标准制定和餐饮环节使用明示 | 【国务院食安办等部门积极推进预制菜国家标准制定和餐饮环节使用明示】财联社9月21 | - 期货市场，分类：软消息  
- 理由：该消息主要涉及政策推动和行业标准，间接 | 65 | unknown | 利好政策 | NULL | NULL | 2025-09-21 21:02:34 | 2025-09-27 09:57:34 | 该消息涉及国家标准的制定，具有一定的政策导向和市场影响，但具体实施细节和时间未明 | 这则新闻涉及国务院等部门积极推进预制菜国家标准的制定，属于对行业的支持和规范，有

| 3 | 1758455489 | 超20家A股上市公司本周披露并购重组最新公告 向日葵拟购买高端半导体材料公司兮璞 | 【超20家A股上市公司本周披露并购重组最新公告 向日葵拟购买高端半导体材料公司兮 | - 股票市场，分类：硬消息  
- 理由：消息涉及多个上市公司的并购重组情况，直 | 75 | unknown | 并购重组 / 并购落地 | NULL | NULL | 2025-09-21 21:02:34 | 2025-09-27 09:57:34 | 该消息涉及多家上市公司的并购重组，具体且可验证，可能对相关股票产生短期影响，尤其 | 新闻内容提到多家上市公司披露并购重组公告，特别是向日葵拟购买兮璞材料100%股权

| 4 | 1758455188 | 李强会见美国国会众议员代表团 | 【李强会见美国国会众议员代表团】财联社9月21日电，据央视新闻报道，国务院总理李 | - 期货市场，分类：软消息  
- 理由：消息主要涉及中美关系的政治表态，间接影 | 65 | unknown | 其他 | NULL | NULL | 2025-09-21 21:02:34 | 2025-09-27 13:57:28 | 这条新闻传达了中美关系的积极信号，可能对市场产生正面影响，但缺乏具体的可验证数据 | 这条新闻主要涉及中美关系的外交会谈，不属于财经消息的具体分类。

| 5 | 1758451712 | 臻镭科技：公司实际控制人、董事长郁发新被实施留置措施 | 【臻镭科技：公司实际控制人、董事长郁发新被实施留置措施】财联社9月21日电，臻镭 | - 股票市场，分类：硬消息  
- 理由：公司实际控制人被实施留置措施，直接影响 | 60 | unknown | 其他 | NULL | NULL | 2025-09-21 21:02:34 | 2025-09-27 13:57:28 | 该消息涉及公司实际控制人被实施留置措施，虽然公司表示不会对经营产生重大影响，但仍 | 该新闻主要涉及公司高层被留置的情况，属于公司治理和管理层变动，不符合其他具体的财

```


**腾讯云 示例数据 (前5行):**

```
| id | ctime | title | content | ai_analysis | message_score | message_label | message_type | market_react | screenshots | created_at | updated_at | message_score_rationale | message_type_rationale

| 1 | 1758457187 | 9月21周日《新闻联播》要闻25条 | 【9月21周日《新闻联播》要闻25条】财联社9月21日电，今天《新闻联播》主要内 | - 股票市场，分类：软消息  
- 理由：该消息主要涉及政治、文化及社会发展等内 | 45 | hard | 其他 | NULL | NULL | 2025-09-21 21:02:34 | 2025-09-30 17:53:57 | 虽然新闻中包含了一些经济和国际关系的内容，但大部分信息较为笼统，缺乏具体的可验证 | 该新闻内容主要是对《新闻联播》要闻的汇总，不符合上述任何特定财经消息类型。

| 2 | 1758456047 | 国务院食安办等部门积极推进预制菜国家标准制定和餐饮环节使用明示 | 【国务院食安办等部门积极推进预制菜国家标准制定和餐饮环节使用明示】财联社9月21 | - 期货市场，分类：软消息  
- 理由：该消息主要涉及政策推动和行业标准，间接 | 65 | unknown | 利好政策 | NULL | NULL | 2025-09-21 21:02:34 | 2025-09-27 09:57:34 | 该消息涉及国家标准的制定，具有一定的政策导向和市场影响，但具体实施细节和时间未明 | 这则新闻涉及国务院等部门积极推进预制菜国家标准的制定，属于对行业的支持和规范，有

| 3 | 1758455489 | 超20家A股上市公司本周披露并购重组最新公告 向日葵拟购买高端半导体材料公司兮璞 | 【超20家A股上市公司本周披露并购重组最新公告 向日葵拟购买高端半导体材料公司兮 | - 股票市场，分类：硬消息  
- 理由：消息涉及多个上市公司的并购重组情况，直 | 75 | unknown | 并购重组 / 并购落地 | NULL | NULL | 2025-09-21 21:02:34 | 2025-09-27 09:57:34 | 该消息涉及多家上市公司的并购重组，具体且可验证，可能对相关股票产生短期影响，尤其 | 新闻内容提到多家上市公司披露并购重组公告，特别是向日葵拟购买兮璞材料100%股权

| 4 | 1758455188 | 李强会见美国国会众议员代表团 | 【李强会见美国国会众议员代表团】财联社9月21日电，据央视新闻报道，国务院总理李 | - 期货市场，分类：软消息  
- 理由：消息主要涉及中美关系的政治表态，间接影 | 65 | unknown | 其他 | NULL | NULL | 2025-09-21 21:02:34 | 2025-09-27 13:57:28 | 这条新闻传达了中美关系的积极信号，可能对市场产生正面影响，但缺乏具体的可验证数据 | 这条新闻主要涉及中美关系的外交会谈，不属于财经消息的具体分类。

| 5 | 1758451712 | 臻镭科技：公司实际控制人、董事长郁发新被实施留置措施 | 【臻镭科技：公司实际控制人、董事长郁发新被实施留置措施】财联社9月21日电，臻镭 | - 股票市场，分类：硬消息  
- 理由：公司实际控制人被实施留置措施，直接影响 | 60 | unknown | 其他 | NULL | NULL | 2025-09-21 21:02:34 | 2025-09-27 13:57:28 | 该消息涉及公司实际控制人被实施留置措施，虽然公司表示不会对经营产生重大影响，但仍 | 该新闻主要涉及公司高层被留置的情况，属于公司治理和管理层变动，不符合其他具体的财

```

---

### recommendation_log

- **阿里云**: 9 行 | **腾讯云**: 9 行 | **差额**: 相同

- 引擎: InnoDB | 创建时间: 2025-09-16 17:21:26


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | id                             | int                  | NO    | PRI  | None       |
  | date                           | date                 | NO    | UNI  | None       |
  | long_names                     | text                 | YES   |      | None       |
  | short_names                    | text                 | YES   |      | None       |
  | total_long_count               | int                  | YES   |      | 0          |
  | total_short_count              | int                  | YES   |      | 0          |
  | created_at                     | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | updated_at                     | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| id | date | long_names | short_names | total_long_count | total_short_count | created_at | updated_at

| 1 | 2025-09-16 | 胶合板主连（3），淀粉主连（3），苯乙烯主连（3），欧线集运主连（3），铁矿石主 | 苹果主连（-3），国际铜主连（-3），丁二烯胶主连（-3），红枣主连（-3），沪 | 17 | 7 | 2025-09-16 17:26:35 | 2025-09-16 17:36:25

| 3 | 2025-09-17 | 豆一主连（3），玉米主连（3），淀粉主连（5），铁矿石主连（3），中证1000股 | 氧化铝主连（-3），豆二主连（-3），丁二烯胶主连（-5），棉纱主连（-4），焦 | 13 | 10 | 2025-09-17 17:27:27 | 2025-09-17 17:27:27

| 4 | 2025-09-19 | 氧化铝主连（6），燃油主连（4），鸡蛋主连（3），生猪主连（3），菜油主连（3） | 沥青主连（-5），沪铜主连（-5），LPG主连（-3），沪锡主连（-3），不锈钢 | 6 | 6 | 2025-09-19 09:05:33 | 2025-09-19 09:05:33

| 5 | 2025-09-22 | 苹果主连（3），沪金主连（3），胶合板主连（5），国际铜主连（3），棉花主连（3 | 沥青主连（-3），玉米主连（-5），淀粉主连（-3），苯乙烯主连（-4），甲醇主 | 15 | 6 | 2025-09-22 21:28:57 | 2025-09-22 21:28:57

| 6 | 2025-09-23 | 淀粉主连（3），苯乙烯主连（4），生猪主连（3），聚丙烯主连（3），对二甲苯主连 | 铸造铝主连（-3），豆一主连（-4），苹果主连（-4），国际铜主连（-4），丁二 | 6 | 23 | 2025-09-23 17:12:09 | 2025-09-23 17:12:09

```


**腾讯云 示例数据 (前5行):**

```
| id | date | long_names | short_names | total_long_count | total_short_count | created_at | updated_at

| 1 | 2025-09-16 | 胶合板主连（3），淀粉主连（3），苯乙烯主连（3），欧线集运主连（3），铁矿石主 | 苹果主连（-3），国际铜主连（-3），丁二烯胶主连（-3），红枣主连（-3），沪 | 17 | 7 | 2025-09-16 17:26:35 | 2025-09-16 17:36:25

| 3 | 2025-09-17 | 豆一主连（3），玉米主连（3），淀粉主连（5），铁矿石主连（3），中证1000股 | 氧化铝主连（-3），豆二主连（-3），丁二烯胶主连（-5），棉纱主连（-4），焦 | 13 | 10 | 2025-09-17 17:27:27 | 2025-09-17 17:27:27

| 4 | 2025-09-19 | 氧化铝主连（6），燃油主连（4），鸡蛋主连（3），生猪主连（3），菜油主连（3） | 沥青主连（-5），沪铜主连（-5），LPG主连（-3），沪锡主连（-3），不锈钢 | 6 | 6 | 2025-09-19 09:05:33 | 2025-09-19 09:05:33

| 5 | 2025-09-22 | 苹果主连（3），沪金主连（3），胶合板主连（5），国际铜主连（3），棉花主连（3 | 沥青主连（-3），玉米主连（-5），淀粉主连（-3），苯乙烯主连（-4），甲醇主 | 15 | 6 | 2025-09-22 21:28:57 | 2025-09-22 21:28:57

| 6 | 2025-09-23 | 淀粉主连（3），苯乙烯主连（4），生猪主连（3），聚丙烯主连（3），对二甲苯主连 | 铸造铝主连（-3），豆一主连（-4），苹果主连（-4），国际铜主连（-4），丁二 | 6 | 23 | 2025-09-23 17:12:09 | 2025-09-23 17:12:09

```

---

### system_config

- **阿里云**: 1 行 | **腾讯云**: 1 行 | **差额**: 相同

- 引擎: InnoDB | 创建时间: 2025-08-31 17:13:29


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | id                             | int                  | NO    | PRI  | None       |
  | auto_update_enabled            | tinyint(1)           | YES   |      | 0          |
  | daily_update_time              | time                 | YES   |      | 17:00:00   |
  | multithread_enabled            | tinyint(1)           | YES   |      | 1          |
  | concurrency                    | int                  | YES   |      | 5          |
  | timeout_seconds                | int                  | YES   |      | 60         |
  | created_at                     | timestamp            | NO    |      | CURRENT_TIMESTAMP |
  | updated_at                     | timestamp            | NO    |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前1行):**

```
| id | auto_update_enabled | daily_update_time | multithread_enabled | concurrency | timeout_seconds | created_at | updated_at

| 1 | 0 | 17:00:00 | 1 | 2 | 90 | 2025-08-31 17:13:29 | 2025-11-12 09:13:19

```


**腾讯云 示例数据 (前1行):**

```
| id | auto_update_enabled | daily_update_time | multithread_enabled | concurrency | timeout_seconds | created_at | updated_at

| 1 | 0 | 17:00:00 | 1 | 2 | 90 | 2025-08-31 17:13:29 | 2025-11-12 09:13:19

```

---

### trading_account_daily

- **阿里云**: 2 行 | **腾讯云**: 13 行 | **差额**: -11

- 引擎: InnoDB | 创建时间: 2026-04-24 11:17:40


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | id                             | int                  | NO    | PRI  | None       |
  | record_date                    | date                 | NO    | UNI  | None       |
  | equity                         | float                | NO    |      | None       |
  | cash                           | float                | NO    |      | None       |
  | position_val                   | float                | YES   |      | 0          |
  | daily_pnl                      | float                | YES   |      | 0          |
  | created_at                     | datetime             | YES   |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前2行):**

```
| id | record_date | equity | cash | position_val | daily_pnl | created_at

| 1 | 2026-04-24 | 31153.2 | 0.03 | 31153.2 | 1153.25 | 2026-04-24 11:17:41

| 2 | 2026-04-23 | 30000.0 | 0.03 | 30000.0 | 1020.27 | 2026-04-24 11:19:53

```


**腾讯云 示例数据 (前5行):**

```
| id | record_date | equity | cash | position_val | daily_pnl | created_at

| 16 | 2026-04-29 | 30000.0 | 20000.0 | 9999.99 | 0.0 | 2026-04-29 21:29:31

| 19 | 2026-04-30 | 30594.0 | 20000.0 | 10594.0 | 593.99 | 2026-04-30 20:40:25

| 21 | 2026-05-06 | 29518.6 | 19783.9 | 9734.77 | -1075.36 | 2026-05-06 19:57:00

| 22 | 2026-05-07 | 29723.9 | 20125.1 | 9598.86 | 205.347 | 2026-05-07 19:01:19

| 23 | 2026-05-08 | 31174.3 | 238.815 | 30935.5 | 1450.45 | 2026-05-08 19:42:44

```

---

### trading_operations

- **阿里云**: 2 行 | **腾讯云**: 8 行 | **差额**: -6

- 引擎: InnoDB | 创建时间: 2026-04-25 18:08:49


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | id                             | int                  | NO    | PRI  | None       |
  | signal_id                      | int                  | YES   |      | None       |
  | signal_date                    | date                 | NO    | MUL  | None       |
  | variety_id                     | int                  | NO    |      | None       |
  | variety_name                   | varchar(20)          | YES   |      | None       |
  | sector                         | varchar(20)          | YES   |      | None       |
  | signal_type                    | varchar(20)          | NO    |      | None       |
  | main_score                     | float                | YES   |      | None       |
  | is_selected                    | tinyint(1)           | YES   |      | 0          |
  | reject_reason                  | varchar(30)          | YES   |      | None       |
  | extra_json                     | json                 | YES   |      | None       |
  | created_at                     | datetime             | YES   |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前2行):**

```
| id | signal_id | signal_date | variety_id | variety_name | sector | signal_type | main_score | is_selected | reject_reason | extra_json | created_at

| 4 | 145 | 2026-04-23 | 13 | 沪金 | 贵金属 | A_OPEN_SHORT | 0.733333 | 1 | NULL | {"rank_note": "selected"} | 2026-04-25 18:26:34

| 6 | 152 | 2026-04-24 | 28 | PTA | 化工能化 | A_OPEN_LONG | 0.466667 | 0 | capacity_full | {"rank_note": "capacity_full"} | 2026-04-25 20:40:26

```


**腾讯云 示例数据 (前5行):**

```
| id | signal_id | signal_date | variety_id | variety_name | sector | signal_type | operation_type | direction | signal_cycle_id | main_score | is_selected | reject_reason | selection_rank | extra_json | created_at

| 12 | 174 | 2026-04-29 | 40 | 氧化铝 | 有色金属 | A_OPEN_SHORT | OPEN | SHORT | 40-SHORT-2026-04-29 | 0.5 | 1 | NULL | 1 | {"rank_note": "selected", "selection_ran | 2026-04-29 21:30:56

| 13 | 188 | 2026-05-08 | 28 | PTA | 化工能化 | A_OPEN_SHORT | OPEN | SHORT | 28-SHORT-2026-05-08 | 0.966667 | 1 | NULL | 1 | {"rank_note": "selected", "selection_ran | 2026-05-08 19:42:44

| 14 | 186 | 2026-05-08 | 17 | 豆粕 | 油脂油料 | A_OPEN_SHORT | OPEN | SHORT | 17-SHORT-2026-05-08 | 0.5 | 1 | NULL | 3 | {"rank_note": "selected", "selection_ran | 2026-05-08 19:42:44

| 15 | 190 | 2026-05-08 | 45 | 低硫燃油 | 化工能化 | A_OPEN_SHORT | OPEN | SHORT | 45-SHORT-2026-05-08 | 0.866667 | 0 | sector_conflict | 2 | {"rank_note": "sector_conflict"} | 2026-05-08 19:42:44

| 16 | 195 | 2026-05-12 | 6 | 沪铝 | 有色金属 | A_OPEN_LONG | OPEN | LONG | 6-LONG-2026-05-12 | 0.566667 | 0 | capacity_full | NULL | {"rank_note": "capacity_full"} | 2026-05-12 19:49:25

```

---

### trading_pool

- **阿里云**: 55 行 | **腾讯云**: 55 行 | **差额**: 相同

- 引擎: InnoDB | 创建时间: 2026-04-24 11:17:40


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | id                             | int                  | NO    | PRI  | None       |
  | variety_id                     | int                  | NO    | UNI  | None       |
  | variety_name                   | varchar(20)          | YES   |      | None       |
  | sector                         | varchar(20)          | NO    |      | None       |
  | is_active                      | tinyint(1)           | YES   |      | 1          |
  | created_at                     | datetime             | YES   |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| id | variety_id | variety_name | sector | is_active | created_at

| 1 | 5 | 沪铜 | 有色金属 | 1 | 2026-04-24 11:17:40

| 2 | 6 | 沪铝 | 有色金属 | 1 | 2026-04-24 11:17:40

| 3 | 7 | 沪锌 | 有色金属 | 1 | 2026-04-24 11:17:40

| 4 | 13 | 沪金 | 贵金属 | 1 | 2026-04-24 11:17:40

| 5 | 1 | 铁矿石 | 黑色系 | 1 | 2026-04-24 11:17:40

```


**腾讯云 示例数据 (前5行):**

```
| id | variety_id | variety_name | sector | is_active | created_at

| 1 | 5 | 沪铜 | 有色金属 | 0 | 2026-04-24 11:17:40

| 2 | 6 | 沪铝 | 有色金属 | 1 | 2026-04-24 11:17:40

| 3 | 7 | 沪锌 | 有色金属 | 0 | 2026-04-24 11:17:40

| 4 | 13 | 沪金 | 贵金属 | 1 | 2026-04-24 11:17:40

| 5 | 1 | 铁矿石 | 黑色系 | 0 | 2026-04-24 11:17:40

```

---

### trading_positions

- **阿里云**: 3 行 | **腾讯云**: 4 行 | **差额**: -1

- 引擎: InnoDB | 创建时间: 2026-04-24 11:17:40


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | id                             | int                  | NO    | PRI  | None       |
  | operation_id                   | int                  | YES   |      | None       |
  | variety_id                     | int                  | NO    |      | None       |
  | variety_name                   | varchar(20)          | YES   |      | None       |
  | sector                         | varchar(20)          | YES   |      | None       |
  | direction                      | varchar(10)          | NO    |      | None       |
  | open_date                      | date                 | NO    |      | None       |
  | open_price                     | float                | NO    |      | None       |
  | close_date                     | date                 | YES   |      | None       |
  | close_price                    | float                | YES   |      | None       |
  | size_pct                       | float                | YES   |      | 0.3333     |
  | status                         | varchar(10)          | YES   | MUL  | open       |
  | pnl_pct                        | float                | YES   |      | None       |
  | created_at                     | datetime             | YES   |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前3行):**

```
| id | operation_id | variety_id | variety_name | sector | direction | open_date | open_price | close_date | close_price | size_pct | status | pnl_pct | created_at

| 1 | 3 | 6 | 沪铝 | 有色金属 | SHORT | 2026-04-23 | 24970.0 | NULL | NULL | 0.333333 | open | NULL | 2026-04-24 11:19:53

| 2 | 2 | 13 | 沪金 | 贵金属 | SHORT | 2026-04-23 | 1040.06 | NULL | NULL | 0.333333 | open | NULL | 2026-04-24 11:19:53

| 3 | 1 | 20 | 棕榈油 | 油脂油料 | LONG | 2026-04-23 | 9781.0 | NULL | NULL | 0.333333 | open | NULL | 2026-04-24 11:19:53

```


**腾讯云 示例数据 (前4行):**

```
| id | operation_id | open_operation_id | open_signal_id | close_signal_id | theory_cycle_id | variety_id | variety_name | sector | direction | open_date | open_price | close_date | close_price | size_pct | status | pnl_pct | created_at

| 13 | 12 | 12 | 174 | NULL | 40-SHORT-2026-04-29 | 40 | 氧化铝 | 有色金属 | SHORT | 2026-04-29 | 2862.0 | NULL | NULL | 0.333333 | open | NULL | 2026-04-29 21:30:02

| 14 | 14 | 14 | 186 | 200 | 17-SHORT-2026-05-08 | 17 | 豆粕 | 油脂油料 | SHORT | 2026-05-08 | 3003.0 | 2026-05-13 | 3048.0 | 0.333333 | closed | -0.014985 | 2026-05-08 19:42:44

| 15 | 13 | 13 | 188 | 207 | 28-SHORT-2026-05-08 | 28 | PTA | 化工能化 | SHORT | 2026-05-08 | 6338.0 | 2026-05-15 | 6394.0 | 0.333333 | closed | -0.0088356 | 2026-05-08 19:42:44

| 16 | 19 | 19 | 210 | NULL | 17-SHORT-2026-05-18 | 17 | 豆粕 | 油脂油料 | SHORT | 2026-05-18 | 2985.0 | NULL | NULL | 0.333333 | open | NULL | 2026-05-18 20:33:43

```

---

### trading_signal_state

- **阿里云**: 110 行 | **腾讯云**: 0 行 | **差额**: +110

- 引擎: InnoDB | 创建时间: 2026-04-25 18:08:49


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | variety_id                     | int                  | NO    | PRI  | None       |
  | state_date                     | date                 | NO    | PRI  | None       |
  | state                          | enum('none','long','short') | NO    |      | none       |
```


**阿里云 示例数据 (前5行):**

```
| variety_id | state_date | state

| 1 | 2026-04-23 | none

| 1 | 2026-04-24 | none

| 2 | 2026-04-23 | none

| 2 | 2026-04-24 | none

| 3 | 2026-04-23 | none

```

---

### trading_signals

- **阿里云**: 7 行 | **腾讯云**: 47 行 | **差额**: -40

- 引擎: InnoDB | 创建时间: 2026-04-24 11:17:40


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | id                             | int                  | NO    | PRI  | None       |
  | signal_date                    | date                 | NO    | MUL  | None       |
  | variety_id                     | int                  | NO    |      | None       |
  | variety_name                   | varchar(20)          | YES   |      | None       |
  | signal_type                    | varchar(20)          | NO    |      | None       |
  | main_score                     | float                | YES   |      | None       |
  | extra_json                     | json                 | YES   |      | None       |
  | created_at                     | datetime             | YES   |      | CURRENT_TIMESTAMP |
```


**阿里云 示例数据 (前5行):**

```
| id | signal_date | variety_id | variety_name | signal_type | main_score | extra_json | created_at

| 145 | 2026-04-23 | 13 | 沪金 | A_OPEN_SHORT | 0.733333 | {"bg": {"bg1": 18.24, "bg2": 15.49, "bg3 | 2026-04-25 18:26:25

| 146 | 2026-04-23 | 42 | 沪银 | A_OPEN_SHORT | 0.933333 | {"bg": {"bg1": 21.0, "bg2": 24.97, "bg3" | 2026-04-25 18:26:31

| 147 | 2026-04-23 | 50 | 塑料 | A_OPEN_LONG | 0.966667 | {"bg": {"bg1": -16.63, "bg2": -20.5, "bg | 2026-04-25 18:26:33

| 152 | 2026-04-24 | 28 | PTA | A_OPEN_LONG | 0.466667 | {"bg": {"bg1": -11.01, "bg2": -7.85, "bg | 2026-04-25 20:40:19

| 153 | 2026-04-24 | 30 | 聚丙烯 | A_OPEN_LONG | 0.966667 | {"bg": {"bg1": -18.23, "bg2": -23.53, "b | 2026-04-25 20:40:20

```


**腾讯云 示例数据 (前5行):**

```
| id | signal_date | variety_id | variety_name | signal_type | signal_role | direction | cycle_id | related_open_signal_id | related_open_date | theory_state_before | theory_state_after | main_score | extra_json | created_at

| 172 | 2026-04-29 | 20 | 棕榈油 | A_CLOSE_LONG | close | LONG | 20-LONG-2026-04-22 | NULL | 2026-04-22 | long | none | NULL | {"m3": -10.75, "retail": 4.72, "window": | 2026-04-29 21:30:54

| 173 | 2026-04-29 | 24 | 白糖 | A_CLOSE_LONG | close | LONG | 24-LONG-2026-04-16 | NULL | 2026-04-16 | long | none | NULL | {"m3": -10.44, "retail": -7.22, "window" | 2026-04-29 21:30:54

| 174 | 2026-04-29 | 40 | 氧化铝 | A_OPEN_SHORT | open | SHORT | 40-SHORT-2026-04-29 | NULL | NULL | none | short | 0.5 | {"bg": {"bg1": 14.86, "bg2": 29.36, "bg3 | 2026-04-29 21:30:55

| 175 | 2026-05-06 | 2 | 螺纹钢 | A_CLOSE_SHORT | close | SHORT | 2-SHORT-2026-04-27 | NULL | 2026-04-27 | short | none | NULL | {"m3": 2.789999999999999, "retail": -13. | 2026-05-06 19:56:57

| 176 | 2026-05-06 | 42 | 沪银 | A_CLOSE_SHORT | close | SHORT | 42-SHORT-2026-04-23 | NULL | 2026-04-23 | short | none | NULL | {"m3": 3.8000000000000007, "retail": 5.2 | 2026-05-06 19:56:59

```

---

### update_items

- **阿里云**: 83 行 | **腾讯云**: 83 行 | **差额**: 相同

- 引擎: InnoDB | 创建时间: 2025-08-31 15:11:44


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | item_id                        | varchar(50)          | NO    | PRI  | None       |
  | run_id                         | varchar(50)          | NO    | MUL  | None       |
  | contract_symbol                | varchar(20)          | NO    | MUL  | None       |
  | target_table                   | varchar(50)          | NO    |      | None       |
  | started_at                     | timestamp            | YES   |      | None       |
  | finished_at                    | timestamp            | YES   |      | None       |
  | duration_ms                    | int                  | YES   |      | 0          |
  | status                         | enum('success','failure','running') | YES   | MUL  | running    |
  | error_stage                    | enum('fetch','store','timeout','unknown') | YES   |      | None       |
  | error_message                  | text                 | YES   |      | None       |
  | retry_of_item_id               | varchar(50)          | YES   |      | None       |
```


**阿里云 示例数据 (前5行):**

```
| item_id | run_id | contract_symbol | target_table | started_at | finished_at | duration_ms | status | error_stage | error_message | retry_of_item_id

| item_run_1756626311018_adm | run_1756626311018 | adm | hist_adm | 2025-08-31 15:45:14 | 2025-08-31 15:45:15 | 54 | failure | store | list index out of range | NULL

| item_run_1756626311018_agm | run_1756626311018 | agm | hist_agm | 2025-08-31 15:45:14 | 2025-08-31 15:45:14 | 54 | failure | store | list index out of range | NULL

| item_run_1756626311018_alm | run_1756626311018 | alm | hist_alm | 2025-08-31 15:45:14 | 2025-08-31 15:45:14 | 51 | failure | store | list index out of range | NULL

| item_run_1756626311018_am | run_1756626311018 | am | hist_am | 2025-08-31 15:45:15 | 2025-08-31 15:45:15 | 56 | failure | store | list index out of range | NULL

| item_run_1756626311018_aom | run_1756626311018 | aom | hist_aom | 2025-08-31 15:45:14 | 2025-08-31 15:45:15 | 58 | failure | store | list index out of range | NULL

```


**腾讯云 示例数据 (前5行):**

```
| item_id | run_id | contract_symbol | target_table | started_at | finished_at | duration_ms | status | error_stage | error_message | retry_of_item_id

| item_run_1756626311018_adm | run_1756626311018 | adm | hist_adm | 2025-08-31 15:45:14 | 2025-08-31 15:45:15 | 54 | failure | store | list index out of range | NULL

| item_run_1756626311018_agm | run_1756626311018 | agm | hist_agm | 2025-08-31 15:45:14 | 2025-08-31 15:45:14 | 54 | failure | store | list index out of range | NULL

| item_run_1756626311018_alm | run_1756626311018 | alm | hist_alm | 2025-08-31 15:45:14 | 2025-08-31 15:45:14 | 51 | failure | store | list index out of range | NULL

| item_run_1756626311018_am | run_1756626311018 | am | hist_am | 2025-08-31 15:45:15 | 2025-08-31 15:45:15 | 56 | failure | store | list index out of range | NULL

| item_run_1756626311018_aom | run_1756626311018 | aom | hist_aom | 2025-08-31 15:45:14 | 2025-08-31 15:45:15 | 58 | failure | store | list index out of range | NULL

```

---

### update_runs

- **阿里云**: 1 行 | **腾讯云**: 1 行 | **差额**: 相同

- 引擎: InnoDB | 创建时间: 2025-08-31 15:11:44


**表结构 (阿里云):**

```
| 字段名                         | 类型                | Null  | Key  | 默认值       |

  | run_id                         | varchar(50)          | NO    | PRI  | None       |
  | triggered_by                   | enum('manual','auto') | NO    | MUL  | None       |
  | scheduled_at                   | timestamp            | YES   |      | None       |
  | started_at                     | timestamp            | YES   | MUL  | None       |
  | finished_at                    | timestamp            | YES   |      | None       |
  | date_start                     | date                 | NO    |      | None       |
  | date_end                       | date                 | NO    |      | None       |
  | timeout_ms                     | int                  | YES   |      | 60000      |
  | concurrency                    | int                  | YES   |      | 5          |
  | is_multithread_on              | tinyint(1)           | YES   |      | 1          |
  | total_contracts                | int                  | YES   |      | 0          |
  | success_count                  | int                  | YES   |      | 0          |
  | fail_count                     | int                  | YES   |      | 0          |
  | status                         | enum('running','success','failure','partial') | YES   | MUL  | running    |
  | notes                          | text                 | YES   |      | None       |
```


**阿里云 示例数据 (前1行):**

```
| run_id | triggered_by | scheduled_at | started_at | finished_at | date_start | date_end | timeout_ms | concurrency | is_multithread_on | total_contracts | success_count | fail_count | status | notes

| run_1756626311018 | manual | NULL | 2025-08-31 15:45:11 | 2025-08-31 15:45:18 | 2025-08-01 | 2025-08-31 | 60000 | 5 | 1 | 83 | 0 | 83 | failure | NULL

```


**腾讯云 示例数据 (前1行):**

```
| run_id | triggered_by | scheduled_at | started_at | finished_at | date_start | date_end | timeout_ms | concurrency | is_multithread_on | total_contracts | success_count | fail_count | status | notes

| run_1756626311018 | manual | NULL | 2025-08-31 15:45:11 | 2025-08-31 15:45:18 | 2025-08-01 | 2025-08-31 | 60000 | 5 | 1 | 83 | 0 | 83 | failure | NULL

```
