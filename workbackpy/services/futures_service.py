import akshare as ak
import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd

class FuturesService:
    """期货数据服务"""
    
    DATA_DIR = "data"
    CONTRACTS_FILE = "futures_contracts.json"
    
    def __init__(self):
        # 确保数据目录存在
        if not os.path.exists(self.DATA_DIR):
            os.makedirs(self.DATA_DIR)
    
    def get_contracts_file_path(self):
        """获取合约文件路径"""
        return os.path.join(self.DATA_DIR, self.CONTRACTS_FILE)
    
    def fetch_and_save_contracts(self):
        """获取并保存期货合约数据"""
        try:
            # 获取期货合约表
            contracts_df = ak.futures_hist_table_em()
            
            # 转换为字典格式
            contracts_data = {
                "update_time": datetime.now().isoformat(),
                "contracts": []
            }
            
            for _, row in contracts_df.iterrows():
                contract = {
                    "exchange": row.iloc[0],  # 交易所
                    "name": row.iloc[1],      # 合约名称
                    "symbol": row.iloc[2]     # 合约代码
                }
                contracts_data["contracts"].append(contract)
            
            # 保存到文件
            with open(self.get_contracts_file_path(), 'w', encoding='utf-8') as f:
                json.dump(contracts_data, f, ensure_ascii=False, indent=2)
            
            return contracts_data
        except Exception as e:
            print(f"获取期货合约数据失败: {str(e)}")
            return None
    
    def get_contracts(self):
        """获取期货合约列表"""
        try:
            # 检查文件是否存在且是今天的数据
            file_path = self.get_contracts_file_path()
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 检查数据是否是今天的
                update_time = datetime.fromisoformat(data["update_time"])
                if update_time.date() == datetime.now().date():
                    return data["contracts"]
            
            # 数据不存在或过期，重新获取
            new_data = self.fetch_and_save_contracts()
            return new_data["contracts"] if new_data else []
        except Exception as e:
            print(f"获取合约列表失败: {str(e)}")
            return []
    
    def get_futures_history(self, symbol: str, period: str = "daily", 
                           start_date: str = None, end_date: str = None):
        """获取期货历史数据"""
        try:
            # 如果需要计算日增仓，需要往前多取一天数据
            actual_start_date = start_date
            if start_date:
                start_dt = datetime.strptime(start_date, "%Y%m%d")
                prev_day = start_dt - timedelta(days=1)
                actual_start_date = prev_day.strftime("%Y%m%d")
            
            # 获取历史数据
            df = ak.futures_hist_em(
                symbol=symbol, 
                period=period,
                start_date=actual_start_date,
                end_date=end_date
            )
            # 打印一下df
            print(df)

            
            if df.empty:
                return []
            
            # 调试信息：打印DataFrame结构
            print(f"DataFrame columns: {df.columns.tolist()}")
            print(f"DataFrame index type: {type(df.index)}")
            if len(df) > 0:
                print(f"First row sample: {dict(df.iloc[0])}")
                if hasattr(df.index[0], 'strftime'):
                    print(f"Index first element (formatted): {df.index[0].strftime('%Y-%m-%d')}")
                else:
                    print(f"Index first element: {df.index[0]}")
            
            # 转换为列表格式并计算日增仓
            result = []
            prev_position = None
            
            for i, (_, row) in enumerate(df.iterrows()):
                # 计算日增仓
                current_position = row['持仓量']
                daily_change = ""
                if prev_position is not None:
                    change = current_position - prev_position
                    if change > 0:
                        daily_change = f"增仓{change}"
                    elif change < 0:
                        daily_change = f"减仓{abs(change)}"
                    else:
                        daily_change = "持平"
                
                # 如果指定了开始日期，跳过第一天（用于计算的前一天）
                if start_date and i == 0 and actual_start_date != start_date:
                    prev_position = current_position
                    continue
                
                # 处理日期格式 - 修复时间显示问题
                try:
                    # 优先从时间列获取数据
                    if '时间' in row and pd.notna(row['时间']):
                        if hasattr(row['时间'], 'strftime'):
                            # pandas Timestamp 或 datetime 对象
                            date_str = row['时间'].strftime("%Y-%m-%d")
                        else:
                            # 字符串格式
                            date_str = str(row['时间'])
                    else:
                        # 如果时间列没有数据，使用DataFrame的索引
                        # DataFrame的索引通常是日期
                        if hasattr(row.name, 'strftime'):
                            date_str = row.name.strftime("%Y-%m-%d")
                        else:
                            date_str = str(row.name)
                except Exception:
                    # 兜底处理
                    date_str = f"第{i+1}天"
                
                record = {
                    "时间": date_str,
                    "开盘": int(row['开盘']),
                    "最高": int(row['最高']),
                    "最低": int(row['最低']),
                    "收盘": int(row['收盘']),
                    "涨跌": int(row['涨跌']),
                    "涨跌幅": round(row['涨跌幅'], 2),
                    "成交量": self._format_volume(row['成交量']),
                    "成交额": int(row['成交额']),
                    "持仓量": self._format_volume(current_position),
                    "日增仓": daily_change
                }
                result.append(record)
                prev_position = current_position
            
            return result
        except Exception as e:
            print(f"获取期货历史数据失败: {str(e)}")
            return []
    
    def _format_volume(self, volume):
        """格式化成交量/持仓量显示"""
        if volume >= 10000:
            return f"{volume/10000:.2f}万"
        else:
            return str(int(volume))
    
    def get_period_options(self):
        """获取周期选项"""
        return [
            {"value": "daily", "label": "日线"},
            {"value": "weekly", "label": "周线"},
            {"value": "monthly", "label": "月线"}
        ] 