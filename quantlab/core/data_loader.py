"""
数据加载器 - 从 futures.db 读取主连数据
"""
import sqlite3
import pandas as pd
from pathlib import Path
import backtrader as bt

# 数据库路径（相对于 quantlab 目录）
DB_PATH = Path(__file__).parent.parent.parent / "database" / "futures" / "futures.db"


def get_available_symbols() -> list:
    """
    获取所有可用品种列表
    
    Returns:
        list: [{'symbol': 'xxx', 'name': 'xxx'}, ...]
    """
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql("SELECT symbol, name FROM contracts_main WHERE is_active = 1", conn)
    return df.to_dict('records')


def load_symbol_data(symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """
    加载单个品种的历史数据
    
    Args:
        symbol: 品种代码（如 'rbm', 'cum'，不区分大小写）
        start_date: 开始日期 'YYYY-MM-DD'
        end_date: 结束日期 'YYYY-MM-DD'
    
    Returns:
        DataFrame with columns: date(index), open, high, low, close, volume, openinterest
    """
    table_name = f"hist_{symbol.lower()}"
    
    query = f"""
        SELECT trade_date, open_price, high_price, low_price, close_price, volume, open_interest
        FROM {table_name}
        WHERE 1=1
    """
    if start_date:
        query += f" AND trade_date >= '{start_date}'"
    if end_date:
        query += f" AND trade_date <= '{end_date}'"
    query += " ORDER BY trade_date"
    
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql(query, conn)
    
    if df.empty:
        raise ValueError(f"No data found for symbol {symbol}")
    
    # 转换为 Backtrader 标准列名
    df.columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'openinterest']
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    return df


def create_bt_datafeed(symbol: str, start_date: str = None, end_date: str = None) -> bt.feeds.PandasData:
    """
    创建 Backtrader DataFeed 对象
    
    Args:
        symbol: 品种代码
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        bt.feeds.PandasData 对象
    """
    df = load_symbol_data(symbol, start_date, end_date)
    
    data = bt.feeds.PandasData(
        dataname=df,
        datetime=None,  # index 即为日期
        open='open',
        high='high',
        low='low',
        close='close',
        volume='volume',
        openinterest='openinterest'
    )
    
    return data


def load_multi_symbols(symbols: list, start_date: str = None, end_date: str = None) -> dict:
    """
    加载多个品种数据
    
    Args:
        symbols: 品种代码列表
        start_date: 开始日期
        end_date: 结束日期
    
    Returns:
        dict: {symbol: bt.feeds.PandasData}
    """
    feeds = {}
    for symbol in symbols:
        try:
            feeds[symbol] = create_bt_datafeed(symbol, start_date, end_date)
            print(f"✓ 加载 {symbol} 成功")
        except Exception as e:
            print(f"✗ 加载 {symbol} 失败 - {e}")
    return feeds


def get_symbol_info(symbol: str) -> dict:
    """
    获取品种详细信息
    
    Args:
        symbol: 品种代码
    
    Returns:
        dict: {'symbol': 'xxx', 'name': 'xxx', 'exchange': 'xxx', ...}
    """
    with sqlite3.connect(DB_PATH) as conn:
        df = pd.read_sql(
            f"SELECT * FROM contracts_main WHERE symbol = '{symbol.upper()}' OR symbol = '{symbol.lower()}'",
            conn
        )
    if df.empty:
        return None
    return df.iloc[0].to_dict()


def list_all_tables() -> list:
    """列出数据库中所有表名"""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        return [row[0] for row in cursor.fetchall()]


if __name__ == '__main__':
    # 测试代码
    print("数据库路径:", DB_PATH)
    print("数据库存在:", DB_PATH.exists())
    
    print("\n所有表:")
    for table in list_all_tables():
        print(f"  - {table}")
    
    print("\n可用品种:")
    symbols = get_available_symbols()
    for s in symbols[:10]:  # 只显示前10个
        print(f"  - {s['symbol']}: {s['name']}")
    print(f"  ... 共 {len(symbols)} 个品种")
