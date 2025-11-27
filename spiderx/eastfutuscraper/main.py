import json
import time
import re
import requests
import os
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging
import pymysql
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 数据库配置
DB_CONFIG = {
    'host': 'rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'ysd',
    'password': 'Yan1234567',
    'database': 'futures',
    'charset': 'utf8mb4'
}

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def create_history_table(conn, symbol):
    """
    创建期货历史数据表（如果不存在）
    
    Args:
        conn: 数据库连接
        symbol: 期货品种代码（小写）
    """
    table_name = f"hist_{symbol}"
    cursor = conn.cursor()
    
    try:
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                trade_date DATE PRIMARY KEY COMMENT '交易日期',
                open_price DECIMAL(10,2) NOT NULL COMMENT '开盘价',
                high_price DECIMAL(10,2) NOT NULL COMMENT '最高价',
                low_price DECIMAL(10,2) NOT NULL COMMENT '最低价',
                close_price DECIMAL(10,2) NOT NULL COMMENT '收盘价',
                volume BIGINT NOT NULL DEFAULT 0 COMMENT '成交量',
                open_interest BIGINT NOT NULL DEFAULT 0 COMMENT '持仓量',
                turnover DECIMAL(20,2) NOT NULL DEFAULT 0 COMMENT '成交额',
                price_change DECIMAL(10,2) DEFAULT 0 COMMENT '涨跌',
                change_pct DECIMAL(10,2) DEFAULT 0.00 COMMENT '涨跌幅',
                macd_dif DECIMAL(10,4) NULL COMMENT 'MACD快线',
                macd_dea DECIMAL(10,4) NULL COMMENT 'MACD慢线',
                macd_histogram DECIMAL(10,4) NULL COMMENT 'MACD柱状图',
                rsi_14 DECIMAL(6,2) NULL COMMENT 'RSI(14)',
                kdj_k DECIMAL(6,2) NULL COMMENT 'KDJ-K值',
                kdj_d DECIMAL(6,2) NULL COMMENT 'KDJ-D值',
                kdj_j DECIMAL(6,2) NULL COMMENT 'KDJ-J值',
                bb_upper DECIMAL(10,2) NULL COMMENT '布林带上轨',
                bb_middle DECIMAL(10,2) NULL COMMENT '布林带中轨',
                bb_lower DECIMAL(10,2) NULL COMMENT '布林带下轨',
                bb_width DECIMAL(10,2) NULL COMMENT '布林带宽度',
                recommendation VARCHAR(20) NULL COMMENT '推荐操作：做多/做空/观察',
                source_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '数据源时间戳',
                ingest_ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '入库时间戳',
                INDEX idx_trade_date (trade_date)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='期货历史数据_{symbol}'
        """)
        conn.commit()
        logger.info(f"表 {table_name} 已确认存在")
    except Exception as e:
        logger.error(f"创建表 {table_name} 失败: {e}")
        conn.rollback()
    finally:
        cursor.close()

def safe_decimal(value, default=0):
    """
    安全地将值转换为浮点数，处理 '-'、None、空字符串等无效值
    
    Args:
        value: 待转换的值
        default: 无效值时的默认返回值
    
    Returns:
        float: 转换后的数值，如果无效则返回 default
    """
    if value is None:
        return default
    
    # 如果是字符串类型
    if isinstance(value, str):
        value = value.strip()
        # 处理 '-'、空字符串、'None' 等无效值
        if value == '' or value == '-' or value.lower() == 'none' or value.lower() == 'null':
            return default
        # 尝试转换为浮点数
        try:
            return float(value)
        except (ValueError, TypeError):
            return default
    
    # 如果是数字类型，直接返回
    if isinstance(value, (int, float)):
        return float(value)
    
    # 其他类型，尝试转换
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def insert_futures_data_to_db(conn, item, trade_date):
    """
    将单条期货数据插入数据库
    
    Args:
        conn: 数据库连接
        item: 期货数据字典
        trade_date: 交易日期（格式：YYYY-MM-DD）
    
    Returns:
        bool: 插入是否成功
    """
    try:
        # 获取代码并转换为小写
        symbol = item.get('dm', '').lower()
        if not symbol:
            logger.warning("数据缺少代码字段，跳过")
            return False
        
        # 确保表存在
        create_history_table(conn, symbol)
        
        table_name = f"hist_{symbol}"
        cursor = conn.cursor()
        
        # 字段映射，使用 safe_decimal 处理可能为 '-' 的值
        open_price = safe_decimal(item.get('o'), 0)  # 今开
        high_price = safe_decimal(item.get('h'), 0)  # 最高
        low_price = safe_decimal(item.get('l'), 0)   # 最低
        close_price = safe_decimal(item.get('p'), 0)  # 最新价（收盘价）
        volume = safe_decimal(item.get('vol'), 0)     # 成交量
        turnover = safe_decimal(item.get('cje'), 0)   # 成交额
        open_interest = safe_decimal(item.get('ccl'), 0)  # 持仓量
        price_change = safe_decimal(item.get('zde'), 0)   # 涨跌额
        change_pct = safe_decimal(item.get('zdf'), 0)     # 涨跌幅
        
        # 使用 INSERT ... ON DUPLICATE KEY UPDATE 实现覆盖逻辑
        sql = f"""
            INSERT INTO {table_name} 
            (trade_date, open_price, high_price, low_price, close_price, 
             volume, open_interest, turnover, price_change, change_pct)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                open_price = VALUES(open_price),
                high_price = VALUES(high_price),
                low_price = VALUES(low_price),
                close_price = VALUES(close_price),
                volume = VALUES(volume),
                open_interest = VALUES(open_interest),
                turnover = VALUES(turnover),
                price_change = VALUES(price_change),
                change_pct = VALUES(change_pct),
                ingest_ts = CURRENT_TIMESTAMP
        """
        
        cursor.execute(sql, (
            trade_date, open_price, high_price, low_price, close_price,
            volume, open_interest, turnover, price_change, change_pct
        ))
        
        conn.commit()
        cursor.close()
        return True
        
    except Exception as e:
        logger.error(f"插入数据失败 (symbol={symbol}): {e}")
        conn.rollback()
        return False

def save_all_data_to_db(all_results):
    """
    将所有爬取的数据保存到数据库
    
    Args:
        all_results: 所有交易所的期货数据
    """
    if not all_results:
        logger.warning("没有数据需要保存到数据库")
        return
    
    # 获取当前日期作为交易日期
    trade_date = datetime.now().strftime('%Y-%m-%d')
    logger.info(f"开始将数据保存到数据库，交易日期: {trade_date}")
    
    try:
        conn = get_db_connection()
        
        total_success = 0
        total_failed = 0
        
        # 遍历所有交易所的数据
        for exchange_id, result in all_results.items():
            exchange_name = result.get('exchange_name', exchange_id)
            data_list = result.get('list', [])
            
            logger.info(f"正在处理 {exchange_name} 的 {len(data_list)} 条数据...")
            
            for item in data_list:
                if insert_futures_data_to_db(conn, item, trade_date):
                    total_success += 1
                else:
                    total_failed += 1
        
        conn.close()
        
        logger.info(f"数据库保存完成！成功: {total_success} 条，失败: {total_failed} 条")
        return total_success, total_failed
        
    except Exception as e:
        logger.error(f"数据库保存过程发生错误: {e}")
        return 0, 0

def load_contracts_filter():
    """
    加载 contracts_main.json，提取需要过滤的期货品种 symbol 列表
    """
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        contracts_file = os.path.join(current_dir, "contracts_main.json")
        
        with open(contracts_file, "r", encoding="utf-8") as f:
            contracts_data = json.load(f)
        
        # 提取所有 symbol，转换为小写以便匹配
        symbols = set()
        for contract in contracts_data.get("contracts_main", []):
            symbol = contract.get("symbol", "").lower()
            if symbol:
                symbols.add(symbol)
        
        logger.info(f"已加载 {len(symbols)} 个期货品种作为过滤条件")
        return symbols
    except Exception as e:
        logger.error(f"加载 contracts_main.json 失败: {e}")
        return set()

def filter_futures_data(data, valid_symbols):
    """
    根据 valid_symbols 过滤期货数据
    """
    if not data or not valid_symbols:
        return data
    
    original_list = data.get('list', [])
    filtered_list = []
    
    for item in original_list:
        # 从 dm 字段获取 symbol（东方财富API返回的字段）
        symbol = item.get('dm', '').lower()
        if symbol in valid_symbols:
            filtered_list.append(item)
    
    data['list'] = filtered_list
    data['filtered_count'] = len(filtered_list)
    data['original_count'] = len(original_list)
    
    logger.info(f"数据过滤完成: 原始 {len(original_list)} 条 -> 过滤后 {len(filtered_list)} 条")
    
    return data

def parse_jsonp(content):
    """解析JSONP格式的响应"""
    match = re.search(r'^\w+\((.*)\)', content)
    data_str = ""
    if match:
        data_str = match.group(1)
    else:
        data_str = content
    
    # 清理可能的尾部分号
    if data_str.endswith(';'):
        data_str = data_str[:-1]
    
    return json.loads(data_str)

def get_single_exchange_data(driver, exchange_id, exchange_name):
    """
    获取单个交易所的期货数据
    
    Args:
        driver: Selenium WebDriver 实例
        exchange_id: 交易所ID (如 113, 114等)
        exchange_name: 交易所名称 (如 "上期所", "大商所"等)
    
    Returns:
        dict: 包含该交易所数据的字典，如果失败返回 None
    """
    try:
        target_url = f"https://quote.eastmoney.com/center/gridlist.html#futures_{exchange_id}"
        logger.info(f"正在打开 {exchange_name} 页面: {target_url}")
        driver.get(target_url)
        
        # 等待页面加载和请求发送
        logger.info(f"等待 {exchange_name} 页面加载及数据请求...")
        time.sleep(5)  # 简单等待，确保请求已发出
        
        # 获取性能日志
        logs = driver.get_log('performance')
        
        api_pattern = f"futsseapi.eastmoney.com/list/{exchange_id}"
        found_url = None
        
        logger.info(f"正在扫描 {exchange_name} 网络日志查找 API 请求...")
        for entry in logs:
            try:
                message_obj = json.loads(entry['message'])
                message = message_obj.get('message', {})
                
                # 只关注请求发送事件
                if message.get('method') == 'Network.requestWillBeSent':
                    request_url = message['params']['request']['url']
                    if api_pattern in request_url:
                        logger.info(f"找到 {exchange_name} API URL: {request_url}")
                        found_url = request_url
                        break # 找到第一个匹配的即可
            except Exception as e:
                continue
        
        if found_url:
            # 提取必要的头部信息
            headers = {
                "User-Agent": driver.execute_script("return navigator.userAgent;"),
                "Referer": target_url
            }
            
            # 第一步：先请求一次获取 total 数量
            logger.info(f"{exchange_name} - 第一次请求：获取数据总数...")
            try:
                response = requests.get(found_url, headers=headers)
                
                if response.status_code == 200:
                    content = response.text
                    initial_data = parse_jsonp(content)
                    total = initial_data.get('total', 0)
                    logger.info(f"{exchange_name} - 获取到数据总数: {total}")
                    
                    if total == 0:
                        logger.warning(f"{exchange_name} - 数据总数为 0，没有可获取的数据")
                        return None
                    
                    # 第二步：修改 URL 参数，一次性获取所有数据
                    logger.info(f"{exchange_name} - 第二次请求：获取全部 {total} 条数据...")
                    parsed_url = urlparse(found_url)
                    query_params = parse_qs(parsed_url.query)
                    
                    # 修改 pageSize 为 total，pageIndex 为 0
                    query_params['pageSize'] = [str(total)]
                    query_params['pageIndex'] = ['0']
                    
                    # 重新构建 URL
                    new_query = urlencode(query_params, doseq=True)
                    new_url = urlunparse((
                        parsed_url.scheme,
                        parsed_url.netloc,
                        parsed_url.path,
                        parsed_url.params,
                        new_query,
                        parsed_url.fragment
                    ))
                    
                    # 发送第二次请求
                    response = requests.get(new_url, headers=headers)
                    
                    if response.status_code == 200:
                        content = response.text
                        final_data = parse_jsonp(content)
                        actual_count = len(final_data.get('list', []))
                        logger.info(f"{exchange_name} - 成功获取 {actual_count}/{total} 条数据")
                        
                        # 添加交易所标识
                        final_data['exchange_id'] = exchange_id
                        final_data['exchange_name'] = exchange_name
                        
                        return final_data
                    else:
                        logger.error(f"{exchange_name} - 第二次请求失败，状态码: {response.status_code}")
                else:
                    logger.error(f"{exchange_name} - 第一次请求失败，状态码: {response.status_code}")
            except json.JSONDecodeError as e:
                logger.error(f"{exchange_name} - JSON 解析失败: {e}")
            except Exception as e:
                logger.error(f"{exchange_name} - 请求过程中发生错误: {e}")
        else:
            logger.warning(f"{exchange_name} - 未在日志中找到目标 API 请求")
            
    except Exception as e:
        logger.error(f"{exchange_name} - 处理过程发生错误: {e}")
    
    return None


def get_all_futures_data():
    """
    使用Selenium打开所有交易所期货页面，劫持API请求参数，并获取数据
    """
    # 定义所有交易所配置
    exchanges = [
        {"id": "113", "name": "上期所"},
        {"id": "142", "name": "上期能源"},
        {"id": "114", "name": "大商所"},
        {"id": "115", "name": "郑商所"},
        {"id": "225", "name": "广期所"},
    ]
    
    # 配置 Chrome 选项
    chrome_options = Options()
    # 如果需要无头模式，取消下面一行的注释
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--ignore-certificate-errors")
    
    # 关键：启用性能日志以捕获网络请求
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    driver = None
    all_results = {}
    
    try:
        logger.info("正在启动 Chrome 浏览器...")
        driver = webdriver.Chrome(options=chrome_options)
        
        # 遍历所有交易所
        for exchange in exchanges:
            exchange_id = exchange['id']
            exchange_name = exchange['name']
            
            logger.info(f"\n{'='*50}")
            logger.info(f"开始爬取: {exchange_name} (ID: {exchange_id})")
            logger.info(f"{'='*50}")
            
            result = get_single_exchange_data(driver, exchange_id, exchange_name)
            
            if result:
                all_results[exchange_id] = result
                logger.info(f"{exchange_name} 数据获取成功！")
            else:
                logger.warning(f"{exchange_name} 数据获取失败！")
            
            # 每个交易所之间稍微等待一下
            time.sleep(2)
            
    except Exception as e:
        logger.error(f"浏览器操作发生错误: {e}")
    finally:
        if driver:
            logger.info("关闭浏览器...")
            driver.quit()

    return all_results

if __name__ == "__main__":
    # 加载过滤条件
    valid_symbols = load_contracts_filter()
    
    # 获取所有交易所期货数据
    all_results = get_all_futures_data()
    
    if all_results:
        # 过滤数据并统计
        total_original = 0
        total_filtered = 0
        exchanges_info = {}
        
        for exchange_id, result in all_results.items():
            exchange_name = result.get('exchange_name', exchange_id)
            
            # 过滤数据
            if valid_symbols:
                result = filter_futures_data(result, valid_symbols)
            
            original_count = result.get('original_count', result.get('total', 0))
            filtered_count = result.get('filtered_count', len(result.get('list', [])))
            
            total_original += original_count
            total_filtered += filtered_count
            
            exchanges_info[exchange_id] = {
                "name": exchange_name,
                "original_count": original_count,
                "filtered_count": filtered_count
            }
        
        # 打印数据统计信息
        print("\n" + "="*60)
        print("--- 数据获取成功 ---")
        print("="*60)
        for exchange_id, info in exchanges_info.items():
            print(f"{info['name']} (ID: {exchange_id}):")
            print(f"  原始数据: {info['original_count']} 条")
            print(f"  过滤后: {info['filtered_count']} 条")
            print()
        print("-"*60)
        print(f"总计:")
        print(f"  所有交易所数: {len(all_results)}")
        print(f"  原始数据总数: {total_original} 条")
        print(f"  过滤后总数: {total_filtered} 条")
        print("="*60)
        
        # 保存数据到数据库
        print("\n" + "="*60)
        print("--- 开始保存数据到数据库 ---")
        print("="*60)
        success_count, failed_count = save_all_data_to_db(all_results)
        print("-"*60)
        print(f"数据库保存结果:")
        print(f"  成功: {success_count} 条")
        print(f"  失败: {failed_count} 条")
        print("="*60)
    else:
        logger.error("所有交易所数据获取失败！")

