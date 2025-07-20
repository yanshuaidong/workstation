#!/usr/bin/env python3
"""
每日定时任务：更新期货合约数据
可以通过 cron 定时执行此脚本
"""

import sys
import os
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.futures_service import FuturesService

def daily_update_contracts():
    """每日更新期货合约数据"""
    print(f"开始执行每日合约数据更新任务 - {datetime.now()}")
    
    try:
        futures_service = FuturesService()
        result = futures_service.fetch_and_save_contracts()
        
        if result:
            print(f"合约数据更新成功！")
            print(f"更新时间: {result['update_time']}")
            print(f"合约数量: {len(result['contracts'])}")
        else:
            print("合约数据更新失败")
            return False
            
    except Exception as e:
        print(f"合约数据更新异常: {str(e)}")
        return False
    
    print(f"每日合约数据更新任务完成 - {datetime.now()}")
    return True

if __name__ == "__main__":
    success = daily_update_contracts()
    sys.exit(0 if success else 1) 