"""
持仓管理模块
包含：期货持仓的CRUD操作
"""

from flask import Blueprint, request, jsonify
import pymysql
from datetime import datetime
import logging

# 创建蓝图
positions_bp = Blueprint('positions', __name__)

logger = logging.getLogger(__name__)

# ========== 持仓管理API ==========

@positions_bp.route('/positions/list', methods=['GET'])
def get_positions_list():
    """获取持仓列表（支持筛选）"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    # 获取筛选参数
    status = request.args.get('status', '').strip()  # 1=有仓, 0=空仓, 空=全部
    direction = request.args.get('direction', '').strip()  # LONG/SHORT/多/空
    symbol = request.args.get('symbol', '').strip()  # 品种搜索
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 构建WHERE条件
        where_conditions = []
        where_params = []
        
        if status != '':
            where_conditions.append("status = %s")
            where_params.append(int(status))
        
        if direction:
            where_conditions.append("direction = %s")
            where_params.append(direction)
        
        if symbol:
            where_conditions.append("symbol LIKE %s")
            where_params.append(f"%{symbol}%")
        
        # 构建WHERE子句
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 查询持仓列表
        sql = f"""
            SELECT 
                id,
                symbol,
                direction,
                status,
                created_at,
                updated_at
            FROM futures_positions 
            {where_clause}
            ORDER BY updated_at DESC
        """
        
        cursor.execute(sql, where_params)
        positions = cursor.fetchall()
        
        # 格式化数据
        formatted_positions = []
        for pos in positions:
            formatted_positions.append({
                'id': pos['id'],
                'symbol': pos['symbol'],
                'direction': pos['direction'],
                'status': pos['status'],
                'status_text': '有仓' if pos['status'] == 1 else '空仓',
                'created_at': pos['created_at'].strftime('%Y-%m-%d %H:%M:%S') if pos['created_at'] else '',
                'updated_at': pos['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if pos['updated_at'] else ''
            })
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                'positions': formatted_positions,
                'total': len(formatted_positions)
            }
        })
        
    except Exception as e:
        logger.error(f"获取持仓列表失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()


@positions_bp.route('/positions/create', methods=['POST'])
def create_position():
    """创建持仓记录"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    data = request.get_json()
    
    # 验证必填字段
    if not data.get('symbol') or not data.get('direction'):
        return jsonify({
            'code': 1,
            'message': '品种和方向为必填字段'
        })
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT INTO futures_positions 
            (symbol, direction, status)
            VALUES (%s, %s, %s)
        """, (
            data['symbol'].strip(),
            data['direction'].strip(),
            data.get('status', 1)  # 默认有仓
        ))
        
        position_id = cursor.lastrowid
        conn.commit()
        
        return jsonify({
            'code': 0,
            'message': '持仓创建成功',
            'data': {'id': position_id}
        })
        
    except Exception as e:
        logger.error(f"创建持仓失败: {e}")
        conn.rollback()
        return jsonify({
            'code': 1,
            'message': f'创建失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()


@positions_bp.route('/positions/detail/<int:position_id>', methods=['GET'])
def get_position_detail(position_id):
    """获取持仓详情"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("""
            SELECT 
                id, symbol, direction, status, created_at, updated_at
            FROM futures_positions 
            WHERE id = %s
        """, (position_id,))
        
        position = cursor.fetchone()
        
        if not position:
            return jsonify({
                'code': 1,
                'message': '持仓记录不存在'
            })
        
        formatted_data = {
            'id': position['id'],
            'symbol': position['symbol'],
            'direction': position['direction'],
            'status': position['status'],
            'status_text': '有仓' if position['status'] == 1 else '空仓',
            'created_at': position['created_at'].strftime('%Y-%m-%d %H:%M:%S') if position['created_at'] else '',
            'updated_at': position['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if position['updated_at'] else ''
        }
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': formatted_data
        })
        
    except Exception as e:
        logger.error(f"获取持仓详情失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()


@positions_bp.route('/positions/update/<int:position_id>', methods=['PUT'])
def update_position(position_id):
    """更新持仓记录"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 检查持仓是否存在
        cursor.execute("SELECT id FROM futures_positions WHERE id = %s", (position_id,))
        if not cursor.fetchone():
            return jsonify({
                'code': 1,
                'message': '持仓记录不存在'
            })
        
        # 构建更新字段
        update_fields = []
        update_values = []
        
        updatable_fields = ['symbol', 'direction', 'status']
        
        for field in updatable_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                value = data[field]
                if field in ['symbol', 'direction'] and isinstance(value, str):
                    value = value.strip()
                update_values.append(value)
        
        if not update_fields:
            return jsonify({
                'code': 1,
                'message': '没有需要更新的字段'
            })
        
        # 添加updated_at字段更新（自动更新）
        update_values.append(position_id)
        
        # 执行更新
        sql = f"UPDATE futures_positions SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(sql, update_values)
        
        conn.commit()
        
        return jsonify({
            'code': 0,
            'message': '持仓更新成功'
        })
        
    except Exception as e:
        logger.error(f"更新持仓失败: {e}")
        conn.rollback()
        return jsonify({
            'code': 1,
            'message': f'更新失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()


@positions_bp.route('/positions/delete/<int:position_id>', methods=['DELETE'])
def delete_position(position_id):
    """删除持仓记录"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 删除数据库记录
        cursor.execute("DELETE FROM futures_positions WHERE id = %s", (position_id,))
        
        if cursor.rowcount == 0:
            return jsonify({
                'code': 1,
                'message': '持仓记录不存在'
            })
        
        conn.commit()
        
        return jsonify({
            'code': 0,
            'message': '持仓删除成功'
        })
        
    except Exception as e:
        logger.error(f"删除持仓失败: {e}")
        conn.rollback()
        return jsonify({
            'code': 1,
            'message': f'删除失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()


@positions_bp.route('/positions/stats', methods=['GET'])
def get_positions_stats():
    """获取持仓统计信息"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 总持仓数
        cursor.execute("SELECT COUNT(*) as total FROM futures_positions")
        total = cursor.fetchone()['total']
        
        # 有仓数量
        cursor.execute("SELECT COUNT(*) as hold_count FROM futures_positions WHERE status = 1")
        hold_count = cursor.fetchone()['hold_count']
        
        # 空仓数量
        cursor.execute("SELECT COUNT(*) as flat_count FROM futures_positions WHERE status = 0")
        flat_count = cursor.fetchone()['flat_count']
        
        # 多头数量
        cursor.execute("SELECT COUNT(*) as long_count FROM futures_positions WHERE direction IN ('LONG', '多') AND status = 1")
        long_count = cursor.fetchone()['long_count']
        
        # 空头数量
        cursor.execute("SELECT COUNT(*) as short_count FROM futures_positions WHERE direction IN ('SHORT', '空') AND status = 1")
        short_count = cursor.fetchone()['short_count']
        
        return jsonify({
            'code': 0,
            'message': '统计信息获取成功',
            'data': {
                'total': total,
                'hold_count': hold_count,
                'flat_count': flat_count,
                'long_count': long_count,
                'short_count': short_count
            }
        })
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'获取统计信息失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()


@positions_bp.route('/positions/toggle-status/<int:position_id>', methods=['POST'])
def toggle_position_status(position_id):
    """切换持仓状态（有仓/空仓）"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 获取当前状态
        cursor.execute("SELECT status FROM futures_positions WHERE id = %s", (position_id,))
        position = cursor.fetchone()
        
        if not position:
            return jsonify({
                'code': 1,
                'message': '持仓记录不存在'
            })
        
        # 切换状态
        new_status = 0 if position['status'] == 1 else 1
        
        cursor.execute("""
            UPDATE futures_positions 
            SET status = %s 
            WHERE id = %s
        """, (new_status, position_id))
        
        conn.commit()
        
        return jsonify({
            'code': 0,
            'message': f'持仓状态已切换为 {"有仓" if new_status == 1 else "空仓"}',
            'data': {'new_status': new_status}
        })
        
    except Exception as e:
        logger.error(f"切换持仓状态失败: {e}")
        conn.rollback()
        return jsonify({
            'code': 1,
            'message': f'切换失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

