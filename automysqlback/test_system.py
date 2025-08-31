#!/usr/bin/env python3
"""
期货数据更新系统测试脚本
用于验证系统主要功能是否正常
"""

import requests
import json
import time
import sys

# 配置
BASE_URL = 'http://localhost:7002/api'
HEADERS = {'Content-Type': 'application/json'}

def test_connection():
    """测试服务器连接"""
    try:
        response = requests.get(f"{BASE_URL}/settings", timeout=5)
        if response.status_code == 200:
            print("✓ 服务器连接正常")
            return True
        else:
            print(f"✗ 服务器连接失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ 无法连接到服务器: {e}")
        return False

def test_fetch_contracts():
    """测试获取合约列表"""
    print("\n测试获取公开合约列表...")
    try:
        response = requests.get(f"{BASE_URL}/contracts/fetch-public", timeout=30)
        data = response.json()
        
        if data['code'] == 0:
            print(f"✓ 成功获取合约列表")
            print(f"  总合约数: {data['data']['total']}")
            print(f"  主连合约数: {data['data']['main_contracts']}")
            return True
        else:
            print(f"✗ 获取合约列表失败: {data['message']}")
            return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_upsert_contracts():
    """测试更新合约列表"""
    print("\n测试更新合约列表到数据库...")
    try:
        response = requests.post(f"{BASE_URL}/contracts/upsert-list", headers=HEADERS)
        data = response.json()
        
        if data['code'] == 0:
            print(f"✓ 合约列表更新成功")
            print(f"  新增: {data['data']['new_count']}")
            print(f"  更新: {data['data']['updated_count']}")
            return True
        else:
            print(f"✗ 更新合约列表失败: {data['message']}")
            return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_settings():
    """测试系统设置"""
    print("\n测试系统设置...")
    try:
        # 获取设置
        response = requests.get(f"{BASE_URL}/settings")
        data = response.json()
        
        if data['code'] == 0:
            print("✓ 成功获取系统设置")
            settings = data['data']
            print(f"  自动更新: {settings['auto_update_enabled']}")
            print(f"  并发数: {settings['concurrency']}")
            print(f"  超时时间: {settings['timeout_seconds']}秒")
            
            # 测试更新设置
            test_settings = {
                'concurrency': 3,
                'timeout_seconds': 30
            }
            response = requests.post(f"{BASE_URL}/settings", json=test_settings, headers=HEADERS)
            update_data = response.json()
            
            if update_data['code'] == 0:
                print("✓ 设置更新成功")
                return True
            else:
                print(f"✗ 设置更新失败: {update_data['message']}")
                return False
        else:
            print(f"✗ 获取设置失败: {data['message']}")
            return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_contracts_list():
    """测试获取合约列表"""
    print("\n测试获取数据库中的合约列表...")
    try:
        response = requests.get(f"{BASE_URL}/contracts/list")
        data = response.json()
        
        if data['code'] == 0:
            contracts = data['data']
            print(f"✓ 成功获取合约列表: {len(contracts)} 个合约")
            if contracts:
                print(f"  示例合约: {contracts[0]['name']} ({contracts[0]['symbol']})")
            return True
        else:
            print(f"✗ 获取合约列表失败: {data['message']}")
            return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def test_history_update():
    """测试历史数据更新（小规模测试）"""
    print("\n测试历史数据更新...")
    try:
        # 获取一个合约进行测试
        response = requests.get(f"{BASE_URL}/contracts/list")
        contracts_data = response.json()
        
        if contracts_data['code'] != 0 or not contracts_data['data']:
            print("✗ 没有可用的合约进行测试")
            return False
        
        # 选择第一个合约进行测试
        test_symbol = contracts_data['data'][0]['symbol']
        print(f"  使用合约 {test_symbol} 进行测试")
        
        # 设置小范围的日期（最近7天）
        import datetime
        end_date = datetime.date.today()
        start_date = end_date - datetime.timedelta(days=7)
        
        update_request = {
            'symbols': [test_symbol],
            'date_start': start_date.strftime('%Y-%m-%d'),
            'date_end': end_date.strftime('%Y-%m-%d'),
            'timeout_ms': 30000,
            'concurrency': 1,
            'multithread': False,
            'triggered_by': 'manual'
        }
        
        response = requests.post(f"{BASE_URL}/contracts/update-history", 
                               json=update_request, headers=HEADERS)
        data = response.json()
        
        if data['code'] == 0:
            run_id = data['data']['run_id']
            print(f"✓ 历史数据更新已启动，运行ID: {run_id}")
            
            # 等待一段时间让任务完成
            print("  等待更新完成...")
            time.sleep(10)
            
            # 检查运行状态
            status_response = requests.get(f"{BASE_URL}/runs/{run_id}")
            status_data = status_response.json()
            
            if status_data['code'] == 0:
                run_info = status_data['data']['run_info']
                print(f"  运行状态: {run_info['status']}")
                print(f"  成功: {run_info['success_count']}, 失败: {run_info['fail_count']}")
                return True
            else:
                print(f"✗ 获取运行状态失败: {status_data['message']}")
                return False
        else:
            print(f"✗ 启动历史数据更新失败: {data['message']}")
            return False
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("期货数据更新系统功能测试")
    print("=" * 50)
    
    # 检查服务器是否运行
    if not test_connection():
        print("\n请先启动后端服务器: python app.py")
        sys.exit(1)
    
    # 执行各项测试
    tests = [
        ("系统设置", test_settings),
        ("获取公开合约", test_fetch_contracts),
        ("更新合约列表", test_upsert_contracts),
        ("获取合约列表", test_contracts_list),
        ("历史数据更新", test_history_update),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'-' * 30}")
        print(f"测试: {test_name}")
        print(f"{'-' * 30}")
        
        if test_func():
            passed += 1
            print(f"✓ {test_name} - 通过")
        else:
            print(f"✗ {test_name} - 失败")
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print(f"测试完成: {passed}/{total} 通过")
    if passed == total:
        print("🎉 所有测试通过！系统运行正常")
    else:
        print(f"⚠️ {total - passed} 个测试失败，请检查系统配置")
    print("=" * 50)

if __name__ == '__main__':
    main() 