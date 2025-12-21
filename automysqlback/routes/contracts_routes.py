"""
合约管理模块
包含：合约列表查询、历史数据查询
数据来源：阿里云 MySQL 数据库
"""

from flask import Blueprint, request, jsonify
import pymysql
from datetime import datetime, timedelta
import logging

# 创建蓝图
contracts_bp = Blueprint('contracts', __name__)

logger = logging.getLogger(__name__)

# ========== API接口 ==========

@contracts_bp.route('/contracts/list', methods=['GET'])
def get_contracts_list():
    """获取数据库中的合约列表"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("""
            SELECT symbol, name, exchange, is_active 
            FROM contracts_main 
            WHERE is_active = 1 
            ORDER BY symbol
        """)
        
        contracts = cursor.fetchall()
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'contracts': contracts,
                'total': len(contracts)
            }
        })
        
    except Exception as e:
        logger.error(f"获取合约列表失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

@contracts_bp.route('/history/data', methods=['GET'])
def get_history_data():
    """获取指定合约的历史数据"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    symbol = request.args.get('symbol')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not symbol:
        return jsonify({
            'code': 1,
            'message': '缺少合约代码参数'
        })
    
    # 设置默认日期范围（最近一个月）
    if not start_date or not end_date:
        end_date = datetime.now().date().strftime('%Y-%m-%d')
        start_date = (datetime.now().date() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 验证合约是否存在
        cursor.execute("SELECT name FROM contracts_main WHERE symbol = %s AND is_active = 1", (symbol,))
        contract_info = cursor.fetchone()
        
        if not contract_info:
            return jsonify({
                'code': 1,
                'message': f'合约 {symbol} 不存在或未激活'
            })
        
        # 查询历史数据
        table_name = f"hist_{symbol}"
        cursor.execute(f"""
            SELECT 
                trade_date,
                open_price,
                high_price,
                low_price,
                close_price,
                volume,
                open_interest,
                turnover,
                price_change,
                change_pct,
                macd_dif,
                macd_dea,
                macd_histogram,
                rsi_14,
                kdj_k,
                kdj_d,
                kdj_j,
                bb_upper,
                bb_middle,
                bb_lower,
                bb_width,
                recommendation
            FROM {table_name}
            WHERE trade_date >= %s AND trade_date <= %s
            ORDER BY trade_date DESC
            LIMIT 500
        """, (start_date, end_date))
        
        history_data = cursor.fetchall()
        
        # 转换数据格式
        formatted_data = []
        for row in history_data:
            formatted_data.append({
                'date': row['trade_date'].strftime('%Y-%m-%d') if row['trade_date'] else None,
                'price': {
                    'open': float(row['open_price']) if row['open_price'] else 0,
                    'high': float(row['high_price']) if row['high_price'] else 0,
                    'low': float(row['low_price']) if row['low_price'] else 0,
                    'close': float(row['close_price']) if row['close_price'] else 0
                },
                'volume': {
                    'shares': int(row['volume']) if row['volume'] else 0,
                    'open_interest': int(row['open_interest']) if row['open_interest'] else 0,
                    'turnover': float(row['turnover']) if row['turnover'] else 0
                },
                'change': {
                    'price_change': float(row['price_change']) if row['price_change'] else 0,
                    'change_pct': float(row['change_pct']) if row['change_pct'] else 0
                },
                'indicators': {
                    'macd': {
                        'dif': float(row['macd_dif']) if row['macd_dif'] else None,
                        'dea': float(row['macd_dea']) if row['macd_dea'] else None,
                        'histogram': float(row['macd_histogram']) if row['macd_histogram'] else None
                    },
                    'rsi': float(row['rsi_14']) if row['rsi_14'] else None,
                    'kdj': {
                        'k': float(row['kdj_k']) if row['kdj_k'] else None,
                        'd': float(row['kdj_d']) if row['kdj_d'] else None,
                        'j': float(row['kdj_j']) if row['kdj_j'] else None
                    },
                    'bollinger': {
                        'upper': float(row['bb_upper']) if row['bb_upper'] else None,
                        'middle': float(row['bb_middle']) if row['bb_middle'] else None,
                        'lower': float(row['bb_lower']) if row['bb_lower'] else None,
                        'width': float(row['bb_width']) if row['bb_width'] else None
                    }
                },
                'recommendation': row['recommendation'] if row['recommendation'] else None,
                # 原始数据用于表格显示
                'raw': {
                    'trade_date': row['trade_date'].strftime('%Y-%m-%d') if row['trade_date'] else '',
                    'open_price': float(row['open_price']) if row['open_price'] else 0,
                    'high_price': float(row['high_price']) if row['high_price'] else 0,
                    'low_price': float(row['low_price']) if row['low_price'] else 0,
                    'close_price': float(row['close_price']) if row['close_price'] else 0,
                    'volume': int(row['volume']) if row['volume'] else 0,
                    'open_interest': int(row['open_interest']) if row['open_interest'] else 0,
                    'turnover': float(row['turnover']) if row['turnover'] else 0,
                    'price_change': float(row['price_change']) if row['price_change'] else 0,
                    'change_pct': float(row['change_pct']) if row['change_pct'] else 0,
                    'macd_dif': float(row['macd_dif']) if row['macd_dif'] else None,
                    'macd_dea': float(row['macd_dea']) if row['macd_dea'] else None,
                    'macd_histogram': float(row['macd_histogram']) if row['macd_histogram'] else None,
                    'rsi_14': float(row['rsi_14']) if row['rsi_14'] else None,
                    'kdj_k': float(row['kdj_k']) if row['kdj_k'] else None,
                    'kdj_d': float(row['kdj_d']) if row['kdj_d'] else None,
                    'kdj_j': float(row['kdj_j']) if row['kdj_j'] else None,
                    'bb_upper': float(row['bb_upper']) if row['bb_upper'] else None,
                    'bb_middle': float(row['bb_middle']) if row['bb_middle'] else None,
                    'bb_lower': float(row['bb_lower']) if row['bb_lower'] else None,
                    'bb_width': float(row['bb_width']) if row['bb_width'] else None,
                    'recommendation': row['recommendation'] if row['recommendation'] else None
                }
            })
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'symbol': symbol,
                'name': contract_info['name'],
                'start_date': start_date,
                'end_date': end_date,
                'total_records': len(formatted_data),
                'data': formatted_data
            }
        })
        
    except Exception as e:
        logger.error(f"获取历史数据失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

