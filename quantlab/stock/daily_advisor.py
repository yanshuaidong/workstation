"""
daily_advisor.py - 每日操作建议脚本
用于读取数据，输出操作建议

运行频率: 每日/每周
功能: 加载模型 -> 读取持仓 -> 获取行情 -> 计算概率 -> 输出建议
"""

import sqlite3
import pandas as pd
import numpy as np
import joblib
import json
import os
from datetime import datetime, timedelta
from tabulate import tabulate
import warnings

warnings.filterwarnings('ignore')

# ============ 配置 ============
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'stock.db')
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models', 'model.pkl')
PORTFOLIO_PATH = os.path.join(os.path.dirname(__file__), 'portfolio.json')

# 阈值配置
TAKE_PROFIT = 0.25      # 止盈线 +25%
STOP_LOSS = -0.10       # 止损线 -10%
TOP_N = 5               # Top 榜单数量
STRONG_RECOMMEND = 0.65 # 强烈推荐阈值
RECOMMEND = 0.55        # 推荐阈值
HOLD_WEEKS_THRESHOLD = 3  # 持有周数阈值

# 特征列表（与 train.py 保持一致）
FEATURES = [
    # 价格动量（6个）
    'ret_5d', 'ret_10d', 'ret_20d', 'ret_60d',
    'high_5d_break', 'high_20d_break',
    # 均线（9个）
    'ma5', 'ma10', 'ma20', 'ma60',
    'close_to_ma5', 'close_to_ma20', 'ma5_to_ma20',
    'ma_trend', 'ma20_slope',
    # 波动率（4个）
    'atr_20', 'volatility_20', 'amplitude_mean_10', 'vol_contract',
    # 成交量（6个）
    'volume_ratio', 'volume_ma5', 'volume_ma20',
    'volume_trend', 'turnover_mean_10', 'amount_rank',
    # 技术指标（5个）
    'rsi_14', 'macd', 'macd_signal', 'macd_hist', 'macd_cross',
    # 位置（4个）
    'pct_from_high_60', 'pct_from_low_60',
    'price_position_60', 'days_since_high_20'
]


def load_model():
    """加载训练好的模型"""
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"模型文件不存在: {MODEL_PATH}")
    
    model_data = joblib.load(MODEL_PATH)
    return model_data['model'], model_data


def load_portfolio():
    """加载持仓文件"""
    if not os.path.exists(PORTFOLIO_PATH):
        return {
            'cash': 0,
            'positions': [],
            'last_update': datetime.now().strftime('%Y-%m-%d')
        }
    
    with open(PORTFOLIO_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_stock_list(conn):
    """获取股票列表（排除北交所）"""
    query = """
    SELECT symbol, name, market 
    FROM stock_main 
    WHERE market != 'BJ'
    """
    return pd.read_sql(query, conn)


def get_stock_history(conn, symbol, limit=100):
    """获取单只股票的历史数据"""
    table_name = f'hist_{symbol}'
    try:
        query = f'SELECT * FROM "{table_name}" ORDER BY date DESC LIMIT {limit}'
        df = pd.read_sql(query, conn)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date').reset_index(drop=True)
        return df
    except Exception:
        return None


def compute_features(df):
    """计算30个特征（与 train.py 保持一致）"""
    if len(df) < 60:
        return None
    
    df = df.copy()
    close = df['close']
    high = df['high']
    low = df['low']
    volume = df['volume']
    amount = df['amount']
    turnover = df['turnover']
    amplitude = df['amplitude']
    
    # ====== 价格动量（6个）======
    df['ret_5d'] = close.pct_change(5)
    df['ret_10d'] = close.pct_change(10)
    df['ret_20d'] = close.pct_change(20)
    df['ret_60d'] = close.pct_change(60)
    df['high_5d_break'] = (close >= high.rolling(5).max()).astype(int)
    df['high_20d_break'] = (close >= high.rolling(20).max()).astype(int)
    
    # ====== 均线（9个）======
    df['ma5'] = close.rolling(5).mean()
    df['ma10'] = close.rolling(10).mean()
    df['ma20'] = close.rolling(20).mean()
    df['ma60'] = close.rolling(60).mean()
    df['close_to_ma5'] = (close - df['ma5']) / df['ma5']
    df['close_to_ma20'] = (close - df['ma20']) / df['ma20']
    df['ma5_to_ma20'] = (df['ma5'] - df['ma20']) / df['ma20']
    df['ma_trend'] = ((df['ma5'] > df['ma10']) & (df['ma10'] > df['ma20'])).astype(int)
    df['ma20_slope'] = df['ma20'].pct_change(20)
    
    # ====== 波动率（4个）======
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    true_range = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    df['atr_20'] = true_range.rolling(20).mean() / close
    df['volatility_20'] = close.pct_change().rolling(20).std()
    df['amplitude_mean_10'] = amplitude.rolling(10).mean()
    df['vol_contract'] = volume / volume.rolling(20).mean()
    
    # ====== 成交量（6个）======
    df['volume_ma5'] = volume.rolling(5).mean()
    df['volume_ma20'] = volume.rolling(20).mean()
    df['volume_ratio'] = df['volume_ma5'] / df['volume_ma20']
    df['volume_trend'] = (df['volume_ma5'] > df['volume_ma20']).astype(int)
    df['turnover_mean_10'] = turnover.rolling(10).mean()
    df['amount_rank'] = amount.rolling(60).apply(
        lambda x: (x.iloc[-1] - x.min()) / (x.max() - x.min() + 1e-9) if len(x) == 60 else np.nan, 
        raw=False
    )
    
    # ====== 技术指标（5个）======
    delta = close.diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    df['rsi_14'] = 100 - (100 / (1 + rs))
    
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    df['macd'] = ema12 - ema26
    df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
    df['macd_hist'] = df['macd'] - df['macd_signal']
    df['macd_cross'] = ((df['macd'] > df['macd_signal']) & 
                        (df['macd'].shift(1) <= df['macd_signal'].shift(1))).astype(int)
    
    # ====== 位置（4个）======
    high_60 = high.rolling(60).max()
    low_60 = low.rolling(60).min()
    df['pct_from_high_60'] = (close - high_60) / high_60
    df['pct_from_low_60'] = (close - low_60) / low_60
    df['price_position_60'] = (close - low_60) / (high_60 - low_60 + 1e-9)
    df['days_since_high_20'] = high.rolling(20).apply(
        lambda x: 19 - np.argmax(x) if len(x) == 20 else np.nan, raw=True
    )
    
    return df


def get_all_predictions(conn, model, stock_list):
    """获取所有股票的预测概率"""
    results = []
    total = len(stock_list)
    
    for idx, row in stock_list.iterrows():
        symbol = row['symbol']
        name = row['name']
        
        # 过滤ST股票
        if 'ST' in name or 'st' in name:
            continue
        
        # 获取历史数据
        df = get_stock_history(conn, symbol, limit=100)
        if df is None or len(df) < 60:
            continue
        
        # 计算特征
        df = compute_features(df)
        if df is None:
            continue
        
        # 获取最新一行
        latest = df.iloc[-1]
        
        # 过滤成交额不足的
        if latest['amount'] < 20000000:  # 2000万
            continue
        
        # 检查特征是否有效
        features = latest[FEATURES].values.reshape(1, -1)
        if np.any(np.isnan(features)) or np.any(np.isinf(features)):
            continue
        
        # 预测
        prob = model.predict(features)[0]
        
        results.append({
            'symbol': symbol,
            'name': name,
            'probability': prob,
            'close': latest['close'],
            'pct_change': latest.get('pct_change', 0),
            'amount': latest['amount']
        })
    
    return pd.DataFrame(results)


def analyze_position(position, predictions_df, today):
    """分析单个持仓"""
    symbol = position['symbol']
    buy_price = position['buy_price']
    buy_date = position['buy_date']
    current_price = position.get('current_price', buy_price)
    
    # 计算盈亏
    pnl_pct = (current_price - buy_price) / buy_price
    
    # 计算持有天数
    buy_dt = datetime.strptime(buy_date, '%Y-%m-%d')
    today_dt = datetime.strptime(today, '%Y-%m-%d')
    hold_days = (today_dt - buy_dt).days
    hold_weeks = hold_days / 7
    
    # 检查是否在TOP N中
    in_top_n = symbol in predictions_df.head(TOP_N)['symbol'].values if len(predictions_df) > 0 else False
    
    # 获取当前概率
    prob = 0
    if len(predictions_df) > 0:
        prob_row = predictions_df[predictions_df['symbol'] == symbol]
        if len(prob_row) > 0:
            prob = prob_row['probability'].values[0]
    
    # 决定建议
    if pnl_pct >= TAKE_PROFIT:
        advice = '🔴 建议止盈卖出'
        reason = f'盈利达到 {pnl_pct*100:.1f}%，触发止盈'
    elif pnl_pct <= STOP_LOSS:
        advice = '🔴 建议止损卖出'
        reason = f'亏损达到 {pnl_pct*100:.1f}%，触发止损'
    elif not in_top_n and hold_weeks >= HOLD_WEEKS_THRESHOLD:
        advice = '🟡 建议换股'
        reason = f'持有 {hold_weeks:.1f} 周，不在 Top {TOP_N}'
    else:
        advice = '✅ 继续持有'
        if in_top_n:
            reason = f'仍在 Top {TOP_N}，概率 {prob:.2f}'
        else:
            reason = f'持仓中，概率 {prob:.2f}'
    
    return {
        'symbol': symbol,
        'name': position['name'],
        'buy_price': buy_price,
        'current_price': current_price,
        'pnl_pct': pnl_pct,
        'hold_days': hold_days,
        'advice': advice,
        'reason': reason,
        'probability': prob
    }


def generate_report(portfolio, predictions_df, position_analysis):
    """生成报告"""
    today = datetime.now().strftime('%Y-%m-%d')
    
    report = []
    report.append("=" * 60)
    report.append(f"📅 交易建议报告 - {today}")
    report.append("=" * 60)
    
    # 持仓分析部分
    report.append("\n💼 当前持仓分析：")
    
    if len(position_analysis) == 0:
        report.append("  （空仓状态）")
        report.append(f"  可用现金: ¥{portfolio['cash']:,.2f}")
    else:
        # 构建持仓表格
        position_table = []
        for pos in position_analysis:
            pnl_str = f"+{pos['pnl_pct']*100:.2f}%" if pos['pnl_pct'] >= 0 else f"{pos['pnl_pct']*100:.2f}%"
            position_table.append([
                pos['symbol'],
                pos['name'],
                f"{pos['buy_price']:.2f}",
                f"{pos['current_price']:.2f}",
                pnl_str,
                pos['advice']
            ])
        
        headers = ['代码', '名称', '买入价', '现价', '盈亏%', '建议']
        report.append(tabulate(position_table, headers=headers, tablefmt='simple'))
        report.append(f"\n  可用现金: ¥{portfolio['cash']:,.2f}")
    
    # Top N 推荐部分
    report.append(f"\n🎯 今日高概率股票 TOP {TOP_N}：")
    
    if len(predictions_df) == 0:
        report.append("  （暂无数据）")
    else:
        top_stocks = predictions_df.head(TOP_N).copy()
        held_symbols = [pos['symbol'] for pos in portfolio['positions']]
        
        top_table = []
        for idx, row in top_stocks.iterrows():
            rank = top_stocks.index.get_loc(idx) + 1
            is_held = row['symbol'] in held_symbols
            
            if row['probability'] >= STRONG_RECOMMEND:
                recommend = '⭐ 持有中' if is_held else '⭐ 推荐'
            elif row['probability'] >= RECOMMEND:
                recommend = '持有中' if is_held else '可关注'
            else:
                recommend = '持有中' if is_held else ''
            
            top_table.append([
                rank,
                row['symbol'],
                row['name'],
                f"{row['probability']:.2f}",
                recommend
            ])
        
        headers = ['排名', '代码', '名称', '概率', '是否推荐']
        report.append(tabulate(top_table, headers=headers, tablefmt='simple'))
    
    # 操作建议部分
    report.append("\n📋 操作建议：")
    
    suggestions = []
    
    # 持仓建议
    for idx, pos in enumerate(position_analysis):
        suggestions.append(f"{idx+1}. {pos['symbol']} {pos['name']}：{pos['advice']}（{pos['reason']}）")
    
    # 新股推荐建议
    held_symbols = [pos['symbol'] for pos in portfolio['positions']]
    recommend_count = len(suggestions)
    
    for idx, row in predictions_df.head(TOP_N).iterrows():
        if row['symbol'] not in held_symbols and row['probability'] >= STRONG_RECOMMEND:
            recommend_count += 1
            suggestions.append(
                f"{recommend_count}. {row['symbol']} {row['name']}：可考虑买入（概率 {row['probability']:.2f}）"
            )
    
    # 空仓建议
    if len(portfolio['positions']) == 0:
        high_prob_stocks = predictions_df[predictions_df['probability'] >= STRONG_RECOMMEND]
        if len(high_prob_stocks) == 0:
            suggestions.append("• 当前无高概率股票（P ≥ 0.65），建议空仓等待")
    
    if len(suggestions) == 0:
        suggestions.append("• 无特别操作建议，继续观察")
    
    for s in suggestions:
        report.append(f"  {s}")
    
    # 风险提示部分
    report.append("\n⚠️ 风险提示：")
    
    risks = []
    for pos in position_analysis:
        if pos['pnl_pct'] >= TAKE_PROFIT:
            risks.append(f"  - {pos['symbol']} 盈利 {pos['pnl_pct']*100:.1f}%，建议止盈")
        elif pos['pnl_pct'] <= STOP_LOSS:
            risks.append(f"  - {pos['symbol']} 亏损 {pos['pnl_pct']*100:.1f}%，建议止损")
        elif pos['pnl_pct'] > 0:
            risks.append(f"  - {pos['symbol']} 盈利 {pos['pnl_pct']*100:.1f}%，未触发止盈(+25%)或止损(-10%)")
        else:
            risks.append(f"  - {pos['symbol']} 亏损 {pos['pnl_pct']*100:.1f}%，未触发止盈(+25%)或止损(-10%)")
    
    if len(risks) == 0:
        risks.append("  - 当前空仓，注意控制建仓节奏")
    
    for r in risks:
        report.append(r)
    
    report.append("\n" + "=" * 60)
    
    return "\n".join(report)


def main():
    """主函数"""
    print("🔄 加载模型中...")
    try:
        model, model_info = load_model()
        print(f"✅ 模型加载成功（训练日期: {model_info.get('train_date', 'N/A')}）")
        print(f"   验证集 AUC: {model_info.get('val_auc', 'N/A'):.4f}")
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("请先运行 train.py 训练模型")
        return
    
    print("\n📂 加载持仓文件...")
    portfolio = load_portfolio()
    print(f"✅ 持仓数量: {len(portfolio['positions'])}")
    print(f"   可用现金: ¥{portfolio['cash']:,.2f}")
    
    print("\n📊 连接数据库并计算预测...")
    conn = sqlite3.connect(DB_PATH)
    
    stock_list = get_stock_list(conn)
    print(f"   股票数量: {len(stock_list)}")
    
    predictions_df = get_all_predictions(conn, model, stock_list)
    predictions_df = predictions_df.sort_values('probability', ascending=False).reset_index(drop=True)
    print(f"   有效预测: {len(predictions_df)}")
    
    conn.close()
    
    # 分析持仓
    today = datetime.now().strftime('%Y-%m-%d')
    position_analysis = []
    for pos in portfolio['positions']:
        analysis = analyze_position(pos, predictions_df, today)
        position_analysis.append(analysis)
    
    # 生成报告
    print("\n")
    report = generate_report(portfolio, predictions_df, position_analysis)
    print(report)
    
    # 保存报告到文件
    report_path = os.path.join(os.path.dirname(__file__), 'latest_report.txt')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"\n📄 报告已保存到: {report_path}")


if __name__ == '__main__':
    main()

