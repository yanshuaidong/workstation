#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试期货服务时间格式修复
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.futures_service import FuturesService

def test_futures_time_format():
    """测试期货数据时间格式"""
    service = FuturesService()
    
    # 测试获取热卷主连最近几天的数据
    print("=== 测试期货时间格式 ===")
    
    # 获取最近5天的热卷主连数据
    data = service.get_futures_history("HC9999", period="daily")
    
    if data:
        print(f"获取到 {len(data)} 条数据")
        print("\n前3条数据的时间格式:")
        for i, record in enumerate(data[:3]):
            print(f"第{i+1}条: 时间={record['时间']}, 收盘={record['收盘']}")
    else:
        print("未获取到数据")

if __name__ == "__main__":
    test_futures_time_format() 