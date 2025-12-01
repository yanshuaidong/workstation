#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bloomberg 新闻自动处理服务

功能说明：
1. 接收浏览器扩展发送的新闻数据（Flask API）
2. 定时处理新闻（每天6/12/18/24点）
3. AI筛选相关新闻并翻译成中文
4. 保存到MySQL数据库两个表
5. 自动删除已处理的本地数据

工作流程：
插件发送 -> 本地存储 -> 定时触发 -> AI筛选 -> 数据库保存 -> 删除本地数据
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from apscheduler.schedulers.background import BackgroundScheduler
import json
import os
import time
import pymysql
import requests
import signal
import sys
from datetime import datetime, timedelta
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

# 数据文件配置
DATA_DIR = 'captured_data'
DATA_FILE = os.path.join(DATA_DIR, 'bloomberg_news.json')

# AI API 配置（写死在代码里）
AI_API_KEY = "sk-qVU4OZNspU5cSTPONFBFD000t2Oy8Tq9U8h74Wm5Phnl8tsB"
AI_BASE_URL = "https://poloai.top/v1/chat/completions"

# 数据库配置（写死在代码里）
DB_CONFIG = {
    'host': 'rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'ysd',
    'password': 'Yan1234567',
    'database': 'futures',
    'charset': 'utf8mb4'
}

# 服务端口
SERVICE_PORT = 1123

# 确保数据目录存在
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# ==================== 数据库操作 ====================

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def save_to_database(title, content, ctime):
    """
    保存新闻到数据库两个表
    
    参数：
        title: 新闻标题
        content: AI筛选后的内容
        ctime: 新闻发生时间的时间戳（秒）
    
    返回：
        bool: 是否成功
    """
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. 插入新闻表 news_red_telegraph
        insert_news_sql = """
            INSERT INTO news_red_telegraph 
            (ctime, title, content, ai_analysis, message_score, message_label, message_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_news_sql, (
            ctime,
            title,
            content,
            '暂无分析',
            6,
            'hard',
            '彭博社新闻'
        ))
        
        # 获取插入的新闻ID
        news_id = cursor.lastrowid
        
        # 2. 插入跟踪表 news_process_tracking（使用默认值）
        insert_tracking_sql = """
            INSERT INTO news_process_tracking (news_id, ctime)
            VALUES (%s, %s)
        """
        cursor.execute(insert_tracking_sql, (news_id, ctime))
        
        conn.commit()
        logger.info(f"✅ 数据库保存成功 - 新闻ID: {news_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 数据库保存失败: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            cursor.close()
            conn.close()

# ==================== AI接口调用 ====================

def call_ai_api(news_list, max_retries=2):
    """
    调用AI接口筛选新闻（带重试机制）
    
    参数：
        news_list: 新闻列表
        max_retries: 最大重试次数（默认2次）
    
    返回：
        str or None: AI返回的筛选结果，失败返回None
    """
    # 构建提示词
    news_json = json.dumps(news_list, ensure_ascii=False, indent=2)
    
    system_message = """你是一个专业的金融新闻筛选和翻译助手，服务于量化交易系统。

【核心目标】
从给定的新闻列表中，只保留那些对期货或股票市场价格在短期内“可能产生明显影响”的新闻，并翻译成中文标题。

【筛选原则（非常严格，宁可少选也不要多选）】

一、应当保留的新闻（满足任意一条即可）：
1. 与以下内容直接相关，且可能在短期内引发价格波动：
   - 股指、主要成分股、期货合约（股指期货、股指成分、商品期货、外汇期货等）
   - 央行决议、利率变动、意外的货币政策信号
   - 重要宏观数据“明显超预期或不及预期”（如GDP、CPI、非农、PMI等）
   - 大宗商品供给或需求的重大变化（减产、禁运、重大采购/取消采购、库存异常等）
   - 评级机构对国家或大型企业的“评级上调/下调/展望调整”
   - 汇率出现“历史新高/新低”或监管出台新外汇管制、干预政策
   - 企业的重大利好/利空事件：
     · 大额盈利预警或盈利暴雷
     · 明确导致股价或债券价格“暴涨/暴跌”的消息
     · 巨额融资、巨额回购、巨额减持
     · 重大监管处罚、违约、重组、破产等

二、通常应当剔除或忽略的新闻（除非文本中已经说明引发价格大幅波动）：
1. 普通的并购、投资、扩产、合作、开新工厂/新门店、扩张计划等“公司经营类动态”，金额不大的
2. 私募股权、对冲基金、新基金成立、管理人变动等“资产管理人新闻”
3. 一般性的企业 ESG、社会责任、慈善、品牌宣传活动
4. 高管任命、辞职等公司治理类新闻（除非引发股价大幅波动）
5. 中小规模的区域经济项目、普通基础设施项目
6. 任何“相关性较弱、没有明显价格触发点”的新闻

三、判断标准：
- 你需要站在“短期金融市场交易”的角度判断一条新闻是否会对期货或股票价格产生实质影响。
- 如果不确定一条新闻是否足够重要，应当“宁可不选”，不要勉强保留。
- 如果全部新闻都只存在非常间接或微弱的关联，应输出：无重要相关新闻

【输出要求】
1. 对筛选后保留的新闻标题翻译为自然、简洁的中文。
2. 输出格式（严格按照此格式）：
1、[中文翻译的新闻标题1]
2、[中文翻译的新闻标题2]
3、[中文翻译的新闻标题3]
...
3. 如果没有符合条件的新闻，输出：无重要相关新闻
4. 只输出结果列表，不要添加任何额外的解释或分析。"""

    user_message = f"""请从以下新闻中筛选出对期货或股票市场价格在短期内可能产生明显影响的内容，并按要求翻译成中文输出：

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

# ==================== 数据文件操作 ====================

def load_news_data():
    """加载本地新闻数据"""
    if not os.path.exists(DATA_FILE):
        return []
    
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        logger.error(f"❌ 加载数据文件失败: {e}")
        return []

def save_news_data(news_list):
    """保存新闻数据到本地文件"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(news_list, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"❌ 保存数据文件失败: {e}")
        return False

def add_news_item(news_item):
    """添加新闻条目（带去重）"""
    news_list = load_news_data()
    
    # 去重：根据 publishedAt 判断
    existing_times = {item.get('publishedAt') for item in news_list}
    
    if news_item.get('publishedAt') not in existing_times:
        news_list.append(news_item)
        save_news_data(news_list)
        return True
    return False

def delete_news_in_timerange(start_time, end_time):
    """
    删除指定时间范围内的新闻
    
    参数：
        start_time: 开始时间（datetime对象）
        end_time: 结束时间（datetime对象）
    """
    news_list = load_news_data()
    original_count = len(news_list)
    
    # 过滤掉时间范围内的新闻
    filtered_list = []
    for item in news_list:
        local_time_str = item.get('localReceivedTime', '')
        if local_time_str:
            try:
                local_time = datetime.fromisoformat(local_time_str)
                # 保留不在删除范围内的新闻
                if not (start_time <= local_time < end_time):
                    filtered_list.append(item)
            except:
                # 如果时间解析失败，保留该条新闻
                filtered_list.append(item)
        else:
            # 没有本地时间的新闻也保留
            filtered_list.append(item)
    
    deleted_count = original_count - len(filtered_list)
    save_news_data(filtered_list)
    logger.info(f"🗑️ 删除了 {deleted_count} 条新闻 (原有{original_count}条，剩余{len(filtered_list)}条)")

# ==================== 定时任务 ====================

def process_news_task():
    """
    定时任务：处理新闻
    在 6/12/18/24 点执行
    """
    now = datetime.now()
    current_hour = now.hour
    
    # 确定处理的时间段
    if current_hour == 6:
        start_hour, end_hour = 0, 6
        time_label = "0点到6点"
    elif current_hour == 12:
        start_hour, end_hour = 6, 12
        time_label = "6点到12点"
    elif current_hour == 18:
        start_hour, end_hour = 12, 18
        time_label = "12点到18点"
    elif current_hour == 0:
        start_hour, end_hour = 18, 24
        time_label = "18点到24点"
    else:
        logger.warning(f"⚠️ 非预期的执行时间: {current_hour}点")
        return
    
    logger.info(f"\n{'='*60}")
    logger.info(f"🕐 开始处理 {now.strftime('%Y年%m月%d日')} {time_label} 的新闻")
    logger.info(f"{'='*60}")
    
    # 计算时间范围
    start_time = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    if end_hour == 24:
        end_time = (start_time + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        end_time = now.replace(hour=end_hour, minute=0, second=0, microsecond=0)
    
    # 加载所有新闻
    all_news = load_news_data()
    
    # 筛选时间范围内的新闻
    target_news = []
    for item in all_news:
        local_time_str = item.get('localReceivedTime', '')
        if local_time_str:
            try:
                local_time = datetime.fromisoformat(local_time_str)
                if start_time <= local_time < end_time:
                    target_news.append(item)
            except Exception as e:
                logger.warning(f"⚠️ 时间解析失败: {e}")
    
    logger.info(f"📊 找到 {len(target_news)} 条待处理新闻")
    
    if len(target_news) == 0:
        logger.info("ℹ️ 没有需要处理的新闻")
        logger.info(f"{'='*60}\n")
        return
    
    # 准备发送给AI的新闻列表（只包含必要字段）
    news_for_ai = [
        {
            'publishedAt': item.get('publishedAt'),
            'headline': item.get('headline'),
            'brand': item.get('brand', '')
        }
        for item in target_news
    ]
    
    # 调用AI接口筛选
    ai_result = call_ai_api(news_for_ai)
    
    if ai_result is None:
        logger.error("❌ AI筛选失败，本次任务终止")
        logger.info(f"{'='*60}\n")
        return
    
    # 构建标题和内容
    date_str = now.strftime('%Y年%m月%d日')
    title = f"【彭博社{date_str}{time_label}新闻】"
    content = ai_result.strip()
    
    # 计算 ctime（使用时间段的开始时间作为新闻发生时间）
    ctime = int(start_time.timestamp())
    
    logger.info(f"📝 标题: {title}")
    logger.info(f"📄 内容预览: {content[:100]}...")
    
    # 保存到数据库
    success = save_to_database(title, content, ctime)
    
    if success:
        # 删除已处理的新闻
        delete_news_in_timerange(start_time, end_time)
        logger.info("✅ 新闻处理完成")
    else:
        logger.error("❌ 数据库保存失败，不删除本地数据")
    
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
        
        if not captured_data:
            return jsonify({
                'success': False,
                'message': '数据列表为空'
            }), 400
        
        # 当前本地时间
        local_time = datetime.now().isoformat()
        
        # 添加新闻到本地存储
        added_count = 0
        for item in captured_data:
            # 为每条新闻添加本地接收时间
            news_item = {
                'publishedAt': item.get('publishedAt'),
                'headline': item.get('headline'),
                'brand': item.get('brand', ''),
                'localReceivedTime': local_time  # 添加本地接收时间
            }
            
            if add_news_item(news_item):
                added_count += 1
        
        # 获取当前总数
        all_news = load_news_data()
        total_count = len(all_news)
        
        logger.info(f'✅ 新闻接收成功 - 新增: {added_count} 条 | 总计: {total_count} 条')
        
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
    news_list = load_news_data()
    return jsonify({
        'status': 'ok',
        'service': 'Bloomberg新闻处理服务',
        'port': 1123,
        'time': datetime.now().isoformat(),
        'pending_news': len(news_list)
    })

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    news_list = load_news_data()
    return jsonify({
        'total': len(news_list),
        'file': DATA_FILE
    })

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
    logger.info('🚀 Bloomberg新闻处理服务启动')
    logger.info(f'📍 监听端口: {SERVICE_PORT}')
    logger.info(f'💾 数据文件: {os.path.abspath(DATA_FILE)}')
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
    
    # 添加定时任务：每天的 6、12、18、0 点执行
    scheduler.add_job(process_news_task, 'cron', hour='6,12,18,0', minute=0)
    
    scheduler.start()
    logger.info('⏰ 定时任务已启动 (每天6点、12点、18点、24点执行)')
    
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
