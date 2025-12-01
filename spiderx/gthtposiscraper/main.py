# 禁用 requests 内部 urllib3 的警告（macOS 用 LibreSSL 而非 OpenSSL，不影响功能）
import warnings
warnings.filterwarnings('ignore', module='urllib3')

import requests
import json
from datetime import datetime
from typing import Dict, List, Any
import pymysql

# 数据库配置
DB_CONFIG = {
    'host': 'rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'ysd',
    'password': 'Yan1234567',
    'database': 'futures',
    'charset': 'utf8mb4'
}


def fetch_today_positions():
    """
    获取当天的国泰君安持仓数据
    
    Returns:
        dict: 响应的JSON数据，失败返回None
    """
    url = 'https://www.jiaoyikecha.com/ajax/broker_positions.php?v=8bcd6872'
    
    # 获取当天日期
    today = datetime.now().strftime('%Y-%m-%d')
    # 基本请求头，不包含登陆信息
    headers = {
        'accept': '*/*',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cache-control': 'no-cache',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'origin': 'https://www.jiaoyikecha.com',
        'pragma': 'no-cache',
        'referer': 'https://www.jiaoyikecha.com/',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36',
        'x-requested-with': 'XMLHttpRequest'
    }
    
    # POST 数据
    data = {
        'date': today,
        'broker': '国泰君安'
    }
    
    try:
        print(f"正在请求 {today} 的数据...")
        response = requests.post(url, headers=headers, data=data, timeout=10)
        
        print(f"  状态码: {response.status_code}")
        
        if response.status_code == 200:
            try:
                json_data = response.json()
                print(f"  ✓ 数据获取成功")
                return json_data
            except json.JSONDecodeError:
                print(f"  ✗ 响应不是有效的 JSON 格式")
                return None
        else:
            print(f"  ✗ 请求失败，状态码: {response.status_code}")
            return None
        
    except requests.exceptions.RequestException as e:
        print(f"  ✗ 请求异常: {e}")
        return None


def calculate_position_change(contracts: List[Dict]) -> Dict[str, Any]:
    """计算某个品种的增仓数据"""
    total_buy = 0
    total_ss = 0
    total_buy_chge = 0
    total_ss_chge = 0
    
    # 汇总所有合约
    for contract in contracts:
        total_buy += contract.get('buy', 0)
        total_ss += contract.get('ss', 0)
        total_buy_chge += contract.get('buy_chge', 0)
        total_ss_chge += contract.get('ss_chge', 0)
    
    # 净持仓 = 多头 - 空头（正数为净多，负数为净空）
    net_position = total_buy - total_ss
    
    # 净增仓 = 多头增仓 - 空头增仓（正数表示增加多头/减少空头）
    net_change = total_buy_chge - total_ss_chge
    
    # 增仓比例计算逻辑：
    # 如果净增仓 > 0（净增持多头），用 |净增仓| / 多头总持仓
    # 如果净增仓 < 0（净增持空头），用 |净增仓| / 空头总持仓
    change_ratio = 0
    if net_change > 0 and total_buy > 0:
        # 净增持多头，除以多头总持仓
        change_ratio = abs(net_change) / total_buy * 100
    elif net_change < 0 and total_ss > 0:
        # 净增持空头，除以空头总持仓
        change_ratio = abs(net_change) / total_ss * 100
    
    return {
        'total_buy': total_buy,
        'total_ss': total_ss,
        'net_position': net_position,
        'net_change': net_change,
        'change_ratio': change_ratio,
        'is_net_long': net_position > 0,
        'is_increasing': net_change > 0,  # true表示增加多头或减少空头
    }


def analyze_today_data(data: Dict) -> List[Dict[str, Any]]:
    """分析当天数据，返回增仓比例前三大的进攻品种"""
    if not data or 'data' not in data:
        return []
    
    positions = data['data']['positions']
    date = data['data']['date']
    results = []
    
    # 处理positions可能是列表或字典的情况
    if isinstance(positions, list):
        # 如果是列表，需要按品种分组
        positions_dict = {}
        for item in positions:
            name = item.get('name', '未知')
            if name not in positions_dict:
                positions_dict[name] = []
            positions_dict[name].append(item)
        positions = positions_dict
    
    # 遍历所有品种
    for name, contracts in positions.items():
        stats = calculate_position_change(contracts)
        family = contracts[0].get('family', '未知') if contracts else '未知'
        
        # 过滤掉净持仓绝对值小于1000的数据
        if abs(stats['net_position']) < 1000:
            continue
        
        # 只统计方向一致的情况（进攻）：
        # 净多时只统计净增仓为正（多头进攻）
        # 净空时只统计净增仓为负（空头进攻）
        # 不考虑多头撤退和空头撤退的情况
        if stats['net_position'] > 0 and stats['net_change'] <= 0:
            continue  # 净多但净增仓为负或零，跳过（多头撤退）
        if stats['net_position'] < 0 and stats['net_change'] >= 0:
            continue  # 净空但净增仓为正或零，跳过（空头撤退）
        
        results.append({
            'date': date,
            'name': name,
            'family': family,
            **stats
        })
    
    # 找出增仓比例前三大的品种
    if not results:
        return []
    
    results.sort(key=lambda x: x['change_ratio'], reverse=True)
    return results[:3]  # 返回增仓比例前三大的品种


def print_top3_result(top3: List[Dict[str, Any]]):
    """打印前3大进攻品种"""
    if not top3:
        return
    
    print(f"\n[今日前3大进攻品种]")
    for i, item in enumerate(top3, 1):
        direction = "净多" if item['is_net_long'] else "净空"
        change_type = "增多/减空" if item['is_increasing'] else "减多/增空"
        print(f"\nTop{i}: {item['name']} ({item['family']})")
        print(f"  {direction} | {change_type} | 增仓比例: {item['change_ratio']:.2f}%")
        print(f"  净持仓: {item['net_position']:,} | 净增仓: {item['net_change']:,}")


def save_to_database(top3: List[Dict[str, Any]]):
    """将数据保存到数据库"""
    if not top3:
        print("  ⚠ 无有效的数据需要保存到数据库")
        return False
    
    try:
        # 连接数据库
        connection = pymysql.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # 生成当前时间戳（秒级）
        ctime = int(datetime.now().timestamp())
        
        # 生成标题：例如"2025年11月21日国泰君安持仓变化日报"
        date_str = datetime.now().strftime('%Y年%m月%d日')
        title = f"{date_str}国泰君安持仓变化日报"
        
        # 准备content（JSON字符串）
        output_data = {
            'date': top3[0]['date'] if top3 else datetime.now().strftime('%Y-%m-%d'),
            'top3': top3
        }
        content = json.dumps(output_data, ensure_ascii=False)
        
        # 插入news_red_telegraph表
        insert_news_sql = """
            INSERT INTO news_red_telegraph 
            (ctime, title, content, message_score, message_label, message_type)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(insert_news_sql, (ctime, title, content, 7, 'hard', '持仓变化'))
        
        # 获取插入的news_id
        news_id = cursor.lastrowid
        
        # 插入news_process_tracking表
        insert_tracking_sql = """
            INSERT INTO news_process_tracking 
            (news_id, ctime)
            VALUES (%s, %s)
        """
        cursor.execute(insert_tracking_sql, (news_id, ctime))
        
        # 提交事务
        connection.commit()
        
        print(f"\n✓ 数据已保存到数据库")
        print(f"  news_id: {news_id}")
        print(f"  title: {title}")
        print(f"  ctime: {ctime}")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Exception as e:
        print(f"\n✗ 数据库保存失败: {e}")
        if 'connection' in locals():
            connection.rollback()
            connection.close()
        return False


def main():
    """主函数：获取当天数据并分析"""
    print("=" * 60)
    print("国泰君安当日最大增仓品种分析")
    print("=" * 60)
    print()
    
    # 获取当天数据
    data = fetch_today_positions()
    
    if not data:
        print("\n✗ 数据获取失败")
        return
    
    # 分析数据，获取前3大进攻品种
    print("\n正在分析数据...")
    top3 = analyze_today_data(data)
    
    if not top3:
        print("  ⚠ 今日没有符合条件的进攻品种")
        return
    
    # 打印分析结果
    print_top3_result(top3)
    
    # 保存结果到数据库
    save_to_database(top3)
    
    print("\n" + "=" * 60)
    print("分析完成！")
    print("=" * 60)


if __name__ == '__main__':
    main()