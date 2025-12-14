#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bloomberg 新闻自动处理服务

功能说明：
1. 接收浏览器扩展发送的新闻数据（Flask API）
2. 实时存储到本地SQLite数据库 bloomberg_news 表
3. 定时处理新闻（每天5:30/11:30/17:30/23:30）
4. AI筛选期货相关新闻并格式化输出
5. 保存到MySQL数据库 news_red_telegraph 和 news_process_tracking 表
6. 保存到本地SQLite数据库 analysis_task 表
7. 标记已处理新闻（status=1），保留1个月后自动清理

工作流程：
插件发送 -> bloomberg_news表 -> 定时触发 -> AI筛选 -> MySQL保存 -> analysis_task表 -> 标记已处理 -> 清理1个月前数据
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import json
import os
import time
import sqlite3
import pymysql
import requests
import signal
import sys
from datetime import datetime, timedelta
from pathlib import Path
import logging

# ==================== 配置部分 ====================

# Flask应用配置
app = Flask(__name__)
CORS(app)

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('bloomberg_service.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 数据库路径配置（使用 spiderx/db 目录下的数据库）
DB_DIR = Path(__file__).parent.parent / "db"
DB_PATH = DB_DIR / "crawler.db"

# AI API 配置
AI_API_KEY = "sk-qVU4OZNspU5cSTPONFBFD000t2Oy8Tq9U8h74Wm5Phnl8tsB"
AI_BASE_URL = "https://poloai.top/v1/chat/completions"

# Bloomberg URL前缀
BLOOMBERG_URL_PREFIX = "https://www.bloomberg.com"

# 服务端口
SERVICE_PORT = 1123

# MySQL数据库配置
MYSQL_CONFIG = {
    'host': 'rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'ysd',
    'password': 'Yan1234567',
    'database': 'futures',
    'charset': 'utf8mb4'
}

# ==================== 数据库操作 ====================

def get_db_connection():
    """获取数据库连接"""
    if not DB_PATH.exists():
        logger.warning("⚠️ 数据库文件不存在，请先运行 init_db.py")
        # 尝试初始化数据库
        sys.path.insert(0, str(DB_DIR))
        from init_db import init_db
        init_db()
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 支持字典式访问
    return conn


def save_news_to_db(news_item):
    """
    保存新闻到 bloomberg_news 表（带去重）
    
    参数：
        news_item: 新闻数据字典，包含 publishedAt, headline, brand, url
    
    返回：
        bool: 是否成功插入（重复数据返回 False）
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 补全URL（使用 or 确保 None 值被处理为空字符串）
        url = news_item.get('url') or ''
        if url and not url.startswith('http'):
            url = BLOOMBERG_URL_PREFIX + url
        
        # 解析发布时间
        published_at = news_item.get('publishedAt') or ''
        
        # 使用 INSERT OR IGNORE 实现去重（基于 published_at 唯一索引）
        insert_sql = """
            INSERT OR IGNORE INTO bloomberg_news 
            (published_at, headline, brand, url, status)
            VALUES (?, ?, ?, ?, 0)
        """
        cursor.execute(insert_sql, (
            published_at,
            news_item.get('headline', ''),
            news_item.get('brand', ''),
            url
        ))
        
        conn.commit()
        return cursor.rowcount > 0
        
    except Exception as e:
        logger.error(f"保存新闻失败: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def get_pending_news(start_time, end_time):
    """
    获取指定时间范围内待处理的新闻（status=0）
    
    参数：
        start_time: 开始时间（datetime对象）
        end_time: 结束时间（datetime对象）
    
    返回：
        list: 新闻列表
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 根据 created_at 筛选时间范围内的未处理新闻
        select_sql = """
            SELECT id, published_at, headline, brand, url
            FROM bloomberg_news
            WHERE status = 0 
            AND created_at >= ? 
            AND created_at < ?
            ORDER BY created_at ASC
        """
        cursor.execute(select_sql, (
            start_time.strftime('%Y-%m-%d %H:%M:%S'),
            end_time.strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        rows = cursor.fetchall()
        return [dict(row) for row in rows]
        
    except Exception as e:
        logger.error(f"获取待处理新闻失败: {e}")
        return []
    finally:
        if conn:
            conn.close()


def mark_news_as_processed(news_ids):
    """
    将指定新闻标记为已处理（status=1）
    
    参数：
        news_ids: 新闻ID列表
    """
    if not news_ids:
        return
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        placeholders = ','.join(['?' for _ in news_ids])
        update_sql = f"""
            UPDATE bloomberg_news 
            SET status = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id IN ({placeholders})
        """
        cursor.execute(update_sql, news_ids)
        conn.commit()
        
    except Exception as e:
        logger.error(f"标记新闻状态失败: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def delete_old_processed_news():
    """
    删除1个月前的已处理新闻（status=1）
    保留最近1个月的数据，只清理超过1个月的旧数据
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 计算1个月前的时间点
        one_month_ago = datetime.now() - timedelta(days=30)
        one_month_ago_str = one_month_ago.strftime('%Y-%m-%d %H:%M:%S')
        
        # 删除1个月前的已处理新闻
        delete_sql = "DELETE FROM bloomberg_news WHERE status = 1 AND created_at < ?"
        cursor.execute(delete_sql, (one_month_ago_str,))
        deleted_count = cursor.rowcount
        conn.commit()
        
        if deleted_count > 0:
            logger.info(f"清理旧数据: {deleted_count}条")
        
    except Exception as e:
        logger.error(f"删除旧新闻失败: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def save_analysis_task(title, prompt, news_time):
    """
    保存分析任务到 analysis_task 表
    
    参数：
        title: 任务标题
        prompt: 提示词/分析内容
        news_time: 新闻时间（datetime对象）
    
    返回：
        int or None: 成功返回任务ID，失败返回None
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        insert_sql = """
            INSERT INTO analysis_task 
            (title, prompt, news_time, ai_result, is_analyzed)
            VALUES (?, ?, ?, '', 0)
        """
        cursor.execute(insert_sql, (
            title,
            prompt,
            news_time.strftime('%Y-%m-%d %H:%M:%S')
        ))
        
        task_id = cursor.lastrowid
        conn.commit()
        return task_id
        
    except Exception as e:
        logger.error(f"保存分析任务失败: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()


def get_pending_news_count():
    """获取待处理新闻数量"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM bloomberg_news WHERE status = 0")
        return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"获取待处理新闻数量失败: {e}")
        return 0
    finally:
        if conn:
            conn.close()


# ==================== MySQL数据库操作 ====================

def get_mysql_connection():
    """获取MySQL数据库连接"""
    return pymysql.connect(**MYSQL_CONFIG)


def save_to_mysql(title, content, news_timestamp):
    """
    保存AI筛选结果到MySQL数据库
    
    参数：
        title: 标题，如【彭博社2025年11月1日0点到6点新闻】
        content: AI筛选过滤后的内容
        news_timestamp: 新闻时间段开始时间的时间戳（秒）
    
    返回：
        int or None: 成功返回news_id，失败返回None
    """
    conn = None
    try:
        conn = get_mysql_connection()
        cursor = conn.cursor()
        
        # 1. 保存到 news_red_telegraph 表（使用 ON DUPLICATE KEY UPDATE 处理重复）
        insert_news_sql = """
            INSERT INTO news_red_telegraph 
            (ctime, title, content, ai_analysis, message_score, message_label, message_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                title = VALUES(title),
                content = VALUES(content),
                ai_analysis = VALUES(ai_analysis)
        """
        cursor.execute(insert_news_sql, (
            news_timestamp,          # ctime: 新闻发生时间的时间戳
            title,                   # title: 标题
            content,                 # content: AI筛选过滤后的内容
            '暂无分析',              # ai_analysis: 默认值
            6,                       # message_score: 默认值6
            'hard',                  # message_label: 默认值hard
            '彭博社新闻'             # message_type: 默认值
        ))
        
        news_id = cursor.lastrowid
        
        # 如果是更新操作，lastrowid 为 0，需要查询获取实际 ID
        if news_id == 0:
            cursor.execute("SELECT id FROM news_red_telegraph WHERE ctime = %s", (news_timestamp,))
            result = cursor.fetchone()
            if result:
                news_id = result[0]
            else:
                conn.commit()
                return None
        
        # 2. 保存到 news_process_tracking 表（使用 INSERT IGNORE 避免重复）
        insert_tracking_sql = """
            INSERT IGNORE INTO news_process_tracking 
            (news_id, ctime)
            VALUES (%s, %s)
        """
        cursor.execute(insert_tracking_sql, (
            news_id,                 # news_id: 关联news_red_telegraph表的id
            news_timestamp           # ctime: 消息创建时间
        ))
        
        conn.commit()
        return news_id
        
    except Exception as e:
        logger.error(f"MySQL保存失败: {e}")
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()


# ==================== AI接口调用 ====================

def call_ai_api(news_list, max_retries=2):
    """
    调用AI接口筛选新闻（带重试机制）
    
    参数：
        news_list: 新闻列表，每条包含 headline, brand, url
        max_retries: 最大重试次数（默认2次）
    
    返回：
        str or None: AI返回的筛选结果，失败返回None
    """
    # 构建提示词
    news_json = json.dumps(news_list, ensure_ascii=False, indent=2)
    
    system_message = """
你是一个专业的期货市场新闻筛选与翻译助手，服务于量化交易系统。

【核心目标】
从给定新闻中，只保留那些对"可交易期货资产"价格在短期内可能产生显著影响的新闻，并翻译成中文标题。
若影响不确定或极弱，应宁可不选。

【严格筛选范围（必须直接关联期货交易驱动）】

一、应保留（满足任意一条即可）：
1. 宏观政策与风险事件：
   - 央行决议、利率变化、意外政策信号
   - 外汇监管、干预政策或汇率创历史极值
   - 重大制裁、战争、禁运、关税、贸易政策变动

2. 影响大宗商品供需的事件：
   - 石油/天然气/OPEC决议、大型油田或矿山停产/增产/事故
   - 农产品天气异常、灾害、病虫害、出口/进口封锁或采购取消
   - 金属或能源库存显著变化、限产、补库、储备释放

3. 超预期的关键宏观数据：
   - CPI、PPI、GDP、PMI、就业、库存、贸易数据等
   - 且新闻明确表述"超预期/不及预期/市场震动/价格反应"

4. 评级机构或国家风险事件：
   - 主权或大型机构评级调整、违约、流动性危机

5. 金融市场情绪驱动事件：
   - 影响风险偏好或波动率的突发事件（如系统性金融风险、重大违约、金融机构危机）

二、应剔除（除非文本说明已引发显著价格波动）：
1. 公司经营活动：并购、扩产、合作、新项目等普通新闻
2. 管理人动态：基金发售、PE、对冲基金变动
3. ESG、品牌、公关、社会责任报道
4. 高管变更或企业治理新闻
5. 区域项目、城市发展、一般制造业投资
6. 行业观点、预测、研究报告、展望类描述

三、审查逻辑：
- 站在"可交易期货市场（商品、股指、外汇、利率等）交易者"角度评估冲击性。
- 若没有明显影响或新闻内容偏泛化，直接忽略。
- 若不确定冲击是否显著，应宁可不选。
- 若所有新闻均无有效冲击，应输出：无重要相关新闻

【输出格式要求】
1. 对保留的新闻标题翻译成简洁自然的中文，并标明相关期货品种。
2. 格式严格为（每条新闻一行）：
【XX期货相关】【翻译后的中文标题】新闻URL
3. XX为具体期货品种，如：原油、黄金、铜、大豆、玉米、股指、外汇等。
4. 不保留任何解释、评语或额外内容。
5. 无符合内容时输出：无重要相关新闻
"""

    user_message = f"""请从以下新闻中筛选出对期货市场价格在短期内可能产生明显影响的内容，并按要求格式输出：

{news_json}"""

    # 重试配置
    timeouts = [60, 120]  # 第一次60秒，第二次120秒
    
    for attempt in range(max_retries):
        try:
            timeout = timeouts[attempt] if attempt < len(timeouts) else timeouts[-1]
            
            payload = {
                "model": "gpt-4.1-mini",
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.7,
                "max_tokens": 5000
            }
            
            headers = {
                "Accept": "application/json",
                "Authorization": f"Bearer {AI_API_KEY}",
                "Content-Type": "application/json"
            }
            
            response = requests.post(AI_BASE_URL, json=payload, headers=headers, timeout=timeout)
            response.raise_for_status()
            
            result = response.json()["choices"][0]["message"]["content"]
            return result
            
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"AI筛选失败: {e}")
                return None
            time.sleep(2)  # 重试前等待2秒
    
    return None


# ==================== 定时任务 ====================

def build_analysis_prompt(ai_result):
    """
    构建分析任务的提示词
    
    参数：
        ai_result: AI筛选后的新闻内容
    
    返回：
        str: 完整的分析提示词
    """
    analysis_instruction = """
## 角色定位

你是一名专注于**中国期货市场**的资深「3–10 日短期单边趋势筛选师」，服务对象是国内期货交易者。

你的核心任务是**筛选**：  
- 只挑出「**大概率走出 3–10 日单边行情**」的机会；  
- 绝大部分新闻都应被识别为噪音或震荡背景，简短说明后忽略；  
- **宁可漏掉机会，也不要把震荡当趋势**。

你的分析遵循三条铁律：

1. **盘面行为优先**：价格 / 成交量 / 持仓结构 > 新闻故事。  
2. **量化信息优先于形容词**：尽可能使用概率、数字、区间，而不是“可能、大概率、或许”这类模糊词。  
3. **市场已有的量化数据 → 你的推理 → 量化结论**，禁止凭主观想象构造虚假精确度。

---

## 总体决策原则

- 新闻只提供「要验证的假设」，不是结论来源。  
- 真正决定多空和评分的，是通过搜索获取的「**市场已经给出的量化信息**」：
  - 概率（不同情景的隐含概率）  
  - 数量（库存、产量、进出口、减产规模等）  
  - 预测值（机构目标价、需求增速、成本线等）  
- 如果量化数据与新闻叙事矛盾：  
  - 一律以**可验证的量化数据**为准；  
  - 将新闻中夸张或情绪化的部分降级为「噪音 / 少数观点」。

---

## 输入说明

- 输入为对彭博社新闻的初步筛选结果，仅包含**新闻标题和链接 URL**。  
- 无正文，需要你主动做两类搜索：  
  1. 新闻详情（标题 + 正文 + 上下文）  
  2. 相关品种的市场与盘面量化信息。

---

## 信息获取与权重规则（新闻 ≤ 30%，量化 ≥ 70%）

整体原则：

> **新闻提供“故事假设”，市场量化数据提供“硬事实”，你的结论必须建立在“硬事实”之上。**

### 第一步：获取新闻详情（权重不超过 30%）

你**必须**通过搜索 / 浏览器访问每条新闻的链接 URL，获取尽可能完整的新闻内容（标题、正文、上下文）：

- 基于**新闻原文内容**得出的判断，权重**最多**占 30%。  
- 若链接无法访问或被墙 / 付费墙：  
  - 只能依靠标题及其他可查摘要进行判断；  
  - 必须明确说明：「链接无法完全访问，本次判断基于标题及可获得摘要，权重有限」。

在解读新闻时重点关注：  
- 事件是否指向**明确方向**（利多 / 利空）；  
- 事件的**持续性**（一次性冲击 vs 可持续 3–10 日）；  
- 是否涉及**实物供需**（产量、库存、进出口、限产 / 检修、天气、政策等）；  
- 是否属于「**市场早已广泛讨论的旧故事**」。

重要约束：

- 禁止仅根据新闻描述就下结论。  
- 新闻中的任何数字 / 比例 / 概率，仅作为「待验证线索」，必须通过额外搜索校验。

---

### 第二步（核心）：必须执行的「量化数据获取」步骤（权重 ≥ 40%）

对每一条新闻，你必须先完成以下「量化数据搜集」，这是核心步骤：

1. **概率类量化信息（宏观 / 政策 / 事件）**

   当新闻涉及央行决议、降息 / 加息、减产会议、重大政策落地时，必须查找：  
   - 类似 CME FedWatch、利率期货、OIS 曲线 等工具给出的：  
     - 不同情景（如不变 / 25bp / 50bp 等）的**隐含概率区间**；  
   - 明确标注：  
     - 哪个是**基准情景（Base case）**（通常概率 ≥ 60%）；  
     - 哪些是**尾部情景（Tail risk）**（通常概率 < 20%）。

2. **数量类量化信息（供需 / 基本面）**

   如新闻提到减产、限产、增产、库存变化、需求变化等，必须尝试找到：  
   - 具体变动量：  
     - 如「库存周降 2 万吨」「库存同比 -10%」「产量同比 -5%」；  
     - 「开工率从 80% 降至 70%」等；  
   - 若只能找到范围：  
     - 用「约 / 区间」表述，如「约 2–3 万吨」「约 5–8%」；  
   - 标明这些数字来自：官方数据 / 行业机构 / 大型券商 / 交易所等。

3. **预测类量化信息（机构预期）**

   搜索大型机构和主流研究所的**显性数字**：  
   - 价格目标：如「预计白银目标价 10 美元」「目标区间 9–10 美元」；  
   - 需求增速：如「预计需求增长 10%」；  
   - 成本线 / 盈亏平衡点：如「完全成本约在 7 美元附近」；  
   - 宏观路径：如「预计未来一年累计降息 75bp」等。

   如果新闻中某个“大佬”发表观点（如“需求大增”“看多到 XX”）：  
   - 必须检验市场是否已有对应定价：  
     - 若期货曲线、基差、价差结构没有明显跟随变化，则此观点视为**少数观点或噪音**，不能当作“市场预期”。

4. **严禁自创数字**

   - 禁止为了“显得专业”而虚构任何概率、幅度或目标价；  
   - 若确实查不到可靠数字，必须明确写出：  
     - 「未找到可靠的具体数字，本段仅作定性判断，不参与量化评分」。

---

### 第三步：补充搜索市场与盘面信息（权重 ≥ 30%）

在量化数据获取基础上，你还必须进行拓展搜索，获取与新闻相关品种的最新市场与盘面信息：

1. **宏观与机构观点**

   - 高盛、摩根士丹利、摩根大通、花旗、美银等最新观点；  
   - 国内重要机构 / 研究所的最新研报要点（如中信、国泰君安等）；  
   - 对于宏观预期类新闻，需对比：  
     - 「机构基准情景」 vs 「市场隐含路径」，  
     - 避免只听故事不看定价。

2. **供需与基本面数据**

   - 最新**库存、产量、开工率、进出口、检修 / 限产 / 复产**情况；  
   - 主产区 / 主消费区供需动态（天气、政策管制、需求恢复 / 萎缩等）。

3. **资金与持仓结构**

   - 相关主力合约的**持仓量变化**（增仓 / 减仓）；  
   - 多空力量是否出现明显「**方向性增仓**」而非简单对冲 / 挤空。

4. **技术面与价格行为（行为优先）**

   - 价格相对近期区间的位置：箱体突破 / 中枢震荡 / 历史高低附近；  
   - 是否临近关键**支撑 / 阻力位**；  
   - 最近 10–20 日**趋势方向**（上升 / 下降 / 震荡）；  
   - 成交量 + 持仓量组合：  
     - 上涨 + 放量 + **增仓** ⇒ 倾向趋势资金进入；  
     - 上涨 + 放量 + **减仓** ⇒ 警惕挤空 / 被动平仓尾声；  
   - 单日波动与 ATR 对比：  
     - 1–2 倍 ATR ⇒ 较健康的趋势或启动段；  
     - > 3 倍 ATR 且接近一年极值 ⇒ 优先视为情绪加速或可能尾声。

> 若你不执行以上「量化 + 盘面」步骤，就等于只用了一半信息做判断，这是**不被允许的**。

---

## 宏观利率 / 政策预期处理规则（防止情绪带偏）

当新闻与美联储 / 央行决议、降息 / 加息预期、点阵图、前瞻指引等强相关时，必须执行这套额外规则：

1. **必查客观定价**

   - 利率期货 / FedWatch / OIS / 国债收益率曲线等；  
   - 给出不同情景的**大致概率**（如：不变 / 25bp / 50bp 等）。

2. **禁止行为**

   - 禁止将「单一个人/顾问/政客的发言」直接描述为「市场普遍预期」。  
   - 如新闻中出现 “jumbo cut”“激进降息”，必须用利率定价验证：  
     - 若 ≥ 60% 的隐含概率仍集中在常规路径（如 25bp），则：  
       - 激进路径只能被定义为「少数情景 / 尾部风险」，  
       - 不得写成「市场主流预期」或「预期严重错位」。

3. **“预期错位”的定量定义（必须满足其一）**

   只有满足以下任何一条，才允许使用「预期错位」这一表述：

   - 利率期货 / FedWatch 隐含路径，与主流机构基准情景存在**显著差距**：  
     - 例如：  
       - 市场定价未来一年降息总幅度 ≥ 100bp，  
       - 而机构基准情景仅 25–50bp，且尚未收敛；  
   - 又或者，决议 / 数据公布后，点阵图 / 声明明显偏离会前定价，  
     - 导致利率资产出现**20–30bp 以上的快速重定价**。

4. **宏观驱动对评分的约束**

   - 若宏观预期只是与市场定价「基本一致」（如高概率 25bp 常规降息），  
     - 不得因为叙事夸张而给出 9–10 分；  
   - 只有在出现**清晰可量化的预期错位 + 盘面行为共振**时，  
     - 宏观因素才可作为「重大单边驱动」计入 9–10 分条件。

---

## 信息综合原则

- 权重平衡：  
  - 新闻内容（≤ 30%）；  
  - 市场量化数据 + 盘面行为（≥ 70%）。  

- 当新闻结论与盘面行为冲突时：  
  - 以盘面行为为主，降低评分或直接观望；  
  - 明确指出矛盾点，例如：  
    - 「新闻偏利多，但盘面放量减仓，疑似情绪尾声」；  
    - 「新闻强调激进降息，但利率定价仍以 25bp 为高概率基准」。

- 在分析中需明确区分：  
  - 「新闻原文显示：……」  
  - 「补充搜索发现：……」  
  - 「市场量化定价（如概率 / 库存 / 机构预测）显示：……」。

---

## 核心筛选标准（先判定是否具备 3–10 日单边趋势潜力）

在给出详细分析前，**先判定是否具备 3–10 日单边趋势潜力**。  
只有当下列 5 条中至少满足 **3 条**，且**盘面行为与新闻方向一致**时，才输出详细交易方案：

1. **驱动因素的持续性**

   - 事件影响具备至少 3–10 日的持续性，而非一天就被完全消化；  
   - 如：减产 / 限产、天气影响产量、政策调整、库存 / 基差结构变化等。

2. **供需关系的实质变化**

   - 库存、产量、进出口、开工率等出现明确缺口或过剩；  
   - 不仅是“预期喊话”，而是有数据或可靠路径指向供需阶段性改变。

3. **市场预期的错位**（按前述量化定义执行）

   - 新闻 / 数据揭示的信息，与当前价格反映的预期存在明显差异；  
   - 且这种差异可通过**概率 / 价差 / 曲线形态**验证。

4. **技术面与资金行为配合（行为优先）**

   至少满足其中两项：

   - 价格处于**突破 / 趋势启动阶段**（如突破近 20 日高点），而非远离均线的极端高位；  
   - 上涨 / 下跌伴随**明显放量 + 同方向增仓**（而非挤空 / 挤多减仓）；  
   - 单日波动在**1–2 倍 ATR**范围内，避免已经是极端拉升 / 暴跌的尾声。

   若出现：

   - 单日波动 > 3 倍 ATR 且价格接近过去一年极值，  
     - 默认优先视为「情绪加速 / 可能进入尾声」，  
     - 对评分有**上限约束**（见下文）。

5. **风险收益比合理**

   - 能基于技术位或波动率给出明确止损（如前一日低点、关键支撑 / 阻力、1–1.5 倍 ATR）；  
   - 合理测算目标价空间，潜在盈亏比至少 **1:2**。

**若不满足上述条件**：

- 简短说明「建议观望」的原因（如「影响短暂」「预期已充分反应」「盘面行为不配合」「技术面仍在震荡区间」等）；  
- 评分 ≤ 6 分；  
- 不给出具体入场点、止损、目标价。

---

## 风险场景量化与重新归类（非常关键）

对于分析中列出的每一个「风险因素」，必须执行以下动作：

1. 若风险描述依赖于某个**可量化事件**（例如：「若仅降息 25bp 将引发回调」）：  
   - 必须查找市场对该事件的**当前定价 / 概率**（如 FedWatch / 期货隐含概率）；  

2. 根据概率对风险进行归类：

   - 若某情景的隐含概率 **≥ 60%**：  
     - 视为**基准情景（Base case）**，  
     - 不得仅放在「风险」一栏轻描淡写；  
     - 必须进入核心推理，并对交易评分产生显著影响（通常**压低评分 + 不鼓励追高**）。  

   - 若某情景概率明显较低（例如 < 20%）：  
     - 方可视为**尾部风险（Tail risk）**，仅在风险段提示即可。

3. 对交易评分的影响：

   - 如当前多头逻辑**必须依赖低概率情景成立**才能站得住脚，  
     - 则评分**不得超过 7 分**，即使盘面暂时很强；  

   - 若基准情景本身对当前价格不利（例如：  
     - 大概率 25bp 常规降息，而价格在炒作 Jumbo cut），  
     - 必须明确写出：  
       - 「当前价格更多在交易低概率情景，一旦回到基准情景，存在明显回调风险」，  
       - 并以此为理由**压低评分，避免出现 9/10 式的“错觉安全感”**。

---

## 交易评分体系（加入极端波动约束）

| 分数 | 含义 | 输出要求 |
|------|------|----------|
| 1–3  | 影响微弱、方向不明或已充分反应 | 一句话说明原因，建议观望 |
| 4–6  | 有一定逻辑但缺乏单边趋势潜力或行为不配合 | 简述原因，建议观望或等待确认 |
| 7–8  | **满足单边趋势条件**，叙事与盘面高度一致 | 给出完整交易方案（入场、止损、目标） |
| 9–10 | **重大单边驱动事件**，方向确定性极高，行为强烈配合，且存在可量化预期错位 | 给出完整交易方案，可适度加仓 |

**评分铁律：**

1. 评分 < 7 分：  
   - 不得给出具体入场点、止损、目标价；  
   - 只需简短说明观望理由。

2. 评分 ≥ 7 分：  
   - 必须满足上面 5 条标准中的至少 3 条；  
   - 且「新闻方向」与「盘面行为」一致。

3. 9–10 分的额外硬条件：  
   - 同时具备：  
     - **驱动极强且具 3–10 日以上持续性**；  
     - **盘面放量增仓 + 价格处于趋势启动或突破阶段，而非极端尾声**；  
     - **存在可量化的预期错位**（利率路径 / 库存 / 基差结构等显著错价）。  

   - 当价格已处于**历史极值附近**且单日波动 > 3 倍 ATR 时：  
     - 最多只能给到 **7–8 分**；  
     - 必须明确提示「情绪加速段，防范尾声反转风险」。

4. 对于仅有情绪放大、缺乏量化支撑的故事（如单一政客喊话、未反映在定价工具中的激进情景），  
   - 默认**降级为噪音 / 边缘情景**，不得据此给出 9–10 分。

---

## 量化结论输出要求（必须有一个「量化小结」）

在每个品种的分析中，必须单独给出「量化小结」，包括：

- **基准情景（概率最高）**：  
  - 简述情景内容 + 概率区间（如「降息 25bp，概率约 70–80%，来源：XX」）；  
  - 在该情景下，品种价格大致可能的**波动区间 / 涨跌幅区间**（允许用区间，如「回调 5–10%」或「上行 3–6%」）。

- **有利情景（对当前方向有利）**：  
  - 触发条件；  
  - 大致概率；  
  - 大致空间（如「进一步上冲 5–8%」）。

- **不利情景（对当前方向不利）**：  
  - 触发条件；  
  - 大致概率；  
  - 可能回撤空间（如「回调 8–12%」）。

若某一情景完全缺乏可靠量化依据，必须说明：  
> 「此情景缺乏可验证的量化数据，仅作方向性参考，不参与数值测算。」

---

## 统一分析输出格式

### 一、当评分 ≥ 7 分（满足单边趋势条件）时

【品种名称】XX期货（交易所代码）

▶ 信息来源：新闻原文 + 补充搜索  
▶ 单边趋势判定：✅ 满足（说明满足哪几条标准，如「驱动持续性、供需实质变化、技术面配合」）  
▶ 影响判断：利多 / 利空  
▶ 影响周期：预计 3–10 日单边行情（给出大致区间）

▶ 核心驱动：  
一句话：什么事件 / 故事 → 通过什么途径影响供需或情绪 / 资金 → 价格预期向哪个方向单边演变。必要时说明「宏观定价与新闻叙事的一致 / 不一致」。

▶ 量化小结：  
- 基准情景：……（简述 + 概率范围 + 预期涨跌幅区间）  
- 有利情景：……  
- 不利情景：……

▶ 交易策略：  
• 方向：做多 / 做空  
• 入场思路：突破跟随 / 回调介入（如「回调至 XX–XX 区间分批建仓，不追高」）  
• 持仓周期：X–X 日（如 3–7 日）  
• 止损参考：明确价位或区间（如「跌破前一日低点 XX」或「亏损约 2–3%」）  
• 目标预期：目标价或大致涨跌幅（如「上看 XX–XX」或「预期空间约 4–6%」）

▶ 风险因素：  
列出 1–2 个主要反向风险（如「故事被证伪」「政策突然反向」「盘面资金迅速撤出」），必要时注明对应概率级别。

▶ 交易评分：X/10（7–10 分）  
一句话说明评分原因（如「驱动明确且持续、盘面放量增仓突破、预期仍未完全反映」或「处于情绪加速段但尾端风险较大，仅给 7–8 分」）。

---

### 二、当评分 < 7 分（不满足单边趋势条件）时

【品种名称】XX期货（交易所代码）

▶ 信息来源：新闻原文 + 补充搜索  
▶ 单边趋势判定：❌ 不满足  
▶ 建议：观望  

▶ 原因：  
一句话简述（如：「影响短暂、偏情绪冲击」「供需无实质改变，属于故事层面」  
「盘面放量减仓，疑似挤空尾声」「技术面仍在震荡区间，方向不明」等）。

▶ 交易评分：X/10（1–6 分）

---

## 输出规则（严格执行）

1. **筛选优先**  
   - 先判定是否具备 3–10 日单边趋势潜力；  
   - 不满足的统一按「观望」处理，按观望模板输出。

2. **精简原则**  
   - 满足单边趋势条件的品种：  
     - 模块控制在约 10–15 行以内，重点写「量化驱动 + 策略 + 风险」。  
   - 观望品种：  
     - 模块控制在约 5–7 行以内。

3. **合并原则**  
   - 多条新闻指向同一品种时，必须合并分析，只输出**一个**综合结论模块；  
   - 可以简短说明「多条新闻共同指向……」。

4. **过滤原则（直接跳过、不做分析）**  
   若出现以下任一情况，可直接忽略该新闻，不输出模块：

   - 影响与实际可交易品种关联极弱；  
   - 明显属于市场长期共识，价格已充分反映；  
   - 无法形成明确交易方向（多空利弊极度均衡）；  
   - 国内无对应可交易品种；  
   - 或盘面已出现极端走势迹象，例如：  
     - 单日波动 > 3 倍 ATR 且位于过去一年极值附近，并伴随放量减仓（疑似末端爆仓 / 挤空 / 挤多）。  

   对于上述情况，只需在总输出中概括一句「本条新闻仅属情绪或末端波动，不建议基于此开仓」。

5. **排序原则**  
   - 先列出评分 ≥ 7 分的品种模块，按分数从高到低排序；  
   - 再列出评分 < 7 分的观望品种模块。

6. **兜底原则**  
   - 若本批次所有新闻均不具备单边趋势潜力，则统一输出一句：  
     > 本批次新闻暂无明确 3–10 日单边趋势机会，整体建议观望。

---

## 中国期货市场品种参考（可交易标的）

**上期所（SHFE）**：  
铜(CU)、铝(AL)、锌(ZN)、铅(PB)、镍(NI)、锡(SN)、黄金(AU)、白银(AG)、螺纹钢(RB)、热卷(HC)、天然橡胶(RU)、燃料油(FU)、沥青(BU)

**上期能源（INE）**：  
原油(SC)、低硫燃料油(LU)、欧线(EC)

**大商所（DCE）**：  
豆粕(M)、豆油(Y)、棕榈油(P)、豆一(A)、豆二(B)、玉米(C)、玉米淀粉(CS)、鸡蛋(JD)、生猪(LH)、铁矿石(I)、焦煤(JM)、焦炭(J)、塑料(L)、PVC(V)、PP(PP)、乙二醇(EG)、苯乙烯(EB)、LPG(PG)

**郑商所（CZCE）**：  
白糖(SR)、棉花(CF)、棉纱(CY)、苹果(AP)、红枣(CJ)、PTA(TA)、甲醇(MA)、菜油(OI)、菜粕(RM)、玻璃(FG)、纯碱(SA)、尿素(UR)、硅铁(SF)、锰硅(SM)

**广期所（GFEX）**：  
工业硅(SI)、碳酸锂(LC)、多晶硅(PS)
"""
    
    return f"{ai_result}\n\n{analysis_instruction}"


def process_news_task():
    """
    定时任务：处理新闻
    在 5:30/11:30/17:30/23:30 执行
    """
    now = datetime.now()
    current_hour = now.hour
    current_minute = now.minute
    
    # 确定时间段标签（用于标题显示）
    if current_hour == 5 and current_minute == 30:
        time_label = "上午"
    elif current_hour == 11 and current_minute == 30:
        time_label = "下午"
    elif current_hour == 17 and current_minute == 30:
        time_label = "晚上"
    elif current_hour == 23 and current_minute == 30:
        time_label = "凌晨"
    else:
        # 兼容手动触发的情况，根据当前时间判断
        if 5 <= current_hour < 11 or (current_hour == 5 and current_minute >= 30) or (current_hour == 11 and current_minute < 30):
            time_label = "上午"
        elif 11 <= current_hour < 17 or (current_hour == 11 and current_minute >= 30) or (current_hour == 17 and current_minute < 30):
            time_label = "下午"
        elif 17 <= current_hour < 23 or (current_hour == 17 and current_minute >= 30) or (current_hour == 23 and current_minute < 30):
            time_label = "晚上"
        else:
            time_label = "凌晨"
    
    # 计算时间范围：获取过去24小时内未处理的新闻
    end_time = now
    start_time = now - timedelta(hours=24)
    
    # 从数据库获取待处理新闻
    target_news = get_pending_news(start_time, end_time)
    
    if len(target_news) == 0:
        logger.info(f"[{time_label}] 无待处理新闻")
        return
    
    # 获取新闻ID列表，用于后续标记
    news_ids = [item['id'] for item in target_news]
    
    # 准备发送给AI的新闻列表
    news_for_ai = [
        {
            'publishedAt': item.get('published_at'),
            'headline': item.get('headline'),
            'brand': item.get('brand', ''),
            'url': item.get('url', '')
        }
        for item in target_news
    ]
    
    # 调用AI接口筛选
    ai_result = call_ai_api(news_for_ai)
    
    if ai_result is None:
        logger.error(f"[{time_label}] 处理失败: AI筛选失败, 待处理{len(target_news)}条")
        return
    
    # 构建标题
    date_str = now.strftime('%Y年%m月%d日')
    mysql_title = f"彭博社{date_str}{time_label}新闻"
    analysis_title = f"彭博社{date_str}{time_label}分析"
    
    # AI筛选结果
    ai_result_stripped = ai_result.strip()
    
    # 使用当前执行时间的时间戳（秒），确保每次执行都是唯一的
    news_timestamp = int(now.timestamp())
    
    # 保存到MySQL
    mysql_news_id = save_to_mysql(mysql_title, ai_result_stripped, news_timestamp)
    
    # 检查是否无重要新闻
    if "无重要相关新闻" in ai_result_stripped:
        mark_news_as_processed(news_ids)
        delete_old_processed_news()
        logger.info(f"[{time_label}] 完成: {len(news_ids)}条->无重要新闻, MySQL:{mysql_news_id or '失败'}")
        return
    
    # 构建完整的分析提示词
    prompt = build_analysis_prompt(ai_result_stripped)
    
    # 保存到 analysis_task 表
    task_id = save_analysis_task(analysis_title, prompt, start_time)
    
    if task_id:
        mark_news_as_processed(news_ids)
        delete_old_processed_news()
        logger.info(f"[{time_label}] 完成: {len(news_ids)}条->任务{task_id}, MySQL:{mysql_news_id or '失败'}")
    else:
        logger.error(f"[{time_label}] 失败: 分析任务保存失败, 待处理{len(news_ids)}条")


# ==================== Flask路由 ====================

@app.route('/api/capture', methods=['POST', 'OPTIONS'])
def capture_data():
    """接收浏览器扩展发送的新闻数据"""
    
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'message': '没有接收到数据'
            }), 400
        
        # 获取新闻列表
        captured_data = data.get('capturedData', [])
        
        if not captured_data:
            return jsonify({
                'success': False,
                'message': '数据列表为空'
            }), 400
        
        # 添加新闻到数据库
        added_count = 0
        for item in captured_data:
            brand = (item.get('brand') or '').lower().strip()
            news_item = {
                'publishedAt': item.get('publishedAt'),
                'headline': item.get('headline'),
                'brand': brand,
                'url': item.get('url') or ''
            }
            
            if save_news_to_db(news_item):
                added_count += 1
        
        # 获取当前待处理总数
        total_count = get_pending_news_count()
        
        if added_count > 0:
            logger.info(f'接收: +{added_count}, 总计: {total_count}')
        
        return jsonify({
            'success': True,
            'message': '数据保存成功',
            'added': added_count,
            'total': total_count
        }), 200
        
    except Exception as e:
        logger.error(f'接收失败: {e}')
        return jsonify({
            'success': False,
            'message': f'保存失败: {str(e)}'
        }), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查接口"""
    pending_count = get_pending_news_count()
    return jsonify({
        'status': 'ok',
        'service': 'Bloomberg新闻处理服务',
        'port': SERVICE_PORT,
        'time': datetime.now().isoformat(),
        'pending_news': pending_count,
        'database': str(DB_PATH)
    })


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 待处理新闻数量
        cursor.execute("SELECT COUNT(*) FROM bloomberg_news WHERE status = 0")
        pending = cursor.fetchone()[0]
        
        # 已处理新闻数量
        cursor.execute("SELECT COUNT(*) FROM bloomberg_news WHERE status = 1")
        processed = cursor.fetchone()[0]
        
        # 分析任务数量
        cursor.execute("SELECT COUNT(*) FROM analysis_task")
        tasks = cursor.fetchone()[0]
        
        # 待分析任务数量
        cursor.execute("SELECT COUNT(*) FROM analysis_task WHERE is_analyzed = 0")
        pending_tasks = cursor.fetchone()[0]
        
        return jsonify({
            'bloomberg_news': {
                'pending': pending,
                'processed': processed,
                'total': pending + processed
            },
            'analysis_task': {
                'total': tasks,
                'pending': pending_tasks,
                'analyzed': tasks - pending_tasks
            },
            'database': str(DB_PATH)
        })
    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/process_now', methods=['POST'])
def process_now():
    """手动触发处理任务（用于测试）"""
    try:
        process_news_task()
        return jsonify({
            'success': True,
            'message': '处理任务已执行'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


def process_all_pending_news_for_test():
    """
    测试用：处理所有待处理的新闻（不受时间限制）
    """
    now = datetime.now()
    
    # 获取所有待处理的新闻（不限时间范围）
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        select_sql = """
            SELECT id, published_at, headline, brand, url
            FROM bloomberg_news
            WHERE status = 0
            ORDER BY created_at ASC
        """
        cursor.execute(select_sql)
        rows = cursor.fetchall()
        target_news = [dict(row) for row in rows]
        
    except Exception as e:
        logger.error(f"[测试] 获取新闻失败: {e}")
        return {'success': False, 'message': f'获取新闻失败: {str(e)}', 'processed': 0}
    finally:
        if conn:
            conn.close()
    
    if len(target_news) == 0:
        return {'success': True, 'message': '没有需要处理的新闻', 'processed': 0}
    
    # 获取新闻ID列表
    news_ids = [item['id'] for item in target_news]
    
    # 准备发送给AI的新闻列表
    news_for_ai = [
        {
            'publishedAt': item.get('published_at'),
            'headline': item.get('headline'),
            'brand': item.get('brand', ''),
            'url': item.get('url', '')
        }
        for item in target_news
    ]
    
    # 调用AI接口筛选
    ai_result = call_ai_api(news_for_ai)
    
    if ai_result is None:
        logger.error(f"[测试] 失败: AI筛选失败, 待处理{len(target_news)}条")
        return {'success': False, 'message': 'AI筛选失败', 'processed': 0}
    
    # 构建标题（测试模式）
    date_str = now.strftime('%Y年%m月%d日')
    
    # 根据当前时间确定时间段标签
    current_hour = now.hour
    current_minute = now.minute
    if 5 <= current_hour < 11 or (current_hour == 5 and current_minute >= 30) or (current_hour == 11 and current_minute < 30):
        time_label = "上午"
    elif 11 <= current_hour < 17 or (current_hour == 11 and current_minute >= 30) or (current_hour == 17 and current_minute < 30):
        time_label = "下午"
    elif 17 <= current_hour < 23 or (current_hour == 17 and current_minute >= 30) or (current_hour == 23 and current_minute < 30):
        time_label = "晚上"
    else:
        time_label = "凌晨"
    
    mysql_title = f"【彭博社{date_str}{time_label}新闻-测试】"
    analysis_title = f"【彭博社{date_str}{time_label}分析-测试】"
    
    # AI筛选结果
    ai_result_stripped = ai_result.strip()
    
    # 计算新闻时间戳（测试模式使用当前时间）
    news_timestamp = int(now.timestamp())
    
    # 保存到MySQL
    mysql_news_id = save_to_mysql(mysql_title, ai_result_stripped, news_timestamp)
    
    # 检查是否无重要新闻
    if "无重要相关新闻" in ai_result_stripped:
        mark_news_as_processed(news_ids)
        delete_old_processed_news()
        logger.info(f"[测试] 完成: {len(news_ids)}条->无重要新闻, MySQL:{mysql_news_id or '失败'}")
        return {
            'success': True, 
            'message': '无重要相关新闻，已清理原始数据', 
            'processed': len(news_ids),
            'task_id': None,
            'mysql_news_id': mysql_news_id
        }
    
    # 构建完整的分析提示词
    prompt = build_analysis_prompt(ai_result_stripped)
    
    # 保存到 analysis_task 表
    task_id = save_analysis_task(analysis_title, prompt, now)
    
    if task_id:
        mark_news_as_processed(news_ids)
        delete_old_processed_news()
        logger.info(f"[测试] 完成: {len(news_ids)}条->任务{task_id}, MySQL:{mysql_news_id or '失败'}")
        return {
            'success': True, 
            'message': f'处理完成，已创建分析任务 ID: {task_id}', 
            'processed': len(news_ids),
            'task_id': task_id,
            'mysql_news_id': mysql_news_id
        }
    else:
        logger.error(f"[测试] 失败: 分析任务保存失败, 待处理{len(news_ids)}条")
        return {'success': False, 'message': '分析任务保存失败', 'processed': 0}


@app.route('/api/process_test', methods=['POST'])
def process_test():
    """
    测试接口：立即处理所有待处理新闻（不受时间限制）
    用于测试，无需等待定时任务的具体时间
    """
    try:
        result = process_all_pending_news_for_test()
        return jsonify(result), 200 if result['success'] else 500
    except Exception as e:
        logger.error(f"[测试] 异常: {e}")
        return jsonify({
            'success': False,
            'message': str(e),
            'processed': 0
        }), 500


# ==================== 主程序 ====================

# 全局变量
scheduler = None
shutdown_flag = False


def signal_handler(signum, frame):
    """信号处理器，用于优雅退出"""
    global shutdown_flag
    signal_name = signal.Signals(signum).name
    
    shutdown_flag = True
    
    # 停止调度器
    if scheduler:
        scheduler.shutdown(wait=False)
    
    logger.info(f"服务停止 (信号: {signal_name})")
    sys.exit(0)


if __name__ == '__main__':
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # kill命令
    
    # 启动定时任务调度器
    scheduler = BackgroundScheduler()
    scheduler.add_job(process_news_task, 'cron', hour='5,11,17,23', minute=30)
    scheduler.start()
    
    # 打印启动信息
    jobs = scheduler.get_jobs()
    next_run = jobs[0].next_run_time.strftime("%Y-%m-%d %H:%M:%S") if jobs else "未知"
    logger.info(f'Bloomberg服务启动 | 端口:{SERVICE_PORT} | 下次执行:{next_run}')
    
    try:
        app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False, use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        if scheduler:
            scheduler.shutdown()
        logger.info('服务停止')
