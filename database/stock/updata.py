"""
股票数据每日更新维护脚本
功能：
1. 检查 stock_main 表：新增上市股票、删除退市股票
2. 维护 hist_{symbol} 表：创建新表、更新数据至最新日期、删除退市股票表
"""

import sqlite3
import akshare as ak
from datetime import datetime, timedelta
from pathlib import Path


def get_db_path():
    """获取数据库路径"""
    return Path(__file__).parent / "stock.db"


def get_market_by_symbol(symbol: str) -> str:
    """根据股票代码判断市场"""
    if symbol.startswith('6'):
        return 'SH'
    elif symbol.startswith('0') or symbol.startswith('3'):
        return 'SZ'
    elif symbol.startswith('4') or symbol.startswith('8'):
        return 'BJ'
    else:
        return 'UNKNOWN'


def fetch_latest_stock_list():
    """从 akshare 获取最新A股列表"""
    print("正在获取最新A股列表...")
    stock_info = ak.stock_info_a_code_name()
    latest_stocks = {row['code']: row['name'] for _, row in stock_info.iterrows()}
    print(f"  获取到 {len(latest_stocks)} 只股票")
    return latest_stocks


def get_db_stocks(conn):
    """获取数据库中的股票列表"""
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, name FROM stock_main")
    return {row[0]: row[1] for row in cursor.fetchall()}


def update_stock_main(conn, latest_stocks, db_stocks):
    """更新 stock_main 表"""
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    new_stocks = []
    delisted_stocks = []
    name_changed = []
    
    # 1. 检查新上市股票
    for symbol, name in latest_stocks.items():
        if symbol not in db_stocks:
            # 新上市股票
            market = get_market_by_symbol(symbol)
            cursor.execute("""
                INSERT INTO stock_main (symbol, name, market, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (symbol, name, market, now, now))
            new_stocks.append((symbol, name))
        else:
            # 已存在的股票，检查是否改名
            if db_stocks[symbol] != name:
                cursor.execute("""
                    UPDATE stock_main SET name = ?, updated_at = ? WHERE symbol = ?
                """, (name, now, symbol))
                name_changed.append((symbol, db_stocks[symbol], name))
    
    # 2. 检查退市股票并删除
    for symbol, name in db_stocks.items():
        if symbol not in latest_stocks:
            # 删除 stock_main 记录
            cursor.execute("DELETE FROM stock_main WHERE symbol = ?", (symbol,))
            # 删除对应的 hist 表
            table_name = f"hist_{symbol}"
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            delisted_stocks.append((symbol, name))
    
    conn.commit()
    
    return {
        'new': new_stocks,
        'delisted': delisted_stocks,
        'name_changed': name_changed
    }


def create_hist_table(conn, symbol):
    """为股票创建历史数据表"""
    table_name = f"hist_{symbol}"
    cursor = conn.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            date TEXT PRIMARY KEY,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume INTEGER,
            amount REAL,
            amplitude REAL,
            pct_change REAL,
            change REAL,
            turnover REAL
        )
    """)
    conn.commit()


def get_last_date(conn, symbol):
    """获取某只股票历史数据的最后日期"""
    table_name = f"hist_{symbol}"
    cursor = conn.cursor()
    try:
        cursor.execute(f"SELECT MAX(date) FROM {table_name}")
        result = cursor.fetchone()[0]
        return result
    except:
        return None


def fetch_hist_data(symbol, start_date, end_date=None):
    """从 akshare 获取股票历史数据"""
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
    
    try:
        hist = ak.stock_zh_a_hist(
            symbol=symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        return hist
    except Exception as e:
        print(f"    ❌ 获取数据失败: {e}")
        return None


def save_hist_data(conn, symbol, hist_df):
    """保存历史数据到数据库"""
    if hist_df is None or hist_df.empty:
        return 0
    
    table_name = f"hist_{symbol}"
    cursor = conn.cursor()
    inserted = 0
    
    for _, row in hist_df.iterrows():
        try:
            date_str = str(row['日期'])
            cursor.execute(f"""
                INSERT OR REPLACE INTO {table_name}
                (date, open, high, low, close, volume, amount, amplitude, pct_change, change, turnover)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                date_str,
                row['开盘'],
                row['最高'],
                row['最低'],
                row['收盘'],
                row['成交量'],
                row['成交额'],
                row['振幅'],
                row['涨跌幅'],
                row['涨跌额'],
                row['换手率']
            ))
            inserted += 1
        except Exception as e:
            pass  # 静默处理单条插入错误
    
    conn.commit()
    return inserted


def update_hist_tables(conn, latest_stocks, changes):
    """更新历史数据表"""
    cursor = conn.cursor()
    today = datetime.now().strftime("%Y%m%d")
    
    stats = {
        'new_tables': 0,
        'updated': 0,
        'failed': 0,
        'total_records': 0
    }
    
    # 1. 为新上市股票创建表并获取全部历史数据
    if changes['new']:
        print(f"\n📊 为 {len(changes['new'])} 只新股票创建历史数据表...")
        for symbol, name in changes['new']:
            print(f"  处理新股票 {symbol} - {name}")
            create_hist_table(conn, symbol)
            
            # 获取 2018-01-02 至今的数据
            hist_df = fetch_hist_data(symbol, "20180102", today)
            if hist_df is not None and not hist_df.empty:
                records = save_hist_data(conn, symbol, hist_df)
                stats['new_tables'] += 1
                stats['total_records'] += records
                print(f"    ✅ 保存 {records} 条记录")
            else:
                stats['failed'] += 1
                print(f"    ❌ 获取数据失败")
    
    # 2. 更新现有股票的最新数据
    print(f"\n📊 更新现有股票的最新数据...")
    
    # 获取所有股票
    cursor.execute("SELECT symbol, name FROM stock_main")
    active_stocks = cursor.fetchall()
    
    # 排除刚处理过的新股票
    new_symbols = {s[0] for s in changes['new']}
    stocks_to_update = [(s, n) for s, n in active_stocks if s not in new_symbols]
    
    print(f"  需要更新 {len(stocks_to_update)} 只股票")
    
    for i, (symbol, name) in enumerate(stocks_to_update, 1):
        # 获取最后更新日期
        last_date = get_last_date(conn, symbol)
        
        if last_date is None:
            # 没有历史表或表为空，创建并获取全部数据
            print(f"  [{i}/{len(stocks_to_update)}] {symbol} - 无历史数据，获取全部...")
            create_hist_table(conn, symbol)
            start_date = "20180102"
        else:
            # 从最后日期的下一天开始获取
            last_dt = datetime.strptime(last_date, "%Y-%m-%d")
            next_dt = last_dt + timedelta(days=1)
            
            # 如果已经是最新，跳过
            if next_dt.strftime("%Y%m%d") > today:
                continue
            
            start_date = next_dt.strftime("%Y%m%d")
            print(f"  [{i}/{len(stocks_to_update)}] {symbol} - 从 {start_date} 更新...")
        
        hist_df = fetch_hist_data(symbol, start_date, today)
        if hist_df is not None and not hist_df.empty:
            records = save_hist_data(conn, symbol, hist_df)
            stats['updated'] += 1
            stats['total_records'] += records
            print(f"    ✅ 新增 {records} 条记录")
        else:
            # 可能是没有新数据（周末/节假日），不算失败
            pass
    
    return stats


def print_summary(stock_changes, hist_stats):
    """打印更新摘要"""
    print("\n" + "=" * 60)
    print("📋 更新摘要")
    print("=" * 60)
    
    print("\n【stock_main 表变动】")
    print(f"  新上市股票: {len(stock_changes['new'])} 只")
    if stock_changes['new']:
        for symbol, name in stock_changes['new'][:5]:
            print(f"    + {symbol} {name}")
        if len(stock_changes['new']) > 5:
            print(f"    ... 还有 {len(stock_changes['new']) - 5} 只")
    
    print(f"  退市股票(已删除): {len(stock_changes['delisted'])} 只")
    if stock_changes['delisted']:
        for symbol, name in stock_changes['delisted'][:5]:
            print(f"    - {symbol} {name} (已删除记录和历史表)")
        if len(stock_changes['delisted']) > 5:
            print(f"    ... 还有 {len(stock_changes['delisted']) - 5} 只")
    
    print(f"  股票改名: {len(stock_changes['name_changed'])} 只")
    if stock_changes['name_changed']:
        for symbol, old_name, new_name in stock_changes['name_changed'][:3]:
            print(f"    {symbol}: {old_name} → {new_name}")
    
    print("\n【hist 表变动】")
    print(f"  新建表: {hist_stats['new_tables']} 个")
    print(f"  更新表: {hist_stats['updated']} 个")
    print(f"  新增记录: {hist_stats['total_records']} 条")
    
    print("=" * 60)


def main():
    """主函数"""
    print("=" * 60)
    print("📅 股票数据每日更新")
    print(f"⏰ 执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    db_path = get_db_path()
    
    if not db_path.exists():
        print("❌ 数据库文件不存在，请先运行 getstock_main.py")
        return
    
    conn = sqlite3.connect(db_path)
    
    try:
        # 1. 获取最新股票列表
        latest_stocks = fetch_latest_stock_list()
        
        # 2. 获取数据库中的股票列表
        db_stocks = get_db_stocks(conn)
        print(f"  数据库现有 {len(db_stocks)} 只股票")
        
        # 3. 更新 stock_main 表
        print("\n🔄 更新 stock_main 表...")
        stock_changes = update_stock_main(conn, latest_stocks, db_stocks)
        
        # 4. 更新 hist 表
        hist_stats = update_hist_tables(conn, latest_stocks, stock_changes)
        
        # 5. 打印摘要
        print_summary(stock_changes, hist_stats)
        
        print(f"\n✅ 更新完成！数据库位置: {db_path}")
        
    except Exception as e:
        print(f"\n❌ 更新过程出错: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
