#!/usr/bin/env python3
"""
财联社新闻爬虫 - 完整版本
功能：
1. 爬取财联社加红电报新闻
2. 数据入库到远程MySQL数据库
3. AI分析新闻内容（软硬消息分类）
4. AI评分新闻影响力（0-100分）
5. AI标签新闻类型
6. 自动检查并补齐数据库字段
7. 消息处理流程跟踪功能（自动创建跟踪记录）

使用方法:
  python main.py crawl                    - 只爬取新闻
  python main.py analyze [数量]           - 只AI软硬分析最新未分析的新闻
  python main.py score [数量]             - 只AI评分最新未评分的新闻
  python main.py label [数量]             - 只AI标签最新未标签的新闻
  python main.py complete [数量]          - 完整AI处理：分析+评分+标签
  python main.py full                    - 完整流程：爬取+完整AI处理
  python main.py schedule                - 调度模式：10天，每2小时执行一次

强制处理模式（覆盖现有数据）:
  python main.py force-analyze [ID文件]   - 强制分析指定ID的新闻
  python main.py force-score [ID文件]     - 强制评分指定ID的新闻
  python main.py force-label [ID文件]     - 强制标签指定ID的新闻
  python main.py force-complete [ID文件]  - 强制完整AI处理指定ID的新闻

ID文件格式: 每行一个新闻ID，默认使用 force_process_ids.txt
"""

import sys
import os
import time
import json
import logging
import traceback
import asyncio
import re
import requests
import aiohttp
import pymysql
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== 配置参数 ====================

# 数据库配置
DB_CONFIG = {
    'host': 'rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'ysd',
    'password': 'Yan1234567',
    'database': 'futures',
    'charset': 'utf8mb4'
}

# AI API 配置
AI_API_KEY = "sk-qVU4OZNspU5cSTPONFBFD000t2Oy8Tq9U8h74Wm5Phnl8tsB"
AI_BASE_URL = "https://poloai.top/v1/chat/completions"

# AI分析提示词
PROMPT = """
请根据以下步骤，判断多条消息的"硬度"：

1. **市场类型识别**  
   判断消息主要针对【股票市场】还是【期货市场】。

2. **软硬消息分类标准**  
   - 如果是【股票市场】：  
     - **硬消息（直接影响公司基本面）**：财报数据、业绩指引、实际订单/合同、并购重组、资产买卖、分红派息、回购计划  
     - **软消息（间接影响或情绪炒作）**：市场传闻、概念炒作、分析师观点、评级调整、行业趋势、宏观预期  

   - 如果是【期货市场】：  
     - **硬消息（直接影响供需平衡）**：  
       - 生产端：限产、检修、安全检查、环保约束  
       - 流通端：进出口政策调整、关税/配额变化  
       - 消费端：下游需求突然增减（如补库、停产）  
     - **软消息（间接影响或情绪炒作）**：  
       - 政策层：行业倡议、指导意见、会议讲话  
       - 市场层：传闻、概念联想、模糊预期  
       - 舆情层：媒体解读、情绪带动  

3. **格式化输出**  
请用以下格式输出：  
- 【股票市场/期货市场】，分类：[硬消息/软消息]  
- 理由：一句简短解释  
"""

# AI评分提示词
SCORING_PROMPT = """
message_score是消息评分，分数越高表示影响力越大
请你对下面的单条新闻，根据其对股票市场或期货市场的潜在影响，给出一个 1-10 的数字，数字越大表示市场影响力越强。  
评估时请考虑以下维度：

## 新闻重要性评分标准 (1-10分)

### 10分 - 世纪级事件
- **定义**：百年一遇，改变人类历史进程的重大事件
- **特征**：全球性影响、历史转折点、载入史册
- **举例**：世界大战爆发/结束、人类登月、重大疫情全球大流行

### 9分 - 历史性事件  
- **定义**：数十年一遇的重大历史事件
- **特征**：深远影响、改变国际格局、历史性突破
- **举例**：柏林墙倒塌、重大科技革命性突破、超级大国解体

### 8分 - 国际重大事件
- **定义**：影响多国的重大国际事件
- **特征**：跨国影响、改变地区格局、国际高度关注
- **举例**：重要国家政权更迭、重大国际协议签署、区域战争

### 7分 - 国家级重大事件
- **定义**：影响整个国家的重大事件
- **特征**：全国性影响、政策重大调整、社会深度关注
- **举例**：国家领导人更替、重大法律出台、全国性自然灾害

### 6分 - 重要社会事件
- **定义**：引起广泛社会讨论的重要事件
- **特征**：社会热议、持续关注、影响民生
- **举例**：重大政策调整、知名人物重大丑闻、重要企业倒闭

### 5分 - 一般重要新闻
- **定义**：有一定影响力的新闻事件
- **特征**：区域性影响、行业关注、短期热点
- **举例**：地方重要政策、行业重大变动、明星热点事件

### 4分 - 常规新闻
- **定义**：日常报道的一般新闻
- **特征**：例行报道、有限影响、快速遗忘
- **举例**：普通交通事故、一般企业动态、常规政府公告

### 3分 - 轻微新闻
- **定义**：影响较小的新闻
- **特征**：局部影响、关注度低、信息价值有限
- **举例**：小型活动报道、普通人事任命、日常社会新闻

### 2分 - 琐碎新闻
- **定义**：几乎无影响力的琐事
- **特征**：极小范围、快速过时、填充版面
- **举例**：明星日常动态、鸡毛蒜皮的争议、天气预报

### 1分 - 陈词滥调
- **定义**：毫无新意、反复出现的内容
- **特征**：老生常谈、毫无价值、听觉疲劳
- **举例**：例行工作报道、重复性通知、毫无新意的评论

输出要求（严格按 JSON 返回）：  

{
  "message_score": 数字 (1-10),
  "message_score_rationale": "一句中文解释，说明为什么给这个分数"
}

下面是新闻内容：  
[在这里插入消息文本]
"""

# AI类型标签提示词
LABELING_PROMPT = """
# 新闻消息类型智能分类

你是一位专业的金融新闻分析师，请根据新闻内容的核心要素和实际影响，为其分配最准确的消息类型标签。

## 分类原则
1. **深入理解内容本质**：不要被表面文字限制，要理解新闻的实际含义和影响
2. **灵活创新**：如果现有类型不够准确，可以创建更贴切的新标签
3. **精准定位**：选择最能反映新闻核心信息的标签，避免过于宽泛

## 常见类型参考（可扩展）

### 政策监管类
- **利好政策**：政府出台有利于行业/企业发展的政策、补贴、税收优惠等
- **利空政策**：监管收紧、限制措施、处罚决定等负面政策影响

### 资本运作类
- **并购重组**：企业收购、合并、资产重组的计划或进展
- **股权变动**：减持公告、增持公告、股权转让、大股东变更等
- **融资活动**：IPO、增发、发债、贷款等融资相关

### 经营业绩类
- **财报数据**：季报、年报等定期财务报告
- **业绩预告**：业绩预增、预减、扭亏为盈等前瞻性公告
- **分红派息**：现金分红、送股、配股等利润分配方案

### 业务发展类
- **重大订单**：签约大额合同、中标重要项目、战略合作等
- **产能调整**：扩产、减产、停产检修、新产线投产等
- **产品创新**：新产品发布、技术突破、研发进展等

### 市场环境类
- **行业动态**：行业供需变化、价格波动、竞争格局等
- **国际贸易**：进出口数据、关税调整、贸易摩擦等
- **市场传闻**：未经证实的消息、分析师观点、媒体报道等

## 分类思路
1. 识别新闻的**主体**（谁）
2. 判断核心**事件**（做什么）
3. 评估**影响性质**（利好/利空/中性）
4. 确定**信息类型**（政策/经营/市场等）

## 输出要求
**重要：必须严格按照以下JSON格式返回，不要添加任何其他文字说明！**

{
  "message_type": "最贴切的标签名称",
  "message_type_rationale": "简要说明选择该标签的核心理由（限制在100字以内）"
}

**注意：**
1. 只返回JSON格式，不要包含markdown代码块标记
2. message_type_rationale字段内容要简洁明了
3. 确保JSON格式完整且可解析

下面是新闻内容：  
[在这里插入消息文本]
"""




# ==================== 数据库操作函数 ====================

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def check_and_update_database_schema():
    """检查并更新数据库字段结构"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        logger.info("开始检查数据库字段结构...")
        
        # 检查表是否存在，如果不存在则创建
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
        
        # 创建消息处理流程跟踪表
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
        
        # 获取当前表结构
        cursor.execute("DESCRIBE news_red_telegraph")
        existing_columns = {row[0]: row for row in cursor.fetchall()}
        
        # 需要检查和添加的字段
        required_columns = {
            'message_score': "ADD COLUMN message_score TINYINT UNSIGNED",
            'message_score_rationale': "ADD COLUMN message_score_rationale VARCHAR(500)",
            'message_label': "ADD COLUMN message_label ENUM('hard','soft','unknown') DEFAULT 'unknown'",
            'message_type': "ADD COLUMN message_type VARCHAR(64)",
            'message_type_rationale': "ADD COLUMN message_type_rationale VARCHAR(500)",
            'market_react': "ADD COLUMN market_react VARCHAR(255)",
            'screenshots': "ADD COLUMN screenshots JSON",
            'updated_at': "ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        }
        
        # 检查并添加缺失的字段
        for column_name, add_sql in required_columns.items():
            if column_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE news_red_telegraph {add_sql}")
                    logger.info(f"添加字段: {column_name}")
                except Exception as e:
                    logger.warning(f"添加字段 {column_name} 失败: {e}")
        
        conn.commit()
        logger.info("数据库字段结构检查完成")
        
        # 补齐缺失的跟踪记录
        logger.info("开始检查并补齐跟踪记录...")
        missing_count = create_missing_tracking_records()
        if missing_count > 0:
            logger.info(f"补齐了 {missing_count} 条缺失的跟踪记录")
        
    except Exception as e:
        logger.error(f"数据库字段检查失败: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def save_news_to_db(news_data):
    """保存新闻数据到数据库"""
    if not news_data:
        return 0, 0
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    new_count = 0
    duplicate_count = 0
    
    try:
        for news_item in news_data:
            ctime = news_item.get('ctime')
            title = news_item.get('title', '')
            content = news_item.get('content', '')
            
            if not ctime or not title:
                continue
                
            try:
                # 开始事务处理
                conn.begin()
                
                # 清理HTML标签
                title = re.sub(r'<[^>]+>', '', title)
                content = re.sub(r'<[^>]+>', '', content)
                
                # 插入新闻记录
                cursor.execute("""
                    INSERT INTO news_red_telegraph (ctime, title, content)
                    VALUES (%s, %s, %s)
                """, (ctime, title, content))
                
                # 获取新插入的新闻ID
                news_id = cursor.lastrowid
                
                # 同步创建跟踪记录
                cursor.execute("""
                    INSERT INTO news_process_tracking (news_id, ctime)
                    VALUES (%s, %s)
                """, (news_id, ctime))
                
                # 提交事务
                conn.commit()
                
                new_count += 1
                logger.info(f"保存新闻及跟踪记录: {title[:50]}... (ID: {news_id})")
                
            except pymysql.IntegrityError as e:
                conn.rollback()
                if e.args[0] == 1062:  # Duplicate entry
                    duplicate_count += 1
                    logger.debug(f"新闻已存在，跳过: {title[:50]}...")
                else:
                    logger.error(f"保存新闻时出错: {e}")
            except Exception as e:
                conn.rollback()
                logger.error(f"保存新闻及跟踪记录时出错: {e}")
        
        logger.info(f"新闻保存完成: 新增{new_count}条, 重复{duplicate_count}条")
        return new_count, duplicate_count
        
    except Exception as e:
        logger.error(f"保存新闻数据失败: {e}")
        conn.rollback()
        return 0, 0
    finally:
        cursor.close()
        conn.close()

# ==================== 跟踪表操作函数 ====================

def create_missing_tracking_records():
    """为缺失跟踪记录的新闻创建跟踪记录（只包含基础字段）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 查找没有跟踪记录的新闻
        cursor.execute("""
            SELECT n.id, n.ctime
            FROM news_red_telegraph n
            LEFT JOIN news_process_tracking t ON n.id = t.news_id
            WHERE t.news_id IS NULL
        """)
        
        missing_news = cursor.fetchall()
        
        if not missing_news:
            logger.info("所有新闻都已有跟踪记录")
            return 0
        
        # 批量创建跟踪记录
        created_count = 0
        for news_id, ctime in missing_news:
            try:
                cursor.execute("""
                    INSERT INTO news_process_tracking (news_id, ctime)
                    VALUES (%s, %s)
                """, (news_id, ctime))
                created_count += 1
            except pymysql.IntegrityError as e:
                if e.args[0] == 1062:  # Duplicate entry
                    logger.debug(f"跟踪记录已存在，跳过新闻ID: {news_id}")
                else:
                    logger.error(f"创建跟踪记录失败，新闻ID: {news_id}, 错误: {e}")
        
        conn.commit()
        logger.info(f"补齐跟踪记录完成: 新增{created_count}条")
        return created_count
        
    except Exception as e:
        logger.error(f"补齐跟踪记录失败: {e}")
        conn.rollback()
        return 0
    finally:
        cursor.close()
        conn.close()

def get_unanalyzed_news(count=10):
    """获取未分析的新闻"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("""
            SELECT id, title, content 
            FROM news_red_telegraph 
            WHERE ai_analysis IS NULL 
            ORDER BY ctime DESC 
            LIMIT %s
        """, (count,))
        
        news_list = cursor.fetchall()
        return news_list
        
    except Exception as e:
        logger.error(f"获取未分析新闻失败: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def auto_classify_message_label(analysis_text):
    """根据AI分析文本自动分类消息标签"""
    if not analysis_text:
        return 'unknown'
    
    # 将分析文本转换为小写进行匹配
    analysis_lower = analysis_text.lower()
    
    if '硬消息' in analysis_text:
        return 'hard'
    elif '软消息' in analysis_text:
        return 'soft'
    else:
        return 'unknown'

def update_news_analysis_results(results):
    """更新新闻分析结果到数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    success_count = 0
    failure_count = 0
    
    try:
        for result in results:
            try:
                # 自动分类消息标签
                message_label = auto_classify_message_label(result['analysis'])
                
                cursor.execute("""
                    UPDATE news_red_telegraph 
                    SET ai_analysis = %s, message_label = %s, updated_at = NOW()
                    WHERE id = %s
                """, (result['analysis'], message_label, result['id']))
                
                if result['success']:
                    success_count += 1
                    logger.debug(f"新闻ID {result['id']} 自动标记为: {message_label}")
                else:
                    failure_count += 1
                    
            except Exception as e:
                logger.error(f"更新新闻分析结果失败 - ID: {result['id']}, 错误: {e}")
                failure_count += 1
        
        conn.commit()
        logger.info(f"批量更新完成: 成功 {success_count} 条, 失败 {failure_count} 条")
        return success_count, failure_count
        
    except Exception as e:
        logger.error(f"批量更新新闻分析结果失败: {e}")
        conn.rollback()
        return 0, len(results)
    finally:
        cursor.close()
        conn.close()

# ==================== AI分析函数 ====================

async def analyze_single_news_async(session, prompt=None, news_item=None, max_retries=1):
    """异步分析单条新闻（带重试机制）"""
    # 如果没有提供prompt，使用默认的PROMPT变量
    if prompt is None:
        prompt = PROMPT
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "你是一个财经消息分类助手。"},
            {"role": "user", "content": f"{prompt}\n\n新闻标题：{news_item['title']}\n新闻内容：{news_item['content']}"}
        ],
        "max_tokens": 500,
        "temperature": 0.7
    }
    
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {AI_API_KEY}",
        'User-Agent': 'PoloAPI/1.0.0 (https://poloai.top)',
        "Content-Type": "application/json"
    }
    
    # 重试机制
    for attempt in range(max_retries + 1):
        try:
            timeout_duration = 60 + (attempt * 30)  # 每次重试增加30秒超时时间
            
            async with session.post(AI_BASE_URL, json=payload, headers=headers, timeout=timeout_duration) as response:
                if response.status == 200:
                    result = await response.json()
                    analysis_result = result["choices"][0]["message"]["content"]
                    retry_info = f" (重试{attempt}次)" if attempt > 0 else ""
                    logger.info(f"AI分析完成{retry_info} - 新闻ID: {news_item['id']}, 结果: {analysis_result[:50]}...")
                    return {
                        'id': news_item['id'],
                        'analysis': analysis_result[:1000],  # 限制长度
                        'success': True
                    }
                else:
                    error_msg = f"AI请求失败: HTTP {response.status}"
                    if attempt < max_retries:
                        logger.warning(f"{error_msg} - 新闻ID: {news_item['id']}, 准备重试 ({attempt + 1}/{max_retries})")
                        await asyncio.sleep(2 ** attempt)  # 指数退避
                        continue
                    else:
                        logger.error(f"{error_msg} - 新闻ID: {news_item['id']}, 重试次数已用完")
                        return {
                            'id': news_item['id'],
                            'analysis': error_msg,
                            'success': False
                        }
                        
        except asyncio.TimeoutError:
            error_msg = f"AI请求超时 (超时时间: {timeout_duration}秒)"
            if attempt < max_retries:
                logger.warning(f"{error_msg} - 新闻ID: {news_item['id']}, 准备重试 ({attempt + 1}/{max_retries})")
                await asyncio.sleep(2 ** attempt)  # 指数退避
                continue
            else:
                logger.warning(f"{error_msg} - 新闻ID: {news_item['id']}, 重试次数已用完")
                return {
                    'id': news_item['id'],
                    'analysis': "AI请求超时",
                    'success': False
                }
        except Exception as e:
            error_msg = f"AI分析异常: {str(e)[:100]}"
            if attempt < max_retries:
                logger.warning(f"{error_msg} - 新闻ID: {news_item['id']}, 准备重试 ({attempt + 1}/{max_retries})")
                await asyncio.sleep(2 ** attempt)  # 指数退避
                continue
            else:
                logger.error(f"{error_msg} - 新闻ID: {news_item['id']}, 重试次数已用完")
                return {
                    'id': news_item['id'],
                    'analysis': error_msg,
                    'success': False
                }

async def batch_analyze_news_async(prompt=None, news_list=None):
    """批量异步分析新闻"""
    results = []
    
    async with aiohttp.ClientSession() as session:
        # 创建任务列表
        tasks = []
        for news_item in news_list:
            task = analyze_single_news_async(session, prompt=prompt, news_item=news_item)
            tasks.append(task)
        
        # 批量执行，但控制并发数量
        semaphore = asyncio.Semaphore(10)  # 限制并发数为10
        
        async def bounded_task(task):
            async with semaphore:
                return await task
        
        bounded_tasks = [bounded_task(task) for task in tasks]
        results = await asyncio.gather(*bounded_tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"任务执行异常 - 新闻ID: {news_list[i]['id']}, 错误: {result}")
                processed_results.append({
                    'id': news_list[i]['id'],
                    'analysis': f"任务执行异常: {str(result)[:100]}",
                    'success': False
                })
            else:
                processed_results.append(result)
        
        return processed_results

async def analyze_single_news_scoring_async(session, news_item, max_retries=1):
    """异步分析单条新闻进行评分（带重试机制）"""
    # 替换提示词中的占位符
    prompt_content = SCORING_PROMPT.replace("[在这里插入消息文本]", f"标题：{news_item['title']}\n内容：{news_item['content']}")
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "你是一个财经消息评估助手，专门为新闻评分。"},
            {"role": "user", "content": prompt_content}
        ],
        "max_tokens": 500,
        "temperature": 0.3
    }
    
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {AI_API_KEY}",
        'User-Agent': 'PoloAPI/1.0.0 (https://poloai.top)',
        "Content-Type": "application/json"
    }
    
    # 重试机制
    for attempt in range(max_retries + 1):
        try:
            timeout_duration = 60 + (attempt * 30)  # 每次重试增加30秒超时时间
            
            async with session.post(AI_BASE_URL, json=payload, headers=headers, timeout=timeout_duration) as response:
                if response.status == 200:
                    result = await response.json()
                    scoring_result = result["choices"][0]["message"]["content"]
                    
                    # 尝试解析JSON结果
                    try:
                        import json as json_module
                        score_data = json_module.loads(scoring_result)
                        message_score = score_data.get('message_score', 0)
                        message_score_rationale = score_data.get('message_score_rationale', '解析失败')
                        
                        # 确保评分在有效范围内
                        if not isinstance(message_score, (int, float)) or message_score < 0 or message_score > 100:
                            message_score = 0
                            message_score_rationale = "评分超出范围"
                        
                    except (json_module.JSONDecodeError, TypeError):
                        # JSON解析失败时的备用方案
                        message_score = 0
                        message_score_rationale = f"JSON解析失败: {scoring_result[:100]}"
                    
                    retry_info = f" (重试{attempt}次)" if attempt > 0 else ""
                    logger.info(f"AI评分完成{retry_info} - 新闻ID: {news_item['id']}, 评分: {message_score}")
                    return {
                        'id': news_item['id'],
                        'message_score': int(message_score),
                        'message_score_rationale': message_score_rationale[:500],  # 限制长度
                        'success': True
                    }
                else:
                    error_msg = f"AI请求失败: HTTP {response.status}"
                    if attempt < max_retries:
                        logger.warning(f"{error_msg} - 新闻ID: {news_item['id']}, 准备重试 ({attempt + 1}/{max_retries})")
                        await asyncio.sleep(2 ** attempt)  # 指数退避
                        continue
                    else:
                        logger.error(f"{error_msg} - 新闻ID: {news_item['id']}, 重试次数已用完")
                        return {
                            'id': news_item['id'],
                            'message_score': 0,
                            'message_score_rationale': error_msg,
                            'success': False
                        }
                        
        except asyncio.TimeoutError:
            error_msg = f"AI请求超时 (超时时间: {timeout_duration}秒)"
            if attempt < max_retries:
                logger.warning(f"{error_msg} - 新闻ID: {news_item['id']}, 准备重试 ({attempt + 1}/{max_retries})")
                await asyncio.sleep(2 ** attempt)  # 指数退避
                continue
            else:
                logger.warning(f"{error_msg} - 新闻ID: {news_item['id']}, 重试次数已用完")
                return {
                    'id': news_item['id'],
                    'message_score': 0,
                    'message_score_rationale': "AI请求超时",
                    'success': False
                }
        except Exception as e:
            error_msg = f"AI分析异常: {str(e)[:100]}"
            if attempt < max_retries:
                logger.warning(f"{error_msg} - 新闻ID: {news_item['id']}, 准备重试 ({attempt + 1}/{max_retries})")
                await asyncio.sleep(2 ** attempt)  # 指数退避
                continue
            else:
                logger.error(f"{error_msg} - 新闻ID: {news_item['id']}, 重试次数已用完")
                return {
                    'id': news_item['id'],
                    'message_score': 0,
                    'message_score_rationale': error_msg,
                    'success': False
                }

async def analyze_single_news_labeling_async(session, news_item, max_retries=1):
    """异步分析单条新闻进行类型标签（带重试机制）"""
    # 替换提示词中的占位符
    prompt_content = LABELING_PROMPT.replace("[在这里插入消息文本]", f"标题：{news_item['title']}\n内容：{news_item['content']}")
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": "你是一个财经消息分类助手，专门为新闻打标签。请严格按照JSON格式返回结果。"},
            {"role": "user", "content": prompt_content}
        ],
        "max_tokens": 800,  # 增加token数量避免截断
        "temperature": 0.1  # 降低温度提高一致性
    }
    
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {AI_API_KEY}",
        'User-Agent': 'PoloAPI/1.0.0 (https://poloai.top)',
        "Content-Type": "application/json"
    }
    
    # 重试机制
    for attempt in range(max_retries + 1):
        try:
            timeout_duration = 60 + (attempt * 30)  # 每次重试增加30秒超时时间
            
            async with session.post(AI_BASE_URL, json=payload, headers=headers, timeout=timeout_duration) as response:
                if response.status == 200:
                    result = await response.json()
                    labeling_result = result["choices"][0]["message"]["content"]
                    
                    # 尝试解析JSON结果
                    try:
                        import json as json_module
                        import re
                        
                        # 记录完整的AI响应用于调试
                        logger.debug(f"AI完整响应 - 新闻ID: {news_item['id']}, 响应长度: {len(labeling_result)}, 内容: {labeling_result}")
                        
                        # 首先尝试直接解析JSON
                        try:
                            label_data = json_module.loads(labeling_result)
                            message_type = label_data.get('message_type', '其他')
                            message_type_rationale = label_data.get('message_type_rationale', '解析失败')
                            logger.info(f"JSON直接解析成功 - 新闻ID: {news_item['id']}, 标签: {message_type}")
                            
                        except json_module.JSONDecodeError:
                            # 如果直接解析失败，尝试提取JSON部分
                            logger.warning(f"JSON直接解析失败，尝试智能提取 - 新闻ID: {news_item['id']}")
                            
                            # 查找JSON代码块
                            json_match = re.search(r'```json\s*(\{.*?\})\s*```', labeling_result, re.DOTALL)
                            if json_match:
                                json_content = json_match.group(1)
                                logger.debug(f"提取到JSON代码块: {json_content}")
                                try:
                                    label_data = json_module.loads(json_content)
                                    message_type = label_data.get('message_type', '其他')
                                    message_type_rationale = label_data.get('message_type_rationale', '解析失败')
                                    logger.info(f"JSON代码块解析成功 - 新闻ID: {news_item['id']}, 标签: {message_type}")
                                except json_module.JSONDecodeError:
                                    raise ValueError("JSON代码块解析失败")
                            else:
                                # 尝试查找裸JSON
                                json_match = re.search(r'\{[^{}]*"message_type"[^{}]*\}', labeling_result, re.DOTALL)
                                if json_match:
                                    json_content = json_match.group(0)
                                    logger.debug(f"提取到裸JSON: {json_content}")
                                    try:
                                        label_data = json_module.loads(json_content)
                                        message_type = label_data.get('message_type', '其他')
                                        message_type_rationale = label_data.get('message_type_rationale', '解析失败')
                                        logger.info(f"裸JSON解析成功 - 新闻ID: {news_item['id']}, 标签: {message_type}")
                                    except json_module.JSONDecodeError:
                                        raise ValueError("裸JSON解析失败")
                                else:
                                    # 尝试使用正则表达式提取字段
                                    message_type_match = re.search(r'"message_type":\s*"([^"]*)"', labeling_result)
                                    rationale_match = re.search(r'"message_type_rationale":\s*"([^"]*)"', labeling_result)
                                    
                                    if message_type_match:
                                        message_type = message_type_match.group(1)
                                        message_type_rationale = rationale_match.group(1) if rationale_match else "理由提取失败"
                                        logger.info(f"正则表达式提取成功 - 新闻ID: {news_item['id']}, 标签: {message_type}")
                                    else:
                                        raise ValueError("无法提取任何有效信息")
                        
                    except (json_module.JSONDecodeError, TypeError, ValueError) as e:
                        # 所有解析方法都失败时的备用方案
                        logger.error(f"所有JSON解析方法都失败 - 新闻ID: {news_item['id']}, 错误: {e}")
                        message_type = '其他'
                        # 提供更详细的错误信息，但限制长度
                        error_detail = f"解析失败({str(e)[:50]}): {labeling_result[:200]}..."
                        message_type_rationale = error_detail
                    
                    retry_info = f" (重试{attempt}次)" if attempt > 0 else ""
                    logger.info(f"AI标签完成{retry_info} - 新闻ID: {news_item['id']}, 标签: {message_type}")
                    return {
                        'id': news_item['id'],
                        'message_type': message_type[:64],  # 限制长度
                        'message_type_rationale': message_type_rationale[:500],  # 限制长度
                        'success': True
                    }
                else:
                    error_msg = f"AI请求失败: HTTP {response.status}"
                    if attempt < max_retries:
                        logger.warning(f"{error_msg} - 新闻ID: {news_item['id']}, 准备重试 ({attempt + 1}/{max_retries})")
                        await asyncio.sleep(2 ** attempt)  # 指数退避
                        continue
                    else:
                        logger.error(f"{error_msg} - 新闻ID: {news_item['id']}, 重试次数已用完")
                        return {
                            'id': news_item['id'],
                            'message_type': '其他',
                            'message_type_rationale': error_msg,
                            'success': False
                        }
                        
        except asyncio.TimeoutError:
            error_msg = f"AI请求超时 (超时时间: {timeout_duration}秒)"
            if attempt < max_retries:
                logger.warning(f"{error_msg} - 新闻ID: {news_item['id']}, 准备重试 ({attempt + 1}/{max_retries})")
                await asyncio.sleep(2 ** attempt)  # 指数退避
                continue
            else:
                logger.warning(f"{error_msg} - 新闻ID: {news_item['id']}, 重试次数已用完")
                return {
                    'id': news_item['id'],
                    'message_type': '其他',
                    'message_type_rationale': "AI请求超时",
                    'success': False
                }
        except Exception as e:
            error_msg = f"AI分析异常: {str(e)[:100]}"
            if attempt < max_retries:
                logger.warning(f"{error_msg} - 新闻ID: {news_item['id']}, 准备重试 ({attempt + 1}/{max_retries})")
                await asyncio.sleep(2 ** attempt)  # 指数退避
                continue
            else:
                logger.error(f"{error_msg} - 新闻ID: {news_item['id']}, 重试次数已用完")
                return {
                    'id': news_item['id'],
                    'message_type': '其他',
                    'message_type_rationale': error_msg,
                    'success': False
                }

# ==================== 爬虫类和函数 ====================

class ClsNewsCrawler:
    """财联社加红电报新闻爬虫"""
    
    def __init__(self, headless=True):
        self.driver = None
        self.headless = headless
        self.network_logs = []
        
    def setup_driver(self):
        """设置Chrome驱动"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        # 基本配置
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--window-size=1280,720')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 启用网络日志记录
        chrome_options.add_argument('--enable-logging')
        chrome_options.add_argument('--log-level=0')
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        try:
            # 尝试使用系统默认的Chrome/Chromium
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome驱动初始化成功")
        except Exception as e:
            logger.error(f"Chrome驱动初始化失败: {e}")
            # 尝试指定ChromeDriver路径
            try:
                service = Service()  # 使用系统PATH中的chromedriver
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("使用系统PATH驱动初始化成功")
            except Exception as e2:
                logger.error(f"所有驱动初始化方案都失败: {e2}")
                raise
        
        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(10)
    
    def get_network_logs(self):
        """获取网络请求日志"""
        try:
            logs = self.driver.get_log('performance')
            network_requests = []
            
            for log in logs:
                try:
                    message = json.loads(log['message'])
                    if message['message']['method'] == 'Network.responseReceived':
                        url = message['message']['params']['response']['url']
                        if 'cls.cn/v1/roll/get_roll_list' in url:
                            network_requests.append({
                                'url': url,
                                'timestamp': log['timestamp'],
                                'response': message['message']['params']['response']
                            })
                except (json.JSONDecodeError, KeyError):
                    continue
            
            return network_requests
        except Exception as e:
            logger.error(f"获取网络日志失败: {e}")
            return []
    
    def extract_params_from_url(self, url):
        """从URL中提取参数"""
        params = {}
        if '?' in url:
            query_string = url.split('?')[1]
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value
        return params
    
    def click_jiahong_button(self):
        """点击加红按钮"""
        logger.info("开始寻找并点击'加红'按钮...")
        
        # 等待页面加载完成
        try:
            WebDriverWait(self.driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
        except Exception as e:
            logger.warning(f"等待页面加载完成失败: {e}")
        
        # 多种选择器策略
        selectors = [
            "//a[contains(text(), '加红')]",
            "//h3[contains(@class, 'level-2-nav')]//a[contains(text(), '加红')]",
            "//h3[@class='f-l f-s-17 level-2-nav']//a[@class='p-r d-b w-94 c-p c-ef9524']",
            "//a[@class='p-r d-b w-94 c-p c-ef9524']",
            "//a[contains(@class, 'c-ef9524')]"
        ]
        
        for i, selector in enumerate(selectors):
            try:
                logger.info(f"尝试选择器 {i+1}: {selector}")
                elements = self.driver.find_elements(By.XPATH, selector)
                
                if elements:
                    element = elements[0]
                    logger.info(f"找到元素: {element.text[:50]}")
                    
                    # 滚动到元素位置
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(1)
                    
                    # 尝试点击
                    try:
                        element.click()
                        logger.info("成功点击'加红'按钮")
                        return True
                    except:
                        # 使用JavaScript点击
                        self.driver.execute_script("arguments[0].click();", element)
                        logger.info("使用JavaScript成功点击'加红'按钮")
                        return True
                        
            except Exception as e:
                logger.warning(f"选择器 {i+1} 执行失败: {e}")
                continue
        
        logger.error("未能找到或点击'加红'按钮")
        return False
    
    def make_api_request(self, url):
        """使用浏览器的cookies和headers发起API请求"""
        try:
            # 获取浏览器的cookies
            cookies = self.driver.get_cookies()
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            
            # 设置请求头
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Content-Type': 'application/json;charset=utf-8',
                'Pragma': 'no-cache',
                'Referer': 'https://www.cls.cn/telegraph',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            logger.info(f"发起API请求: {url[:100]}...")
            response = requests.get(url, headers=headers, cookies=cookie_dict, timeout=15)
            response.raise_for_status()
            
            json_data = response.json()
            logger.info("API请求成功")
            return json_data
            
        except Exception as e:
            logger.error(f"API请求失败: {e}")
            return None
    
    def crawl_news(self):
        """爬取财联社加红电报新闻"""
        try:
            logger.info("开始爬取财联社加红电报新闻")
            
            # 访问页面
            url = "https://www.cls.cn/telegraph"
            logger.info(f"访问页面: {url}")
            self.driver.get(url)
            
            # 等待页面加载
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.info("页面加载完成，等待12秒...")
            time.sleep(12)
            
            # 点击加红按钮
            click_success = self.click_jiahong_button()
            
            if click_success:
                logger.info("点击成功，等待网络请求...")
                time.sleep(10)
            else:
                logger.warning("点击失败，尝试其他方式...")
                # 尝试滚动页面触发请求
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(6)
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(4)
            
            # 获取网络请求日志
            network_requests = self.get_network_logs()
            logger.info(f"捕获到 {len(network_requests)} 个网络请求")
            
            # 处理API数据
            news_data = []
            for request in network_requests:
                url = request['url']
                params = self.extract_params_from_url(url)
                
                if params.get('sign'):
                    logger.info(f"发现API请求，sign: {params.get('sign')}")
                    
                    # 尝试获取数据
                    try:
                        response = self.make_api_request(url)
                        if response and response.get('errno') == 0:
                            roll_data = response.get('data', {}).get('roll_data', [])
                            news_data.extend(roll_data)
                            logger.info(f"成功获取 {len(roll_data)} 条新闻")
                    except Exception as e:
                        logger.warning(f"API请求失败: {e}")
            
            return news_data
            
        except Exception as e:
            logger.error(f"爬取新闻失败: {e}")
            return []
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")

# ==================== 主业务函数 ====================

def crawl_cls_news():
    """爬取财联社新闻的主函数"""
    crawler = None
    try:
        logger.info("开始财联社新闻爬取任务")
        
        # 创建爬虫实例
        crawler = ClsNewsCrawler(headless=True)
        crawler.setup_driver()
        
        # 爬取新闻
        news_data = crawler.crawl_news()
        
        if news_data:
            # 保存到数据库
            new_count, duplicate_count = save_news_to_db(news_data)
            logger.info(f"爬取任务完成: 获取{len(news_data)}条新闻, 新增{new_count}条, 重复{duplicate_count}条")
            return new_count, duplicate_count, len(news_data)
        else:
            logger.warning("未获取到新闻数据")
            return 0, 0, 0
            
    except Exception as e:
        logger.error(f"爬取任务执行失败: {e}")
        logger.error(traceback.format_exc())
        return 0, 0, 0
    finally:
        if crawler:
            crawler.close()

def analyze_latest_news(count=10, prompt=None):
    """分析最新的未分析新闻"""
    if prompt is None:
        prompt = PROMPT
    
    try:    
        logger.info(f"开始批量AI分析任务 - 数量: {count}")
        
        # 获取最新的未分析新闻
        news_list = get_unanalyzed_news(count)
        
        if not news_list:
            logger.warning("没有找到需要分析的新闻")
            return 0, 0
        
        logger.info(f"获取到 {len(news_list)} 条待分析新闻")
        
        # 异步批量分析
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(batch_analyze_news_async(prompt=prompt, news_list=news_list))
            
            # 更新数据库
            success_count, failure_count = update_news_analysis_results(results)
            logger.info(f"批量AI分析任务完成: 成功 {success_count} 条, 失败 {failure_count} 条")
            return success_count, failure_count
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"批量分析任务执行失败: {e}")
        logger.error(traceback.format_exc())
        return 0, 0

async def batch_analyze_news_scoring_async(news_list):
    """批量异步分析新闻评分"""
    results = []
    
    async with aiohttp.ClientSession() as session:
        # 创建任务列表
        tasks = []
        for news_item in news_list:
            task = analyze_single_news_scoring_async(session, news_item)
            tasks.append(task)
        
        # 批量执行，但控制并发数量
        semaphore = asyncio.Semaphore(8)  # 限制并发数为8
        
        async def bounded_task(task):
            async with semaphore:
                return await task
        
        bounded_tasks = [bounded_task(task) for task in tasks]
        results = await asyncio.gather(*bounded_tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"评分任务执行异常 - 新闻ID: {news_list[i]['id']}, 错误: {result}")
                processed_results.append({
                    'id': news_list[i]['id'],
                    'message_score': 0,
                    'message_score_rationale': f"任务执行异常: {str(result)[:100]}",
                    'success': False
                })
            else:
                processed_results.append(result)
        
        return processed_results

async def batch_analyze_news_labeling_async(news_list):
    """批量异步分析新闻标签"""
    results = []
    
    async with aiohttp.ClientSession() as session:
        # 创建任务列表
        tasks = []
        for news_item in news_list:
            task = analyze_single_news_labeling_async(session, news_item)
            tasks.append(task)
        
        # 批量执行，但控制并发数量
        semaphore = asyncio.Semaphore(8)  # 限制并发数为8
        
        async def bounded_task(task):
            async with semaphore:
                return await task
        
        bounded_tasks = [bounded_task(task) for task in tasks]
        results = await asyncio.gather(*bounded_tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"标签任务执行异常 - 新闻ID: {news_list[i]['id']}, 错误: {result}")
                processed_results.append({
                    'id': news_list[i]['id'],
                    'message_type': '其他',
                    'message_type_rationale': f"任务执行异常: {str(result)[:100]}",
                    'success': False
                })
            else:
                processed_results.append(result)
        
        return processed_results

def update_news_scoring_results(results):
    """更新新闻评分结果到数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    success_count = 0
    failure_count = 0
    
    try:
        for result in results:
            try:
                cursor.execute("""
                    UPDATE news_red_telegraph 
                    SET message_score = %s, message_score_rationale = %s, updated_at = NOW()
                    WHERE id = %s
                """, (result['message_score'], result['message_score_rationale'], result['id']))
                
                if result['success']:
                    success_count += 1
                else:
                    failure_count += 1
                    
            except Exception as e:
                logger.error(f"更新新闻评分结果失败 - ID: {result['id']}, 错误: {e}")
                failure_count += 1
        
        conn.commit()
        logger.info(f"批量更新评分完成: 成功 {success_count} 条, 失败 {failure_count} 条")
        return success_count, failure_count
        
    except Exception as e:
        logger.error(f"批量更新新闻评分结果失败: {e}")
        conn.rollback()
        return 0, len(results)
    finally:
        cursor.close()
        conn.close()

def update_news_labeling_results(results):
    """更新新闻标签结果到数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    success_count = 0
    failure_count = 0
    
    try:
        for result in results:
            try:
                cursor.execute("""
                    UPDATE news_red_telegraph 
                    SET message_type = %s, message_type_rationale = %s, updated_at = NOW()
                    WHERE id = %s
                """, (result['message_type'], result['message_type_rationale'], result['id']))
                
                if result['success']:
                    success_count += 1
                else:
                    failure_count += 1
                    
            except Exception as e:
                logger.error(f"更新新闻标签结果失败 - ID: {result['id']}, 错误: {e}")
                failure_count += 1
        
        conn.commit()
        logger.info(f"批量更新标签完成: 成功 {success_count} 条, 失败 {failure_count} 条")
        return success_count, failure_count
        
    except Exception as e:
        logger.error(f"批量更新新闻标签结果失败: {e}")
        conn.rollback()
        return 0, len(results)
    finally:
        cursor.close()
        conn.close()

def get_unscored_news(count=10):
    """获取未评分的新闻"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("""
            SELECT id, title, content 
            FROM news_red_telegraph 
            WHERE message_score IS NULL 
            ORDER BY ctime DESC 
            LIMIT %s
        """, (count,))
        
        news_list = cursor.fetchall()
        return news_list
        
    except Exception as e:
        logger.error(f"获取未评分新闻失败: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def get_unlabeled_news(count=10):
    """获取未标签的新闻"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("""
            SELECT id, title, content 
            FROM news_red_telegraph 
            WHERE message_type IS NULL 
            ORDER BY ctime DESC 
            LIMIT %s
        """, (count,))
        
        news_list = cursor.fetchall()
        return news_list
        
    except Exception as e:
        logger.error(f"获取未标签新闻失败: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def analyze_news_scoring(count=10):
    """分析新闻评分"""
    try:    
        logger.info(f"开始批量AI评分任务 - 数量: {count}")
        
        # 获取最新的未评分新闻
        news_list = get_unscored_news(count)
        
        if not news_list:
            logger.warning("没有找到需要评分的新闻")
            return 0, 0
        
        logger.info(f"获取到 {len(news_list)} 条待评分新闻")
        
        # 异步批量评分
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(batch_analyze_news_scoring_async(news_list))
            
            # 更新数据库
            success_count, failure_count = update_news_scoring_results(results)
            logger.info(f"批量AI评分任务完成: 成功 {success_count} 条, 失败 {failure_count} 条")
            return success_count, failure_count
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"批量评分任务执行失败: {e}")
        logger.error(traceback.format_exc())
        return 0, 0

def analyze_news_labeling(count=10):
    """分析新闻标签"""
    try:    
        logger.info(f"开始批量AI标签任务 - 数量: {count}")
        
        # 获取最新的未标签新闻
        news_list = get_unlabeled_news(count)
        
        if not news_list:
            logger.warning("没有找到需要标签的新闻")
            return 0, 0
        
        logger.info(f"获取到 {len(news_list)} 条待标签新闻")
        
        # 异步批量标签
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(batch_analyze_news_labeling_async(news_list))
            
            # 更新数据库
            success_count, failure_count = update_news_labeling_results(results)
            logger.info(f"批量AI标签任务完成: 成功 {success_count} 条, 失败 {failure_count} 条")
            return success_count, failure_count
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"批量标签任务执行失败: {e}")
        logger.error(traceback.format_exc())
        return 0, 0

# ==================== 强制处理指定ID的函数 ====================

def load_force_process_ids(file_path="force_process_ids.txt"):
    """从文件中加载需要强制处理的新闻ID列表"""
    try:
        if not os.path.exists(file_path):
            logger.warning(f"ID文件不存在: {file_path}")
            return []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            ids = []
            for line in f:
                line = line.strip()
                if line and line.isdigit():
                    ids.append(int(line))
                elif line and not line.startswith('#'):  # 忽略注释行
                    logger.warning(f"无效的ID格式: {line}")
            
        logger.info(f"从文件 {file_path} 加载了 {len(ids)} 个ID: {ids}")
        return ids
        
    except Exception as e:
        logger.error(f"加载ID文件失败: {e}")
        return []

def get_news_by_ids(news_ids):
    """根据ID列表获取新闻数据"""
    if not news_ids:
        return []
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 构建IN查询
        placeholders = ','.join(['%s'] * len(news_ids))
        cursor.execute(f"""
            SELECT id, title, content 
            FROM news_red_telegraph 
            WHERE id IN ({placeholders})
            ORDER BY id DESC
        """, news_ids)
        
        news_list = cursor.fetchall()
        logger.info(f"根据ID列表获取到 {len(news_list)} 条新闻")
        return news_list
        
    except Exception as e:
        logger.error(f"根据ID获取新闻失败: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def force_analyze_news_by_ids(news_ids, prompt=None):
    """强制分析指定ID的新闻（覆盖现有数据）"""
    if not news_ids:
        logger.warning("没有提供需要强制分析的新闻ID")
        return 0, 0
    
    try:
        logger.info(f"开始强制AI分析任务 - ID列表: {news_ids}")
        
        # 根据ID获取新闻
        news_list = get_news_by_ids(news_ids)
        
        if not news_list:
            logger.warning("根据提供的ID未找到新闻")
            return 0, 0
        
        logger.info(f"获取到 {len(news_list)} 条新闻进行强制分析")
        
        # 异步批量分析
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(batch_analyze_news_async(prompt=prompt, news_list=news_list))
            
            # 强制更新数据库（覆盖现有数据）
            success_count, failure_count = force_update_news_analysis_results(results)
            logger.info(f"强制AI分析任务完成: 成功 {success_count} 条, 失败 {failure_count} 条")
            return success_count, failure_count
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"强制分析任务执行失败: {e}")
        logger.error(traceback.format_exc())
        return 0, 0

def force_analyze_news_scoring_by_ids(news_ids):
    """强制评分指定ID的新闻（覆盖现有数据）"""
    if not news_ids:
        logger.warning("没有提供需要强制评分的新闻ID")
        return 0, 0
    
    try:
        logger.info(f"开始强制AI评分任务 - ID列表: {news_ids}")
        
        # 根据ID获取新闻
        news_list = get_news_by_ids(news_ids)
        
        if not news_list:
            logger.warning("根据提供的ID未找到新闻")
            return 0, 0
        
        logger.info(f"获取到 {len(news_list)} 条新闻进行强制评分")
        
        # 异步批量评分
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(batch_analyze_news_scoring_async(news_list))
            
            # 强制更新数据库（覆盖现有数据）
            success_count, failure_count = force_update_news_scoring_results(results)
            logger.info(f"强制AI评分任务完成: 成功 {success_count} 条, 失败 {failure_count} 条")
            return success_count, failure_count
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"强制评分任务执行失败: {e}")
        logger.error(traceback.format_exc())
        return 0, 0

def force_analyze_news_labeling_by_ids(news_ids):
    """强制标签指定ID的新闻（覆盖现有数据）"""
    if not news_ids:
        logger.warning("没有提供需要强制标签的新闻ID")
        return 0, 0
    
    try:
        logger.info(f"开始强制AI标签任务 - ID列表: {news_ids}")
        
        # 根据ID获取新闻
        news_list = get_news_by_ids(news_ids)
        
        if not news_list:
            logger.warning("根据提供的ID未找到新闻")
            return 0, 0
        
        logger.info(f"获取到 {len(news_list)} 条新闻进行强制标签")
        
        # 异步批量标签
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(batch_analyze_news_labeling_async(news_list))
            
            # 强制更新数据库（覆盖现有数据）
            success_count, failure_count = force_update_news_labeling_results(results)
            logger.info(f"强制AI标签任务完成: 成功 {success_count} 条, 失败 {failure_count} 条")
            return success_count, failure_count
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"强制标签任务执行失败: {e}")
        logger.error(traceback.format_exc())
        return 0, 0

def force_update_news_analysis_results(results):
    """强制更新新闻分析结果到数据库（覆盖现有数据）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    success_count = 0
    failure_count = 0
    
    try:
        for result in results:
            try:
                # 自动分类消息标签
                message_label = auto_classify_message_label(result['analysis'])
                
                # 强制更新，不管原来有没有数据
                cursor.execute("""
                    UPDATE news_red_telegraph 
                    SET ai_analysis = %s, message_label = %s, updated_at = NOW()
                    WHERE id = %s
                """, (result['analysis'], message_label, result['id']))
                
                if result['success']:
                    success_count += 1
                    logger.info(f"强制更新分析结果 - 新闻ID {result['id']} 标记为: {message_label}")
                else:
                    failure_count += 1
                    
            except Exception as e:
                logger.error(f"强制更新新闻分析结果失败 - ID: {result['id']}, 错误: {e}")
                failure_count += 1
        
        conn.commit()
        logger.info(f"强制批量更新分析完成: 成功 {success_count} 条, 失败 {failure_count} 条")
        return success_count, failure_count
        
    except Exception as e:
        logger.error(f"强制批量更新新闻分析结果失败: {e}")
        conn.rollback()
        return 0, len(results)
    finally:
        cursor.close()
        conn.close()

def force_update_news_scoring_results(results):
    """强制更新新闻评分结果到数据库（覆盖现有数据）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    success_count = 0
    failure_count = 0
    
    try:
        for result in results:
            try:
                # 强制更新，不管原来有没有数据
                cursor.execute("""
                    UPDATE news_red_telegraph 
                    SET message_score = %s, message_score_rationale = %s, updated_at = NOW()
                    WHERE id = %s
                """, (result['message_score'], result['message_score_rationale'], result['id']))
                
                if result['success']:
                    success_count += 1
                    logger.info(f"强制更新评分结果 - 新闻ID {result['id']} 评分: {result['message_score']}")
                else:
                    failure_count += 1
                    
            except Exception as e:
                logger.error(f"强制更新新闻评分结果失败 - ID: {result['id']}, 错误: {e}")
                failure_count += 1
        
        conn.commit()
        logger.info(f"强制批量更新评分完成: 成功 {success_count} 条, 失败 {failure_count} 条")
        return success_count, failure_count
        
    except Exception as e:
        logger.error(f"强制批量更新新闻评分结果失败: {e}")
        conn.rollback()
        return 0, len(results)
    finally:
        cursor.close()
        conn.close()

def force_update_news_labeling_results(results):
    """强制更新新闻标签结果到数据库（覆盖现有数据）"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    success_count = 0
    failure_count = 0
    
    try:
        for result in results:
            try:
                # 强制更新，不管原来有没有数据
                cursor.execute("""
                    UPDATE news_red_telegraph 
                    SET message_type = %s, message_type_rationale = %s, updated_at = NOW()
                    WHERE id = %s
                """, (result['message_type'], result['message_type_rationale'], result['id']))
                
                if result['success']:
                    success_count += 1
                    logger.info(f"强制更新标签结果 - 新闻ID {result['id']} 标签: {result['message_type']}")
                else:
                    failure_count += 1
                    
            except Exception as e:
                logger.error(f"强制更新新闻标签结果失败 - ID: {result['id']}, 错误: {e}")
                failure_count += 1
        
        conn.commit()
        logger.info(f"强制批量更新标签完成: 成功 {success_count} 条, 失败 {failure_count} 条")
        return success_count, failure_count
        
    except Exception as e:
        logger.error(f"强制批量更新新闻标签结果失败: {e}")
        conn.rollback()
        return 0, len(results)
    finally:
        cursor.close()
        conn.close()

# ==================== 主程序入口 ====================

def main():
    """主函数"""
    logger.info("=== 财联社新闻爬虫启动 ===")
    
    # 检查并更新数据库字段结构
    try:
        check_and_update_database_schema()
    except Exception as e:
        logger.error(f"数据库字段检查失败，程序无法继续: {e}")
        sys.exit(1)
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "crawl":
            # 只爬取新闻
            logger.info("执行新闻爬取任务")
            new_count, duplicate_count, total_count = crawl_cls_news()
            logger.info(f"爬取完成: 总获取 {total_count} 条, 新增 {new_count} 条, 重复 {duplicate_count} 条")
            
        elif command == "analyze":
            # 只分析新闻
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            logger.info(f"执行AI分析任务，分析数量: {count}")
            success_count, failure_count = analyze_latest_news(count)
            logger.info(f"分析完成: 成功 {success_count} 条, 失败 {failure_count} 条")
            
        elif command == "score":
            # 只评分新闻
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            logger.info(f"执行AI评分任务，评分数量: {count}")
            success_count, failure_count = analyze_news_scoring(count)
            logger.info(f"评分完成: 成功 {success_count} 条, 失败 {failure_count} 条")
            
        elif command == "label":
            # 只标签新闻
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            logger.info(f"执行AI标签任务，标签数量: {count}")
            success_count, failure_count = analyze_news_labeling(count)
            logger.info(f"标签完成: 成功 {success_count} 条, 失败 {failure_count} 条")
            
        elif command == "complete":
            # 完整AI处理：分析 + 评分 + 标签
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            logger.info(f"执行完整AI处理任务，处理数量: {count}")
            
            # 1. 软硬分析
            success1, failure1 = analyze_latest_news(count)
            logger.info(f"软硬分析完成: 成功 {success1} 条, 失败 {failure1} 条")
            
            # 2. 评分
            success2, failure2 = analyze_news_scoring(count)
            logger.info(f"评分完成: 成功 {success2} 条, 失败 {failure2} 条")
            
            # 3. 标签
            success3, failure3 = analyze_news_labeling(count)
            logger.info(f"标签完成: 成功 {success3} 条, 失败 {failure3} 条")
            
            logger.info(f"完整AI处理任务完成: 分析成功{success1}条, 评分成功{success2}条, 标签成功{success3}条")
            
        elif command == "full":
            # 完整流程：爬取 + 完整AI处理
            logger.info("执行完整流程：爬取 + 完整AI处理")
            
            # 1. 爬取新闻
            new_count, duplicate_count, total_count = crawl_cls_news()
            logger.info(f"爬取完成: 总获取 {total_count} 条, 新增 {new_count} 条, 重复 {duplicate_count} 条")
            
            # 2. 完整AI处理（如果有新增的）
            if new_count > 0:
                logger.info(f"开始完整AI处理新增的 {new_count} 条新闻")
                
                # 2.1 软硬分析
                success1, failure1 = analyze_latest_news(new_count)
                logger.info(f"软硬分析完成: 成功 {success1} 条, 失败 {failure1} 条")
                
                # 2.2 评分
                success2, failure2 = analyze_news_scoring(new_count)
                logger.info(f"评分完成: 成功 {success2} 条, 失败 {failure2} 条")
                
                # 2.3 标签
                success3, failure3 = analyze_news_labeling(new_count)
                logger.info(f"标签完成: 成功 {success3} 条, 失败 {failure3} 条")
                
                logger.info(f"完整AI处理完成: 分析成功{success1}条, 评分成功{success2}条, 标签成功{success3}条")
            else:
                logger.info("没有新增新闻，跳过AI处理")
                
        elif command == "force-analyze":
            # 强制分析指定ID的新闻
            id_file = sys.argv[2] if len(sys.argv) > 2 else "force_process_ids.txt"
            logger.info(f"执行强制AI分析任务，ID文件: {id_file}")
            news_ids = load_force_process_ids(id_file)
            if news_ids:
                success_count, failure_count = force_analyze_news_by_ids(news_ids)
                logger.info(f"强制分析完成: 成功 {success_count} 条, 失败 {failure_count} 条")
            else:
                logger.warning("没有找到需要强制处理的ID")
                
        elif command == "force-score":
            # 强制评分指定ID的新闻
            id_file = sys.argv[2] if len(sys.argv) > 2 else "force_process_ids.txt"
            logger.info(f"执行强制AI评分任务，ID文件: {id_file}")
            news_ids = load_force_process_ids(id_file)
            if news_ids:
                success_count, failure_count = force_analyze_news_scoring_by_ids(news_ids)
                logger.info(f"强制评分完成: 成功 {success_count} 条, 失败 {failure_count} 条")
            else:
                logger.warning("没有找到需要强制处理的ID")
                
        elif command == "force-label":
            # 强制标签指定ID的新闻
            id_file = sys.argv[2] if len(sys.argv) > 2 else "force_process_ids.txt"
            logger.info(f"执行强制AI标签任务，ID文件: {id_file}")
            news_ids = load_force_process_ids(id_file)
            if news_ids:
                success_count, failure_count = force_analyze_news_labeling_by_ids(news_ids)
                logger.info(f"强制标签完成: 成功 {success_count} 条, 失败 {failure_count} 条")
            else:
                logger.warning("没有找到需要强制处理的ID")
                
        elif command == "force-complete":
            # 强制完整AI处理指定ID的新闻：分析 + 评分 + 标签
            id_file = sys.argv[2] if len(sys.argv) > 2 else "force_process_ids.txt"
            logger.info(f"执行强制完整AI处理任务，ID文件: {id_file}")
            news_ids = load_force_process_ids(id_file)
            if news_ids:
                # 1. 强制软硬分析
                success1, failure1 = force_analyze_news_by_ids(news_ids)
                logger.info(f"强制软硬分析完成: 成功 {success1} 条, 失败 {failure1} 条")
                
                # 2. 强制评分
                success2, failure2 = force_analyze_news_scoring_by_ids(news_ids)
                logger.info(f"强制评分完成: 成功 {success2} 条, 失败 {failure2} 条")
                
                # 3. 强制标签
                success3, failure3 = force_analyze_news_labeling_by_ids(news_ids)
                logger.info(f"强制标签完成: 成功 {success3} 条, 失败 {failure3} 条")
                
                logger.info(f"强制完整AI处理完成: 分析成功{success1}条, 评分成功{success2}条, 标签成功{success3}条")
            else:
                logger.warning("没有找到需要强制处理的ID")
                
        elif command == "schedule":
            # 调度模式：运行10天，每2小时执行一次
            logger.info("启动调度模式：10天，每2小时执行一次完整流程")
            from scheduler import NewsScheduler
            scheduler = NewsScheduler()
            scheduler.run()
            
        else:
            print("使用方法:")
            print("  python main.py crawl                    - 只爬取新闻")
            print("  python main.py analyze [数量]           - 只AI软硬分析最新未分析的新闻")
            print("  python main.py score [数量]             - 只AI评分最新未评分的新闻")
            print("  python main.py label [数量]             - 只AI标签最新未标签的新闻") 
            print("  python main.py complete [数量]          - 完整AI处理：分析+评分+标签")
            print("  python main.py full                    - 完整流程：爬取+完整AI处理")
            print("  python main.py schedule                - 调度模式：10天，每2小时执行一次")
            print("")
            print("强制处理模式（覆盖现有数据）:")
            print("  python main.py force-analyze [ID文件]   - 强制分析指定ID的新闻")
            print("  python main.py force-score [ID文件]     - 强制评分指定ID的新闻")
            print("  python main.py force-label [ID文件]     - 强制标签指定ID的新闻")
            print("  python main.py force-complete [ID文件]  - 强制完整AI处理指定ID的新闻")
            print("")
            print("ID文件格式: 每行一个新闻ID，默认使用 force_process_ids.txt")
            sys.exit(1)
    else:
        # 默认执行完整流程
        logger.info("执行默认完整流程：爬取 + 完整AI处理")
        
        # 1. 爬取新闻
        new_count, duplicate_count, total_count = crawl_cls_news()
        logger.info(f"爬取完成: 总获取 {total_count} 条, 新增 {new_count} 条, 重复 {duplicate_count} 条")
        
        # 2. 完整AI处理（如果有新增的）
        if new_count > 0:
            logger.info(f"开始完整AI处理新增的 {new_count} 条新闻")
            
            # 2.1 软硬分析
            success1, failure1 = analyze_latest_news(new_count)
            logger.info(f"软硬分析完成: 成功 {success1} 条, 失败 {failure1} 条")
            
            # 2.2 评分
            success2, failure2 = analyze_news_scoring(new_count)
            logger.info(f"评分完成: 成功 {success2} 条, 失败 {failure2} 条")
            
            # 2.3 标签
            success3, failure3 = analyze_news_labeling(new_count)
            logger.info(f"标签完成: 成功 {success3} 条, 失败 {failure3} 条")
            
            logger.info(f"完整AI处理完成: 分析成功{success1}条, 评分成功{success2}条, 标签成功{success3}条")
        else:
            logger.info("没有新增新闻，跳过AI处理")
    
    logger.info("=== 任务完成 ===")

if __name__ == '__main__':
    main()