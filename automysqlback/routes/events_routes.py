"""
期货事件管理模块
包含：事件增删改查
数据来源：阿里云 MySQL 数据库 futures_events 表
"""

from flask import Blueprint, request, jsonify
import pymysql
from datetime import datetime
import logging

# 创建蓝图
events_bp = Blueprint('events', __name__)

logger = logging.getLogger(__name__)

# ========== 事件管理API ==========

@events_bp.route('/events/list', methods=['GET'])
def get_events_list():
    """
    获取指定品种的事件列表
    参数：
    - symbol: 合约代码（必填）
    - start_date: 开始日期（可选）
    - end_date: 结束日期（可选）
    """
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    symbol = request.args.get('symbol')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    if not symbol:
        return jsonify({
            'code': 1,
            'message': '缺少合约代码参数 symbol'
        })
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 构建查询SQL
        sql = """
            SELECT 
                id,
                symbol,
                event_date,
                title,
                content,
                outlook,
                strength,
                created_at,
                updated_at
            FROM futures_events
            WHERE symbol = %s
        """
        params = [symbol]
        
        if start_date:
            sql += " AND event_date >= %s"
            params.append(start_date)
        
        if end_date:
            sql += " AND event_date <= %s"
            params.append(end_date)
        
        sql += " ORDER BY event_date DESC, created_at DESC"
        
        cursor.execute(sql, params)
        events = cursor.fetchall()
        
        # 格式化日期
        formatted_events = []
        for event in events:
            formatted_events.append({
                'id': event['id'],
                'symbol': event['symbol'],
                'event_date': event['event_date'].strftime('%Y-%m-%d') if event['event_date'] else None,
                'title': event['title'],
                'content': event['content'],
                'outlook': event['outlook'],
                'strength': event['strength'],
                'created_at': event['created_at'].strftime('%Y-%m-%d %H:%M:%S') if event['created_at'] else None,
                'updated_at': event['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if event['updated_at'] else None
            })
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'events': formatted_events,
                'total': len(formatted_events)
            }
        })
        
    except Exception as e:
        logger.error(f"获取事件列表失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()


@events_bp.route('/events/create', methods=['POST'])
def create_event():
    """
    创建新事件
    请求体：
    {
        "symbol": "au",
        "event_date": "2024-12-21",
        "title": "美联储降息25个基点",
        "content": "美联储宣布降息25个基点，符合市场预期...",
        "outlook": "bullish",  // bullish/bearish/uncertain/ranging
        "strength": 8  // 1-10
    }
    """
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    data = request.get_json()
    
    # 参数验证
    required_fields = ['symbol', 'event_date', 'title']
    for field in required_fields:
        if not data.get(field):
            return jsonify({
                'code': 1,
                'message': f'缺少必填参数: {field}'
            })
    
    # 验证 outlook 值
    valid_outlooks = ['bullish', 'bearish', 'uncertain', 'ranging', None, '']
    if data.get('outlook') and data.get('outlook') not in valid_outlooks:
        return jsonify({
            'code': 1,
            'message': 'outlook 参数值无效，应为 bullish/bearish/uncertain/ranging'
        })
    
    # 验证 strength 值
    strength = data.get('strength')
    if strength is not None:
        try:
            strength = int(strength)
            if strength < 1 or strength > 10:
                return jsonify({
                    'code': 1,
                    'message': 'strength 参数值应在 1-10 之间'
                })
        except (ValueError, TypeError):
            return jsonify({
                'code': 1,
                'message': 'strength 参数值无效'
            })
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO futures_events 
            (symbol, event_date, title, content, outlook, strength)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            data['symbol'].lower(),  # 统一转小写
            data['event_date'],
            data['title'],
            data.get('content', ''),
            data.get('outlook') if data.get('outlook') else None,
            strength
        ))
        
        conn.commit()
        new_id = cursor.lastrowid
        
        return jsonify({
            'code': 0,
            'message': '创建成功',
            'data': {
                'id': new_id
            }
        })
        
    except Exception as e:
        logger.error(f"创建事件失败: {e}")
        conn.rollback()
        return jsonify({
            'code': 1,
            'message': f'创建失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()


@events_bp.route('/events/detail/<int:event_id>', methods=['GET'])
def get_event_detail(event_id):
    """获取单个事件详情"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("""
            SELECT 
                id,
                symbol,
                event_date,
                title,
                content,
                outlook,
                strength,
                created_at,
                updated_at
            FROM futures_events
            WHERE id = %s
        """, (event_id,))
        
        event = cursor.fetchone()
        
        if not event:
            return jsonify({
                'code': 1,
                'message': f'事件 ID {event_id} 不存在'
            })
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'id': event['id'],
                'symbol': event['symbol'],
                'event_date': event['event_date'].strftime('%Y-%m-%d') if event['event_date'] else None,
                'title': event['title'],
                'content': event['content'],
                'outlook': event['outlook'],
                'strength': event['strength'],
                'created_at': event['created_at'].strftime('%Y-%m-%d %H:%M:%S') if event['created_at'] else None,
                'updated_at': event['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if event['updated_at'] else None
            }
        })
        
    except Exception as e:
        logger.error(f"获取事件详情失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()


@events_bp.route('/events/update/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    """
    更新事件
    请求体：（所有字段可选，只更新传入的字段）
    {
        "event_date": "2024-12-21",
        "title": "美联储降息25个基点",
        "content": "...",
        "outlook": "bullish",
        "strength": 8
    }
    """
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    data = request.get_json()
    
    if not data:
        return jsonify({
            'code': 1,
            'message': '请求体不能为空'
        })
    
    # 验证 outlook 值
    if 'outlook' in data and data['outlook']:
        valid_outlooks = ['bullish', 'bearish', 'uncertain', 'ranging']
        if data['outlook'] not in valid_outlooks:
            return jsonify({
                'code': 1,
                'message': 'outlook 参数值无效，应为 bullish/bearish/uncertain/ranging'
            })
    
    # 验证 strength 值
    if 'strength' in data and data['strength'] is not None:
        try:
            strength = int(data['strength'])
            if strength < 1 or strength > 10:
                return jsonify({
                    'code': 1,
                    'message': 'strength 参数值应在 1-10 之间'
                })
            data['strength'] = strength
        except (ValueError, TypeError):
            return jsonify({
                'code': 1,
                'message': 'strength 参数值无效'
            })
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 先检查事件是否存在
        cursor.execute("SELECT id FROM futures_events WHERE id = %s", (event_id,))
        if not cursor.fetchone():
            return jsonify({
                'code': 1,
                'message': f'事件 ID {event_id} 不存在'
            })
        
        # 构建更新SQL
        update_fields = []
        params = []
        
        allowed_fields = ['event_date', 'title', 'content', 'outlook', 'strength']
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                # outlook 为空字符串时转为 None
                if field == 'outlook' and data[field] == '':
                    params.append(None)
                else:
                    params.append(data[field])
        
        if not update_fields:
            return jsonify({
                'code': 1,
                'message': '没有可更新的字段'
            })
        
        params.append(event_id)
        
        cursor.execute(f"""
            UPDATE futures_events 
            SET {', '.join(update_fields)}
            WHERE id = %s
        """, params)
        
        conn.commit()
        
        return jsonify({
            'code': 0,
            'message': '更新成功'
        })
        
    except Exception as e:
        logger.error(f"更新事件失败: {e}")
        conn.rollback()
        return jsonify({
            'code': 1,
            'message': f'更新失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()


@events_bp.route('/events/delete/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    """删除事件"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 先检查事件是否存在
        cursor.execute("SELECT id, title FROM futures_events WHERE id = %s", (event_id,))
        event = cursor.fetchone()
        
        if not event:
            return jsonify({
                'code': 1,
                'message': f'事件 ID {event_id} 不存在'
            })
        
        cursor.execute("DELETE FROM futures_events WHERE id = %s", (event_id,))
        conn.commit()
        
        return jsonify({
            'code': 0,
            'message': '删除成功',
            'data': {
                'deleted_id': event_id,
                'deleted_title': event[1]
            }
        })
        
    except Exception as e:
        logger.error(f"删除事件失败: {e}")
        conn.rollback()
        return jsonify({
            'code': 1,
            'message': f'删除失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

