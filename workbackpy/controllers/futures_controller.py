from services.futures_service import FuturesService
from datetime import datetime, timedelta

class FuturesController:
    """期货控制器"""
    
    def __init__(self):
        self.futures_service = FuturesService()
    
    def get_contracts(self):
        """获取期货合约列表"""
        try:
            contracts = self.futures_service.get_contracts()
            return contracts
        except Exception as e:
            raise Exception(f"获取合约列表失败: {str(e)}")
    
    def get_history(self, symbol: str, period: str = "daily", 
                   start_date: str = None, end_date: str = None):
        """获取期货历史数据"""
        try:
            # 参数验证
            if not symbol:
                raise ValueError("合约代码不能为空")
            
            # 如果没有指定日期范围，默认最近一个月
            if not start_date or not end_date:
                end_dt = datetime.now()
                start_dt = end_dt - timedelta(days=30)
                start_date = start_dt.strftime("%Y%m%d")
                end_date = end_dt.strftime("%Y%m%d")
            
            # 验证周期参数
            valid_periods = ["daily", "weekly", "monthly"]
            if period not in valid_periods:
                raise ValueError(f"无效的周期参数，必须是: {', '.join(valid_periods)}")
            
            # 获取历史数据
            data = self.futures_service.get_futures_history(
                symbol=symbol,
                period=period,
                start_date=start_date,
                end_date=end_date
            )
            
            return {
                "symbol": symbol,
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "data": data,
                "total": len(data)
            }
        except Exception as e:
            raise Exception(f"获取历史数据失败: {str(e)}")
    
    def get_period_options(self):
        """获取周期选项"""
        try:
            return self.futures_service.get_period_options()
        except Exception as e:
            raise Exception(f"获取周期选项失败: {str(e)}")
    
    def refresh_contracts(self):
        """手动刷新合约数据"""
        try:
            contracts_data = self.futures_service.fetch_and_save_contracts()
            if contracts_data:
                return {
                    "message": "合约数据刷新成功",
                    "update_time": contracts_data["update_time"],
                    "count": len(contracts_data["contracts"])
                }
            else:
                raise Exception("刷新合约数据失败")
        except Exception as e:
            raise Exception(f"刷新合约数据失败: {str(e)}") 