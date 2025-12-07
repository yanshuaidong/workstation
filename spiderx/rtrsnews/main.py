#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Reuters 路透社新闻自动处理服务

功能说明：
1. 接收浏览器扩展发送的新闻数据（Flask API）
2. 实时存储到本地SQLite数据库 reuters_news 表
3. 定时处理新闻（每天5/11/17/23点，与彭博社错开1小时）
4. AI筛选期货相关新闻并格式化输出
5. 保存到MySQL数据库 news_red_telegraph 和 news_process_tracking 表
6. 保存到本地SQLite数据库 analysis_task 表
7. 删除已处理的新闻数据

工作流程：
插件发送 -> reuters_news表 -> 定时触发 -> AI筛选 -> MySQL保存 -> analysis_task表 -> 删除已处理数据
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
        logging.FileHandler('reuters_service.log', encoding='utf-8'),
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

# Reuters URL前缀
REUTERS_URL_PREFIX = "https://www.reuters.com"

# 服务端口
SERVICE_PORT = 1125

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
    保存新闻到 reuters_news 表（带去重）
    
    参数：
        news_item: 新闻数据字典，包含 published_time, title, url
    
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
            url = REUTERS_URL_PREFIX + url
        
        # 解析发布时间
        published_time = news_item.get('published_time') or ''
        
        # 使用 INSERT OR IGNORE 实现去重（基于 published_time 唯一索引）
        insert_sql = """
            INSERT OR IGNORE INTO reuters_news 
            (published_time, title, url, status)
            VALUES (?, ?, ?, 0)
        """
        cursor.execute(insert_sql, (
            published_time,
            news_item.get('title', ''),
            url
        ))
        
        conn.commit()
        
        # rowcount > 0 表示插入成功，= 0 表示重复数据被忽略
        return cursor.rowcount > 0
        
    except Exception as e:
        logger.error(f"❌ 保存新闻到数据库失败: {e}")
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
            SELECT id, published_time, title, url
            FROM reuters_news
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
        logger.error(f"❌ 获取待处理新闻失败: {e}")
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
            UPDATE reuters_news 
            SET status = 1, updated_at = CURRENT_TIMESTAMP
            WHERE id IN ({placeholders})
        """
        cursor.execute(update_sql, news_ids)
        conn.commit()
        
        logger.info(f"✅ 已标记 {len(news_ids)} 条新闻为已处理")
        
    except Exception as e:
        logger.error(f"❌ 标记新闻状态失败: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()


def delete_processed_news():
    """
    删除已处理的新闻（status=1）
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 先统计要删除的数量
        cursor.execute("SELECT COUNT(*) FROM reuters_news WHERE status = 1")
        count = cursor.fetchone()[0]
        
        if count == 0:
            logger.info("ℹ️ 没有需要删除的已处理新闻")
            return
        
        # 删除已处理的新闻
        delete_sql = "DELETE FROM reuters_news WHERE status = 1"
        cursor.execute(delete_sql)
        conn.commit()
        
        logger.info(f"🗑️ 已删除 {count} 条已处理新闻")
        
    except Exception as e:
        logger.error(f"❌ 删除已处理新闻失败: {e}")
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
        
        logger.info(f"✅ 分析任务保存成功 - 任务ID: {task_id}")
        return task_id
        
    except Exception as e:
        logger.error(f"❌ 保存分析任务失败: {e}")
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
        cursor.execute("SELECT COUNT(*) FROM reuters_news WHERE status = 0")
        return cursor.fetchone()[0]
    except Exception as e:
        logger.error(f"❌ 获取待处理新闻数量失败: {e}")
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
        title: 标题，如【路透社2025年11月1日23点到5点新闻】
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
            '路透社新闻'             # message_type: 路透社新闻
        ))
        
        news_id = cursor.lastrowid
        
        # 如果是更新操作，lastrowid 为 0，需要查询获取实际 ID
        if news_id == 0:
            cursor.execute("SELECT id FROM news_red_telegraph WHERE ctime = %s", (news_timestamp,))
            result = cursor.fetchone()
            if result:
                news_id = result[0]
                logger.info(f"✅ MySQL news_red_telegraph 更新成功 - ID: {news_id}")
            else:
                logger.warning("⚠️ 无法获取 news_id")
                conn.commit()
                return None
        else:
            logger.info(f"✅ MySQL news_red_telegraph 保存成功 - ID: {news_id}")
        
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
        
        if cursor.rowcount > 0:
            tracking_id = cursor.lastrowid
            logger.info(f"✅ MySQL news_process_tracking 保存成功 - ID: {tracking_id}")
        else:
            logger.info(f"ℹ️ MySQL news_process_tracking 已存在，跳过插入")
        
        conn.commit()
        return news_id
        
    except Exception as e:
        logger.error(f"❌ 保存到MySQL失败: {e}")
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
        news_list: 新闻列表，每条包含 title, url
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
            logger.info(f"🤖 调用AI接口 (第{attempt + 1}次尝试，超时{timeout}秒)...")
            
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
            logger.info(f"✅ AI接口调用成功 (第{attempt + 1}次尝试)")
            return result
            
        except Exception as e:
            logger.error(f"❌ AI接口调用失败 (第{attempt + 1}次尝试): {e}")
            if attempt == max_retries - 1:
                logger.error("❌ AI接口调用最终失败，已用尽所有重试次数")
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
请根据以上新闻信息，进行深度分析并给出可操作的交易建议：

【分析要求】
1. 市场影响分析：
   - 分析每条新闻对相关期货品种的潜在影响方向（利多/利空）
   - 评估影响的时效性（短期/中期）和强度（强/中/弱）

2. 交易机会识别：
   - 明确指出可能存在的交易机会
   - 给出建议的交易方向（做多/做空）
   - 说明入场时机和注意事项

3. 风险提示：
   - 指出可能的风险因素
   - 给出止损建议或观察要点

4. 关联性分析：
   - 分析不同品种之间的联动关系
   - 指出可能的套利或对冲机会

【输出格式】
请按品种分类输出分析结果，每个品种包含：影响分析、交易建议、风险提示。
"""
    
    return f"{ai_result}\n\n{analysis_instruction}"


def process_news_task():
    """
    定时任务：处理新闻
    在 5/11/17/23 点执行（与彭博社的6/12/18/0错开1小时）
    """
    now = datetime.now()
    current_hour = now.hour
    
    # 确定时间标签（用于标题显示）
    if current_hour == 5:
        time_label = "23点到5点"
    elif current_hour == 11:
        time_label = "5点到11点"
    elif current_hour == 17:
        time_label = "11点到17点"
    elif current_hour == 23:
        time_label = "17点到23点"
    else:
        logger.warning(f"⚠️ 非预期的执行时间: {current_hour}点")
        return
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🕐 开始处理 {now.strftime('%Y年%m月%d日')} {time_label} 的新闻")
    logger.info(f"{'='*60}")
    
    # 计算时间范围：获取过去24小时内未处理的新闻
    end_time = now
    start_time = now - timedelta(hours=24)
    
    # 从数据库获取待处理新闻
    target_news = get_pending_news(start_time, end_time)
    
    logger.info(f"📊 找到 {len(target_news)} 条待处理新闻")
    
    if len(target_news) == 0:
        logger.info("ℹ️ 没有需要处理的新闻")
        logger.info(f"{'='*60}\n")
        return
    
    # 获取新闻ID列表，用于后续标记
    news_ids = [item['id'] for item in target_news]
    
    # 准备发送给AI的新闻列表
    news_for_ai = [
        {
            'published_time': item.get('published_time'),
            'title': item.get('title'),
            'url': item.get('url', '')
        }
        for item in target_news
    ]
    
    # 调用AI接口筛选
    ai_result = call_ai_api(news_for_ai)
    
    if ai_result is None:
        logger.error("❌ AI筛选失败，本次任务终止")
        logger.info(f"{'='*60}\n")
        return
    
    # 构建标题
    date_str = now.strftime('%Y年%m月%d日')
    title = f"【路透社{date_str}{time_label}新闻】"
    
    # AI筛选结果
    ai_result_stripped = ai_result.strip()
    
    # 使用当前执行时间的时间戳（秒），确保每次执行都是唯一的
    news_timestamp = int(now.timestamp())
    
    logger.info(f"📝 标题: {title}")
    logger.info(f"📄 AI筛选结果预览: {ai_result_stripped[:200]}...")
    
    # ========== 保存到MySQL（即使"无重要相关新闻"也要保存） ==========
    mysql_news_id = save_to_mysql(title, ai_result_stripped, news_timestamp)
    if mysql_news_id:
        logger.info(f"✅ MySQL保存成功 - news_id: {mysql_news_id}")
    else:
        logger.warning("⚠️ MySQL保存失败，继续执行后续流程")
    
    # 检查是否无重要新闻
    if "无重要相关新闻" in ai_result_stripped:
        logger.info("ℹ️ AI筛选结果：无重要相关新闻，跳过analysis_task入库")
        # 仍然标记新闻为已处理并删除
        mark_news_as_processed(news_ids)
        delete_processed_news()
        logger.info("✅ 新闻已标记处理完成（无需创建分析任务）")
        logger.info(f"{'='*60}\n")
        return
    
    # 构建完整的分析提示词
    prompt = build_analysis_prompt(ai_result_stripped)
    
    # 保存到 analysis_task 表
    task_id = save_analysis_task(title, prompt, start_time)
    
    if task_id:
        # 标记新闻为已处理
        mark_news_as_processed(news_ids)
        
        # 删除已处理的新闻
        delete_processed_news()
        
        logger.info("✅ 新闻处理完成")
    else:
        logger.error("❌ 分析任务保存失败，不删除新闻数据")
    
    logger.info(f"{'='*60}\n")


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
        
        # 调试：打印第一条数据查看结构
        if captured_data:
            logger.info(f"🔍 调试 - 第一条原始数据: {captured_data[0]}")
        
        if not captured_data:
            return jsonify({
                'success': False,
                'message': '数据列表为空'
            }), 400
        
        # 添加新闻到数据库
        added_count = 0
        for item in captured_data:
            news_item = {
                'published_time': item.get('published_time'),
                'title': item.get('title'),
                'url': item.get('url') or ''  # 使用 or 处理 None 值
            }
            
            if save_news_to_db(news_item):
                added_count += 1
        
        # 获取当前待处理总数
        total_count = get_pending_news_count()
        
        logger.info(f'✅ 新闻接收成功 - 新增: {added_count} 条 | 待处理总计: {total_count} 条')
        
        return jsonify({
            'success': True,
            'message': '数据保存成功',
            'added': added_count,
            'total': total_count
        }), 200
        
    except Exception as e:
        logger.error(f'❌ 数据接收失败: {e}')
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
        'service': 'Reuters路透社新闻处理服务',
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
        cursor.execute("SELECT COUNT(*) FROM reuters_news WHERE status = 0")
        pending = cursor.fetchone()[0]
        
        # 已处理新闻数量
        cursor.execute("SELECT COUNT(*) FROM reuters_news WHERE status = 1")
        processed = cursor.fetchone()[0]
        
        # 分析任务数量
        cursor.execute("SELECT COUNT(*) FROM analysis_task")
        tasks = cursor.fetchone()[0]
        
        # 待分析任务数量
        cursor.execute("SELECT COUNT(*) FROM analysis_task WHERE is_analyzed = 0")
        pending_tasks = cursor.fetchone()[0]
        
        return jsonify({
            'reuters_news': {
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
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🧪 [测试模式] 开始处理所有待处理新闻")
    logger.info(f"{'='*60}")
    
    # 获取所有待处理的新闻（不限时间范围）
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        select_sql = """
            SELECT id, published_time, title, url
            FROM reuters_news
            WHERE status = 0
            ORDER BY created_at ASC
        """
        cursor.execute(select_sql)
        rows = cursor.fetchall()
        target_news = [dict(row) for row in rows]
        
    except Exception as e:
        logger.error(f"❌ 获取待处理新闻失败: {e}")
        return {'success': False, 'message': f'获取新闻失败: {str(e)}', 'processed': 0}
    finally:
        if conn:
            conn.close()
    
    logger.info(f"📊 找到 {len(target_news)} 条待处理新闻")
    
    if len(target_news) == 0:
        logger.info("ℹ️ 没有需要处理的新闻")
        logger.info(f"{'='*60}\n")
        return {'success': True, 'message': '没有需要处理的新闻', 'processed': 0}
    
    # 获取新闻ID列表
    news_ids = [item['id'] for item in target_news]
    
    # 准备发送给AI的新闻列表
    news_for_ai = [
        {
            'published_time': item.get('published_time'),
            'title': item.get('title'),
            'url': item.get('url', '')
        }
        for item in target_news
    ]
    
    # 调用AI接口筛选
    ai_result = call_ai_api(news_for_ai)
    
    if ai_result is None:
        logger.error("❌ AI筛选失败，本次任务终止")
        logger.info(f"{'='*60}\n")
        return {'success': False, 'message': 'AI筛选失败', 'processed': 0}
    
    # 构建标题（测试模式）
    date_str = now.strftime('%Y年%m月%d日')
    time_str = now.strftime('%H:%M')
    title = f"【路透社{date_str} {time_str} 测试】"
    
    # AI筛选结果
    ai_result_stripped = ai_result.strip()
    
    # 计算新闻时间戳（测试模式使用当前时间）
    news_timestamp = int(now.timestamp())
    
    logger.info(f"📝 标题: {title}")
    logger.info(f"📄 AI筛选结果预览: {ai_result_stripped[:200]}...")
    
    # ========== 保存到MySQL（即使"无重要相关新闻"也要保存） ==========
    mysql_news_id = save_to_mysql(title, ai_result_stripped, news_timestamp)
    if mysql_news_id:
        logger.info(f"✅ MySQL保存成功 - news_id: {mysql_news_id}")
    else:
        logger.warning("⚠️ MySQL保存失败，继续执行后续流程")
    
    # 检查是否无重要新闻
    if "无重要相关新闻" in ai_result_stripped:
        logger.info("ℹ️ AI筛选结果：无重要相关新闻，跳过analysis_task入库")
        # 仍然标记新闻为已处理并删除
        mark_news_as_processed(news_ids)
        delete_processed_news()
        logger.info("✅ 测试处理完成（无重要新闻，未创建分析任务）")
        logger.info(f"{'='*60}\n")
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
    task_id = save_analysis_task(title, prompt, now)
    
    if task_id:
        # 标记新闻为已处理
        mark_news_as_processed(news_ids)
        
        # 删除已处理的新闻
        delete_processed_news()
        
        logger.info("✅ 测试处理完成")
        logger.info(f"{'='*60}\n")
        return {
            'success': True, 
            'message': f'处理完成，已创建分析任务 ID: {task_id}', 
            'processed': len(news_ids),
            'task_id': task_id,
            'mysql_news_id': mysql_news_id
        }
    else:
        logger.error("❌ 分析任务保存失败")
        logger.info(f"{'='*60}\n")
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
        logger.error(f"❌ 测试处理失败: {e}")
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
    logger.info(f"收到信号 {signal_name}，准备优雅退出...")
    print(f"\n🛑 收到停止信号 {signal_name}，正在安全停止服务...")
    
    shutdown_flag = True
    
    # 停止调度器
    if scheduler:
        logger.info("正在停止定时任务调度器...")
        scheduler.shutdown(wait=False)
        logger.info("定时任务调度器已停止")
    
    logger.info("服务已安全停止")
    sys.exit(0)


if __name__ == '__main__':
    logger.info('='*60)
    logger.info('🚀 Reuters路透社新闻处理服务启动')
    logger.info(f'📍 监听端口: {SERVICE_PORT}')
    logger.info(f'💾 数据库路径: {DB_PATH.absolute()}')
    logger.info(f'🔗 接收接口: http://localhost:{SERVICE_PORT}/api/capture')
    logger.info(f'💚 健康检查: http://localhost:{SERVICE_PORT}/api/health')
    logger.info(f'📊 统计信息: http://localhost:{SERVICE_PORT}/api/stats')
    logger.info('='*60)
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # kill命令
    logger.info("✅ 信号处理器已注册")
    
    # 启动定时任务调度器
    scheduler = BackgroundScheduler()
    
    # 添加定时任务：每天的 5、11、17、23 点执行（与彭博社错开1小时）
    scheduler.add_job(process_news_task, 'cron', hour='5,11,17,23', minute=0)
    
    scheduler.start()
    logger.info('⏰ 定时任务已启动 (每天5点、11点、17点、23点执行)')
    
    # 打印下次执行时间
    jobs = scheduler.get_jobs()
    if jobs:
        next_run_time = jobs[0].next_run_time
        logger.info(f'📅 下次执行时间: {next_run_time.strftime("%Y-%m-%d %H:%M:%S")}')
    
    try:
        # 启动Flask服务
        app.run(host='0.0.0.0', port=SERVICE_PORT, debug=False, use_reloader=False)
    except (KeyboardInterrupt, SystemExit):
        if scheduler:
            scheduler.shutdown()
        logger.info('👋 服务已停止')
