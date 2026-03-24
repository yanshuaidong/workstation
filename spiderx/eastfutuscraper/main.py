import json
import time
import re
import random
import requests
import os
import traceback
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import logging
import pymysql
import pandas as pd
from datetime import datetime

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False

# 配置日志
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
# 仅在直接运行时添加控制台 handler，避免与 scheduler 冲突
if not logger.handlers:
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(console_handler)

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
        logger.debug(f"表 {table_name} 已确认存在")
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
        logger.warning("没有数据需要保存")
        return 0, 0
    
    # 获取当前日期作为交易日期
    trade_date = datetime.now().strftime('%Y-%m-%d')
    
    try:
        conn = get_db_connection()
        
        total_success = 0
        total_failed = 0
        
        # 遍历所有交易所的数据
        for exchange_id, result in all_results.items():
            data_list = result.get('list', [])
            
            for item in data_list:
                if insert_futures_data_to_db(conn, item, trade_date):
                    total_success += 1
                else:
                    total_failed += 1
        
        conn.close()
        
        logger.info(f"入库完成: 成功 {total_success}, 失败 {total_failed}")
        return total_success, total_failed
        
    except Exception as e:
        logger.error(f"数据库保存错误: {e}")
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
        
        logger.debug(f"已加载 {len(symbols)} 个期货品种过滤条件")
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
    """
    tag = f"[{exchange_name}({exchange_id})]"
    try:
        target_url = f"https://quote.eastmoney.com/center/gridlist.html#futures_{exchange_id}"
        logger.info(f"{tag} 打开页面: {target_url}")
        
        page_start = time.time()
        driver.get(target_url)
        
        wait_seconds = 8
        logger.info(f"{tag} 等待页面加载 {wait_seconds}s...")
        time.sleep(wait_seconds)
        page_elapsed = time.time() - page_start
        
        page_title = driver.title
        current_url = driver.current_url
        logger.info(f"{tag} 页面加载完成 ({page_elapsed:.1f}s) | title='{page_title}' | url={current_url}")
        
        logs = driver.get_log('performance')
        logger.info(f"{tag} 性能日志条数: {len(logs)}")
        
        if len(logs) == 0:
            logger.warning(f"{tag} 性能日志为空！可能 Chrome 未正确捕获网络请求")
            return None
        
        api_pattern = f"futsseapi.eastmoney.com/list/{exchange_id}"
        found_url = None
        network_request_count = 0
        all_api_urls = []
        
        for entry in logs:
            try:
                message_obj = json.loads(entry['message'])
                message = message_obj.get('message', {})
                
                if message.get('method') == 'Network.requestWillBeSent':
                    network_request_count += 1
                    request_url = message['params']['request']['url']
                    if 'eastmoney.com' in request_url:
                        all_api_urls.append(request_url[:120])
                    if api_pattern in request_url:
                        found_url = request_url
                        break
            except Exception:
                continue
        
        logger.info(f"{tag} 网络请求总数: {network_request_count}, eastmoney 相关请求: {len(all_api_urls)}")
        
        if not found_url:
            logger.warning(f"{tag} 未找到目标 API (pattern={api_pattern})")
            if all_api_urls:
                logger.info(f"{tag} eastmoney 请求列表 (前10条):")
                for i, url in enumerate(all_api_urls[:10]):
                    logger.info(f"{tag}   [{i+1}] {url}")
            else:
                logger.warning(f"{tag} 未捕获任何 eastmoney 请求，页面可能未正常加载")
            return None
        
        logger.info(f"{tag} 找到目标 API: {found_url[:150]}")
        
        headers = {
            "User-Agent": driver.execute_script("return navigator.userAgent;"),
            "Referer": target_url
        }
        
        try:
            resp1_start = time.time()
            response = requests.get(found_url, headers=headers, timeout=15)
            resp1_elapsed = time.time() - resp1_start
            
            if response.status_code != 200:
                logger.error(f"{tag} 首次请求失败 (HTTP {response.status_code}, {resp1_elapsed:.1f}s)")
                return None
            
            initial_data = parse_jsonp(response.text)
            total = initial_data.get('total', 0)
            logger.info(f"{tag} 首次请求成功 ({resp1_elapsed:.1f}s), 数据总量: {total}")
            
            if total == 0:
                logger.warning(f"{tag} 数据总数为 0，可能当日无数据")
                return None
            
            parsed_url = urlparse(found_url)
            query_params = parse_qs(parsed_url.query)
            query_params['pageSize'] = [str(total)]
            query_params['pageIndex'] = ['0']
            new_query = urlencode(query_params, doseq=True)
            new_url = urlunparse((
                parsed_url.scheme, parsed_url.netloc, parsed_url.path,
                parsed_url.params, new_query, parsed_url.fragment
            ))
            
            resp2_start = time.time()
            response = requests.get(new_url, headers=headers, timeout=30)
            resp2_elapsed = time.time() - resp2_start
            
            if response.status_code != 200:
                logger.error(f"{tag} 全量请求失败 (HTTP {response.status_code}, {resp2_elapsed:.1f}s)")
                return None
            
            final_data = parse_jsonp(response.text)
            actual_count = len(final_data.get('list', []))
            logger.info(f"{tag} 全量请求成功 ({resp2_elapsed:.1f}s), 获取 {actual_count} 条数据")
            
            final_data['exchange_id'] = exchange_id
            final_data['exchange_name'] = exchange_name
            return final_data
            
        except requests.Timeout:
            logger.error(f"{tag} HTTP 请求超时")
        except json.JSONDecodeError as e:
            logger.error(f"{tag} JSON 解析失败: {e} | 响应前200字符: {response.text[:200]}")
        except Exception as e:
            logger.error(f"{tag} HTTP 请求异常: {e}")
            
    except Exception as e:
        logger.error(f"{tag} 处理异常: {e}")
        logger.error(traceback.format_exc())
    
    return None


def create_chrome_driver():
    """创建并返回一个新的 Chrome WebDriver 实例"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})

    driver = webdriver.Chrome(options=chrome_options)
    
    chrome_version = driver.capabilities.get('browserVersion', 'unknown')
    chromedriver_version = driver.capabilities.get('chrome', {}).get('chromedriverVersion', 'unknown')
    logger.info(f"Chrome 已启动 | 浏览器版本: {chrome_version} | 驱动版本: {chromedriver_version}")
    
    return driver


def get_all_futures_data():
    """
    使用 Selenium 打开所有交易所期货页面，劫持 API 请求参数，并获取数据。
    每个交易所失败后会重试（新建 driver），确保单个交易所的失败不影响其他交易所。
    """
    exchanges = [
        {"id": "113", "name": "上期所"},
        {"id": "142", "name": "上期能源"},
        {"id": "114", "name": "大商所"},
        {"id": "115", "name": "郑商所"},
        {"id": "225", "name": "广期所"},
    ]
    
    max_exchange_retries = 2
    all_results = {}
    driver = None
    
    try:
        logger.info(f"开始爬取 {len(exchanges)} 个交易所数据")
        driver = create_chrome_driver()
        
        for exchange in exchanges:
            exchange_id = exchange['id']
            exchange_name = exchange['name']
            success = False
            
            for attempt in range(1, max_exchange_retries + 1):
                if attempt > 1:
                    logger.info(f"[{exchange_name}] 第 {attempt} 次尝试，重建浏览器实例...")
                    try:
                        if driver:
                            driver.quit()
                    except Exception:
                        pass
                    time.sleep(3)
                    try:
                        driver = create_chrome_driver()
                    except Exception as e:
                        logger.error(f"[{exchange_name}] 重建浏览器失败: {e}")
                        driver = None
                        break
                
                if driver is None:
                    logger.error(f"[{exchange_name}] 无可用浏览器实例，跳过")
                    break
                
                result = get_single_exchange_data(driver, exchange_id, exchange_name)
                
                if result:
                    all_results[exchange_id] = result
                    logger.info(f"[{exchange_name}] 获取成功 (第{attempt}次尝试)")
                    success = True
                    break
                else:
                    logger.warning(f"[{exchange_name}] 第 {attempt}/{max_exchange_retries} 次尝试失败")
            
            if not success:
                logger.error(f"[{exchange_name}] 所有尝试均失败")
            
            time.sleep(2)
            
    except Exception as e:
        logger.error(f"浏览器操作错误: {e}")
        logger.error(traceback.format_exc())
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器异常: {e}")
    
    logger.info(f"爬取完成: {len(all_results)}/{len(exchanges)} 个交易所成功")
    return all_results


# ─────────────────────────── AkShare 降级方案 ──────────────────────

def load_futures_mapping():
    """加载 futures_mapping.json，返回 symbol -> api_symbol 的映射"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    mapping_path = os.path.join(current_dir, "futures_mapping.json")
    
    try:
        with open(mapping_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("futures", {})
    except Exception as e:
        logger.error(f"加载 futures_mapping.json 失败: {e}")
        return {}


def fetch_akshare_day(api_symbol, target_date, max_retries=3):
    """
    通过 AkShare 拉取单个品种的主连历史数据，返回 target_date 当天的行。
    
    Args:
        api_symbol: AkShare 品种代码 (如 "CU0", "RB0")
        target_date: 目标日期 "YYYY-MM-DD"
        max_retries: 最大重试次数
    
    Returns:
        dict: 包含 OHLCV 等字段的字典，失败返回 None
    """
    col_map = {
        "日期": "trade_date",
        "开盘价": "open_price",
        "最高价": "high_price",
        "最低价": "low_price",
        "收盘价": "close_price",
        "成交量": "volume",
        "持仓量": "open_interest",
    }
    
    for attempt in range(1, max_retries + 1):
        try:
            df = ak.futures_main_sina(symbol=api_symbol)
            if df is None or df.empty:
                return None
            
            df = df.rename(columns={k: v for k, v in col_map.items() if k in df.columns})
            if "trade_date" not in df.columns:
                return None
            
            df["trade_date"] = pd.to_datetime(df["trade_date"]).dt.strftime("%Y-%m-%d")
            row = df[df["trade_date"] == target_date]
            
            if row.empty:
                return None
            
            r = row.iloc[0]
            return {
                "open_price": safe_decimal(r.get("open_price"), 0),
                "high_price": safe_decimal(r.get("high_price"), 0),
                "low_price": safe_decimal(r.get("low_price"), 0),
                "close_price": safe_decimal(r.get("close_price"), 0),
                "volume": int(safe_decimal(r.get("volume"), 0)),
                "open_interest": int(safe_decimal(r.get("open_interest"), 0)),
            }
        except Exception as e:
            if attempt < max_retries:
                wait = 2 ** attempt + random.uniform(0.5, 1.5)
                logger.warning(f"  AkShare {api_symbol} 第{attempt}次失败: {e}, {wait:.1f}s 后重试")
                time.sleep(wait)
            else:
                logger.warning(f"  AkShare {api_symbol} {max_retries}次重试全部失败: {e}")
                return None


def akshare_upsert_row(conn, symbol, trade_date, data):
    """将 AkShare 获取的单条数据写入数据库"""
    table = f"hist_{symbol.lower()}"
    create_history_table(conn, symbol.lower())
    
    sql = f"""
        INSERT INTO {table}
            (trade_date, open_price, high_price, low_price, close_price,
             volume, open_interest)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            open_price    = VALUES(open_price),
            high_price    = VALUES(high_price),
            low_price     = VALUES(low_price),
            close_price   = VALUES(close_price),
            volume        = VALUES(volume),
            open_interest = VALUES(open_interest),
            ingest_ts     = CURRENT_TIMESTAMP
    """
    cursor = conn.cursor()
    try:
        cursor.execute(sql, (
            trade_date,
            data["open_price"], data["high_price"], data["low_price"],
            data["close_price"], data["volume"], data["open_interest"],
        ))
        conn.commit()
        return True
    except Exception as e:
        logger.error(f"  AkShare 写库失败 {table}: {e}")
        conn.rollback()
        return False
    finally:
        cursor.close()


def fallback_akshare_crawl(target_date=None):
    """
    AkShare 降级爬取：当 Selenium 主流程失败时调用。
    仅爬取 contracts_main.json 中的品种。
    
    Args:
        target_date: 目标日期 "YYYY-MM-DD"，默认当天
        
    Returns:
        tuple: (success_count, failed_count, skip_count)
    """
    if not HAS_AKSHARE:
        logger.error("[AkShare降级] akshare 库未安装，无法执行降级方案")
        return 0, 0, 0
    
    if target_date is None:
        target_date = datetime.now().strftime("%Y-%m-%d")
    
    logger.info(f"[AkShare降级] 开始执行，目标日期: {target_date}")
    
    futures_mapping = load_futures_mapping()
    if not futures_mapping:
        logger.error("[AkShare降级] futures_mapping.json 加载失败")
        return 0, 0, 0
    
    valid_symbols = load_contracts_filter()
    if not valid_symbols:
        logger.warning("[AkShare降级] contracts_main.json 过滤列表为空，将跳过")
        return 0, 0, 0
    
    # 构建需要爬取的品种列表：contracts_main 中的 symbol 与 mapping 的交集
    symbols_to_fetch = []
    for symbol in valid_symbols:
        symbol_lower = symbol.lower()
        mapping_entry = futures_mapping.get(symbol) or futures_mapping.get(symbol_lower)
        if not mapping_entry:
            for k, v in futures_mapping.items():
                if k.lower() == symbol_lower:
                    mapping_entry = v
                    break
        if mapping_entry:
            symbols_to_fetch.append({
                "symbol": symbol_lower,
                "api_symbol": mapping_entry["api_symbol"],
                "name": mapping_entry.get("name", symbol),
            })
        else:
            logger.warning(f"[AkShare降级] 品种 {symbol} 在 futures_mapping.json 中未找到映射，跳过")
    
    total = len(symbols_to_fetch)
    logger.info(f"[AkShare降级] 需要爬取 {total} 个品种")
    
    if total == 0:
        return 0, 0, 0
    
    conn = None
    ok, fail, skip = 0, 0, 0
    
    try:
        conn = get_db_connection()
        
        for idx, item in enumerate(symbols_to_fetch, 1):
            symbol = item["symbol"]
            api_symbol = item["api_symbol"]
            name = item["name"]
            
            logger.info(f"[AkShare降级] [{idx}/{total}] {symbol}({name}) -> {api_symbol}")
            
            data = fetch_akshare_day(api_symbol, target_date)
            
            if data is None:
                logger.info(f"[AkShare降级] [{idx}/{total}] {symbol} - {target_date} 无数据")
                skip += 1
            else:
                if akshare_upsert_row(conn, symbol, target_date, data):
                    logger.info(
                        f"[AkShare降级] [{idx}/{total}] {symbol} 写入成功 "
                        f"(close={data['close_price']}, vol={data['volume']})"
                    )
                    ok += 1
                else:
                    fail += 1
            
            if idx < total:
                time.sleep(random.uniform(0.8, 1.5))
    
    except Exception as e:
        logger.error(f"[AkShare降级] 执行异常: {e}")
        logger.error(traceback.format_exc())
    finally:
        if conn:
            try:
                conn.close()
            except Exception:
                pass
    
    logger.info(f"[AkShare降级] 完成: 成功 {ok}, 跳过 {skip}, 失败 {fail}")
    return ok, fail, skip


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

