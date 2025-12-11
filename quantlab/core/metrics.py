"""
绩效指标计算
"""
from typing import Optional


def extract_metrics(strategy_result) -> dict:
    """
    从回测结果提取关键指标
    
    Args:
        strategy_result: cerebro.run() 返回的策略实例
    
    Returns:
        dict: 绩效指标字典
    """
    metrics = {}
    
    # Sharpe Ratio
    try:
        sharpe = strategy_result.analyzers.sharpe.get_analysis()
        metrics['sharpe_ratio'] = sharpe.get('sharperatio', None)
    except:
        metrics['sharpe_ratio'] = None
    
    # Drawdown
    try:
        dd = strategy_result.analyzers.drawdown.get_analysis()
        metrics['max_drawdown'] = dd.get('max', {}).get('drawdown', None)
        metrics['max_drawdown_len'] = dd.get('max', {}).get('len', None)
    except:
        metrics['max_drawdown'] = None
        metrics['max_drawdown_len'] = None
    
    # Returns
    try:
        returns = strategy_result.analyzers.returns.get_analysis()
        metrics['total_return'] = returns.get('rtot', None)
        metrics['avg_return'] = returns.get('ravg', None)
        metrics['annual_return'] = returns.get('rnorm', None)
    except:
        metrics['total_return'] = None
        metrics['avg_return'] = None
        metrics['annual_return'] = None
    
    # Trades
    try:
        trades = strategy_result.analyzers.trades.get_analysis()
        metrics['total_trades'] = trades.get('total', {}).get('total', 0)
        metrics['won_trades'] = trades.get('won', {}).get('total', 0)
        metrics['lost_trades'] = trades.get('lost', {}).get('total', 0)
        
        # 盈利交易统计
        won = trades.get('won', {})
        metrics['won_avg_pnl'] = won.get('pnl', {}).get('average', 0)
        metrics['won_max_pnl'] = won.get('pnl', {}).get('max', 0)
        
        # 亏损交易统计
        lost = trades.get('lost', {})
        metrics['lost_avg_pnl'] = lost.get('pnl', {}).get('average', 0)
        metrics['lost_max_pnl'] = lost.get('pnl', {}).get('max', 0)
        
        # 盈亏比
        if metrics['lost_avg_pnl'] != 0 and metrics['lost_avg_pnl'] is not None:
            metrics['profit_factor'] = abs(metrics['won_avg_pnl'] / metrics['lost_avg_pnl'])
        else:
            metrics['profit_factor'] = None
        
    except:
        metrics['total_trades'] = 0
        metrics['won_trades'] = 0
        metrics['lost_trades'] = 0
        metrics['won_avg_pnl'] = 0
        metrics['lost_avg_pnl'] = 0
        metrics['profit_factor'] = None
    
    # 胜率
    if metrics['total_trades'] > 0:
        metrics['win_rate'] = metrics['won_trades'] / metrics['total_trades']
    else:
        metrics['win_rate'] = 0
    
    # SQN (System Quality Number)
    try:
        sqn = strategy_result.analyzers.sqn.get_analysis()
        metrics['sqn'] = sqn.get('sqn', None)
    except:
        metrics['sqn'] = None
    
    return metrics


def print_metrics(metrics: dict, title: str = "绩效报告"):
    """打印绩效报告"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)
    
    # 收益指标
    print("\n【收益指标】")
    if metrics.get('total_return') is not None:
        print(f"  总收益率:      {metrics['total_return'] * 100:>10.2f}%")
    if metrics.get('annual_return') is not None:
        print(f"  年化收益率:    {metrics['annual_return'] * 100:>10.2f}%")
    
    # 风险指标
    print("\n【风险指标】")
    if metrics.get('max_drawdown') is not None:
        print(f"  最大回撤:      {metrics['max_drawdown']:>10.2f}%")
    if metrics.get('max_drawdown_len') is not None:
        print(f"  最长回撤期:    {int(metrics['max_drawdown_len']):>10d} 天")
    
    # 风险调整收益
    print("\n【风险调整收益】")
    if metrics.get('sharpe_ratio') is not None:
        print(f"  Sharpe Ratio:  {metrics['sharpe_ratio']:>10.3f}")
    if metrics.get('sqn') is not None:
        print(f"  SQN:           {metrics['sqn']:>10.3f}")
    
    # 交易统计
    print("\n【交易统计】")
    print(f"  总交易次数:    {metrics.get('total_trades', 0):>10d}")
    print(f"  盈利次数:      {metrics.get('won_trades', 0):>10d}")
    print(f"  亏损次数:      {metrics.get('lost_trades', 0):>10d}")
    print(f"  胜率:          {metrics.get('win_rate', 0) * 100:>10.1f}%")
    
    if metrics.get('profit_factor') is not None:
        print(f"  盈亏比:        {metrics['profit_factor']:>10.2f}")
    if metrics.get('won_avg_pnl'):
        print(f"  平均盈利:      {metrics['won_avg_pnl']:>10.2f}")
    if metrics.get('lost_avg_pnl'):
        print(f"  平均亏损:      {metrics['lost_avg_pnl']:>10.2f}")
    
    print("=" * 60)


def compare_metrics(metrics_list: list, labels: list = None) -> None:
    """
    比较多个策略的绩效
    
    Args:
        metrics_list: 绩效指标列表
        labels: 策略标签列表
    """
    import pandas as pd
    
    if labels is None:
        labels = [f"策略{i+1}" for i in range(len(metrics_list))]
    
    # 选择关键指标进行比较
    key_metrics = [
        'total_return', 'annual_return', 'sharpe_ratio', 
        'max_drawdown', 'win_rate', 'total_trades', 'profit_factor', 'sqn'
    ]
    
    data = {}
    for i, (m, label) in enumerate(zip(metrics_list, labels)):
        data[label] = {k: m.get(k) for k in key_metrics}
    
    df = pd.DataFrame(data).T
    
    # 格式化显示
    format_dict = {
        'total_return': lambda x: f"{x*100:.2f}%" if x else "N/A",
        'annual_return': lambda x: f"{x*100:.2f}%" if x else "N/A",
        'sharpe_ratio': lambda x: f"{x:.3f}" if x else "N/A",
        'max_drawdown': lambda x: f"{x:.2f}%" if x else "N/A",
        'win_rate': lambda x: f"{x*100:.1f}%" if x else "N/A",
        'total_trades': lambda x: f"{int(x)}" if x else "0",
        'profit_factor': lambda x: f"{x:.2f}" if x else "N/A",
        'sqn': lambda x: f"{x:.2f}" if x else "N/A",
    }
    
    print("\n" + "=" * 80)
    print(" 策略对比")
    print("=" * 80)
    print(df.to_string())
    print("=" * 80)
    
    return df


def metrics_to_dataframe(metrics_list: list, params_list: list = None):
    """
    将多组绩效指标转换为 DataFrame
    
    Args:
        metrics_list: 绩效指标列表
        params_list: 参数列表（可选）
    
    Returns:
        pd.DataFrame
    """
    import pandas as pd
    
    df = pd.DataFrame(metrics_list)
    
    if params_list:
        params_df = pd.DataFrame(params_list)
        df = pd.concat([params_df, df], axis=1)
    
    return df
