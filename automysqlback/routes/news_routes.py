"""
新闻管理模块
包含：新闻CRUD、新闻处理流程、OSS文件管理等功能
"""

from flask import Blueprint, request, jsonify
import pymysql
from datetime import datetime, timedelta
import time
import logging
import re
import json as json_module
import oss2

# 创建蓝图
news_bp = Blueprint('news', __name__)

logger = logging.getLogger(__name__)

# ========== OSS工具函数 ==========

def generate_upload_key(news_id, filename):
    """生成上传文件的key，按月份组织目录结构"""
    now = datetime.now()
    year = now.strftime('%Y')
    month = now.strftime('%m')
    day = now.strftime('%d')
    
    # 生成唯一文件名
    file_ext = filename.split('.')[-1] if '.' in filename else 'png'
    unique_filename = f"news_{news_id}_{int(time.time())}_{hash(filename) % 10000}.{file_ext}"
    
    return f"screenshots/{year}/{month}/{day}/{unique_filename}"

def generate_signed_upload_url(object_key, content_type='image/png', expires=3600, get_oss_bucket=None):
    """生成带签名的上传URL"""
    try:
        bucket = get_oss_bucket()
        
        # 生成预签名URL用于上传
        signed_url = bucket.sign_url('PUT', object_key, expires, 
                                   headers={'Content-Type': content_type})
        
        return {
            'upload_url': signed_url,
            'object_key': object_key,
            'expires': expires
        }
    except Exception as e:
        logger.error(f"生成上传URL失败: {e}")
        return None

def generate_signed_access_url(object_key, expires=3600, get_oss_bucket=None):
    """生成带签名的访问URL"""
    try:
        bucket = get_oss_bucket()
        
        # 检查对象是否存在
        if not bucket.object_exists(object_key):
            return None
            
        # 生成预签名URL用于访问
        signed_url = bucket.sign_url('GET', object_key, expires)
        
        return signed_url
    except Exception as e:
        logger.error(f"生成访问URL失败: {e}")
        return None

def format_tracking_news(row, get_oss_bucket):
    """格式化跟踪新闻数据"""
    # 处理 screenshots JSON 数据
    screenshots_data = []
    if row['screenshots']:
        try:
            if isinstance(row['screenshots'], str):
                screenshots_data = json_module.loads(row['screenshots'])
            else:
                screenshots_data = row['screenshots']
        except:
            screenshots_data = []
    
    # 为每个截图生成访问URL
    screenshots_with_urls = []
    for screenshot_key in screenshots_data:
        access_url = generate_signed_access_url(screenshot_key, get_oss_bucket=get_oss_bucket)
        screenshots_with_urls.append({
            'key': screenshot_key,
            'url': access_url
        })
    
    return {
        'id': row['id'],
        'tracking_id': row['tracking_id'],
        'ctime': row['ctime'],
        'title': row['title'],
        'content': row['content'],
        'ai_analysis': row['ai_analysis'],
        'message_score': row['message_score'],
        'message_label': row['message_label'],
        'message_type': row['message_type'],
        'market_react': row['market_react'],
        'screenshots': screenshots_with_urls,
        'time': row['formatted_time'].strftime('%Y-%m-%d %H:%M:%S') if row['formatted_time'] else ''
    }

# ========== 新闻管理API ==========

@news_bp.route('/news/stats', methods=['GET'])
def get_cls_news_stats():
    """获取新闻统计信息"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 总新闻数
        cursor.execute("SELECT COUNT(*) as total FROM news_red_telegraph")
        total = cursor.fetchone()['total']
        
        # 今日新闻数
        cursor.execute("""
            SELECT COUNT(*) as today_count 
            FROM news_red_telegraph 
            WHERE DATE(created_at) = CURDATE()
        """)
        today_count = cursor.fetchone()['today_count']
        
        # 最新新闻时间
        cursor.execute("""
            SELECT FROM_UNIXTIME(MAX(ctime)) as latest_time 
            FROM news_red_telegraph
        """)
        latest_result = cursor.fetchone()
        latest_time = latest_result['latest_time'].strftime('%Y-%m-%d %H:%M:%S') if latest_result['latest_time'] else ''
        
        # 最早新闻时间
        cursor.execute("""
            SELECT FROM_UNIXTIME(MIN(ctime)) as earliest_time 
            FROM news_red_telegraph
        """)
        earliest_result = cursor.fetchone()
        earliest_time = earliest_result['earliest_time'].strftime('%Y-%m-%d %H:%M:%S') if earliest_result['earliest_time'] else ''
        
        return jsonify({
            'code': 0,
            'message': '统计信息获取成功',
            'data': {
                'total': total,
                'today_count': today_count,
                'latest_time': latest_time,
                'earliest_time': earliest_time
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

@news_bp.route('/news/list', methods=['GET'])
def get_cls_news_list():
    """分页查询财联社新闻（包含高级搜索和筛选功能）"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    page = request.args.get('page', 1, type=int)
    page_size = request.args.get('page_size', 10, type=int)
    search = request.args.get('search', '').strip()  # 搜索关键字
    search_field = request.args.get('search_field', 'title').strip()  # 搜索字段
    message_label = request.args.get('message_label', '').strip()  # 消息标签筛选
    start_date = request.args.get('start_date', '').strip()  # 开始日期 YYYY-MM-DD
    end_date = request.args.get('end_date', '').strip()  # 结束日期 YYYY-MM-DD
    
    # 限制分页参数
    page = max(1, page)
    page_size = max(1, min(100, page_size))
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 构建WHERE条件
        where_conditions = []
        where_params = []
        
        # 时间范围筛选
        if start_date:
            # 将日期转换为时间戳进行比较
            try:
                start_timestamp = int(datetime.strptime(start_date, '%Y-%m-%d').timestamp())
                where_conditions.append("ctime >= %s")
                where_params.append(start_timestamp)
            except ValueError:
                logger.warning(f"无效的开始日期格式: {start_date}")
        
        if end_date:
            try:
                # 结束日期加1天，确保包含当天的所有数据
                end_datetime = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                end_timestamp = int(end_datetime.timestamp())
                where_conditions.append("ctime < %s")
                where_params.append(end_timestamp)
            except ValueError:
                logger.warning(f"无效的结束日期格式: {end_date}")
        
        # 搜索条件（根据指定字段搜索）
        if search:
            # 验证搜索字段的有效性
            valid_search_fields = ['title', 'content', 'message_type', 'market_react']
            if search_field not in valid_search_fields:
                search_field = 'title'  # 默认使用标题搜索
            
            # 构建搜索条件
            if search_field == 'title':
                where_conditions.append("title LIKE %s")
                where_params.append(f"%{search}%")
            elif search_field == 'content':
                where_conditions.append("content LIKE %s")
                where_params.append(f"%{search}%")
            elif search_field == 'message_type':
                where_conditions.append("message_type LIKE %s")
                where_params.append(f"%{search}%")
            elif search_field == 'market_react':
                where_conditions.append("market_react LIKE %s")
                where_params.append(f"%{search}%")
        
        # 消息标签筛选
        if message_label and message_label in ['hard', 'soft', 'unknown']:
            where_conditions.append("message_label = %s")
            where_params.append(message_label)
        
        # 构建WHERE子句
        where_clause = ""
        if where_conditions:
            where_clause = "WHERE " + " AND ".join(where_conditions)
        
        # 查询总数
        count_sql = f"SELECT COUNT(*) as total FROM news_red_telegraph {where_clause}"
        cursor.execute(count_sql, where_params)
        total = cursor.fetchone()['total']
        
        # 计算偏移量
        offset = (page - 1) * page_size
        
        # 查询新闻列表（按ctime倒序，最新的在前面，包含所有新字段）
        list_sql = f"""
            SELECT 
                id,
                ctime,
                title,
                content,
                ai_analysis,
                message_score,
                message_label,
                message_type,
                market_react,
                screenshots,
                FROM_UNIXTIME(ctime) as formatted_time,
                created_at,
                updated_at
            FROM news_red_telegraph 
            {where_clause}
            ORDER BY ctime DESC 
            LIMIT %s OFFSET %s
        """
        
        list_params = where_params + [page_size, offset]
        cursor.execute(list_sql, list_params)
        
        news_list = cursor.fetchall()
        
        # 格式化数据
        formatted_news = []
        for news in news_list:
            # 处理 screenshots JSON 数据
            screenshots_data = []
            if news['screenshots']:
                try:
                    if isinstance(news['screenshots'], str):
                        screenshots_data = json_module.loads(news['screenshots'])
                    else:
                        screenshots_data = news['screenshots']
                except:
                    screenshots_data = []
            
            formatted_news.append({
                'id': news['id'],
                'ctime': news['ctime'],
                'title': news['title'],
                'content': news['content'],
                'ai_analysis': news['ai_analysis'],
                'message_score': news['message_score'],
                'message_label': news['message_label'],
                'message_type': news['message_type'],
                'market_react': news['market_react'],
                'screenshots': screenshots_data,
                'time': news['formatted_time'].strftime('%Y-%m-%d %H:%M:%S') if news['formatted_time'] else '',
                'created_at': news['created_at'].strftime('%Y-%m-%d %H:%M:%S') if news['created_at'] else '',
                'updated_at': news['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if news['updated_at'] else ''
            })
        
        # 计算分页信息
        total_pages = (total + page_size - 1) // page_size
        
        return jsonify({
            'code': 0,
            'message': '查询成功',
            'data': {
                'news_list': formatted_news,
                'pagination': {
                    'page': page,
                    'page_size': page_size,
                    'total': total,
                    'total_pages': total_pages,
                    'has_prev': page > 1,
                    'has_next': page < total_pages
                },
                'filters': {
                    'search': search,
                    'search_field': search_field,
                    'message_label': message_label,
                    'start_date': start_date,
                    'end_date': end_date
                }
            }
        })
        
    except Exception as e:
        logger.error(f"查询新闻列表失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'查询失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

@news_bp.route('/news/create', methods=['POST'])
def create_news():
    """创建新闻"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    data = request.get_json()
    
    # 验证必填字段
    if not data.get('title') or not data.get('content'):
        return jsonify({
            'code': 1,
            'message': '标题和内容为必填字段'
        })
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 生成ctime（如果没有提供）
        ctime = data.get('ctime', int(time.time()))
        
        # 处理screenshots数据
        screenshots_json = None
        if data.get('screenshots'):
            screenshots_json = json_module.dumps(data['screenshots'])
        
        cursor.execute("""
            INSERT INTO news_red_telegraph 
            (ctime, title, content, ai_analysis, message_score, message_label, 
             message_type, market_react, screenshots)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            ctime,
            data['title'],
            data['content'],
            data.get('ai_analysis'),
            data.get('message_score'),
            data.get('message_label', 'unknown'),
            data.get('message_type'),
            data.get('market_react'),
            screenshots_json
        ))
        
        news_id = cursor.lastrowid
        
        # 自动创建处理跟踪记录
        cursor.execute("""
            INSERT INTO news_process_tracking (news_id, ctime)
            VALUES (%s, %s)
        """, (news_id, ctime))
        
        conn.commit()
        
        return jsonify({
            'code': 0,
            'message': '新闻创建成功',
            'data': {'id': news_id}
        })
        
    except Exception as e:
        logger.error(f"创建新闻失败: {e}")
        conn.rollback()
        return jsonify({
            'code': 1,
            'message': f'创建失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

@news_bp.route('/news/detail/<int:news_id>', methods=['GET'])
def get_news_detail(news_id):
    """获取新闻详情"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    get_oss_bucket = current_app.config['get_oss_bucket']
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("""
            SELECT 
                id, ctime, title, content, ai_analysis, message_score,
                message_label, message_type, market_react, screenshots,
                FROM_UNIXTIME(ctime) as formatted_time, created_at, updated_at
            FROM news_red_telegraph 
            WHERE id = %s
        """, (news_id,))
        
        news = cursor.fetchone()
        
        if not news:
            return jsonify({
                'code': 1,
                'message': '新闻不存在'
            })
        
        # 处理 screenshots JSON 数据
        screenshots_data = []
        if news['screenshots']:
            try:
                if isinstance(news['screenshots'], str):
                    screenshots_data = json_module.loads(news['screenshots'])
                else:
                    screenshots_data = news['screenshots']
            except:
                screenshots_data = []
        
        # 为每个截图生成访问URL
        screenshots_with_urls = []
        for screenshot_key in screenshots_data:
            access_url = generate_signed_access_url(screenshot_key, get_oss_bucket=get_oss_bucket)
            screenshots_with_urls.append({
                'key': screenshot_key,
                'url': access_url
            })
        
        formatted_data = {
            'id': news['id'],
            'ctime': news['ctime'],
            'title': news['title'],
            'content': news['content'],
            'ai_analysis': news['ai_analysis'],
            'message_score': news['message_score'],
            'message_label': news['message_label'],
            'message_type': news['message_type'],
            'market_react': news['market_react'],
            'screenshots': screenshots_with_urls,
            'time': news['formatted_time'].strftime('%Y-%m-%d %H:%M:%S') if news['formatted_time'] else '',
            'created_at': news['created_at'].strftime('%Y-%m-%d %H:%M:%S') if news['created_at'] else '',
            'updated_at': news['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if news['updated_at'] else ''
        }
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': formatted_data
        })
        
    except Exception as e:
        logger.error(f"获取新闻详情失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

@news_bp.route('/news/update/<int:news_id>', methods=['PUT'])
def update_news(news_id):
    """更新新闻"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    data = request.get_json()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 检查新闻是否存在
        cursor.execute("SELECT id FROM news_red_telegraph WHERE id = %s", (news_id,))
        if not cursor.fetchone():
            return jsonify({
                'code': 1,
                'message': '新闻不存在'
            })
        
        # 构建更新字段
        update_fields = []
        update_values = []
        
        updatable_fields = [
            'title', 'content', 'ai_analysis', 'message_score', 
            'message_label', 'message_type', 'market_react'
        ]
        
        for field in updatable_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                update_values.append(data[field])
        
        # 处理screenshots字段
        if 'screenshots' in data:
            update_fields.append("screenshots = %s")
            screenshots_json = json_module.dumps(data['screenshots']) if data['screenshots'] else None
            update_values.append(screenshots_json)
        
        if not update_fields:
            return jsonify({
                'code': 1,
                'message': '没有需要更新的字段'
            })
        
        # 添加updated_at字段
        update_fields.append("updated_at = NOW()")
        update_values.append(news_id)
        
        # 执行更新
        sql = f"UPDATE news_red_telegraph SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(sql, update_values)
        
        conn.commit()
        
        return jsonify({
            'code': 0,
            'message': '新闻更新成功'
        })
        
    except Exception as e:
        logger.error(f"更新新闻失败: {e}")
        conn.rollback()
        return jsonify({
            'code': 1,
            'message': f'更新失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

@news_bp.route('/news/delete/<int:news_id>', methods=['DELETE'])
def delete_news(news_id):
    """删除新闻"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    get_oss_bucket = current_app.config['get_oss_bucket']
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 获取新闻信息（用于删除相关的OSS文件）
        cursor.execute("SELECT screenshots FROM news_red_telegraph WHERE id = %s", (news_id,))
        news = cursor.fetchone()
        
        if not news:
            return jsonify({
                'code': 1,
                'message': '新闻不存在'
            })
        
        # 删除OSS上的截图文件
        if news['screenshots']:
            try:
                screenshots_data = []
                if isinstance(news['screenshots'], str):
                    screenshots_data = json_module.loads(news['screenshots'])
                else:
                    screenshots_data = news['screenshots']
                
                bucket = get_oss_bucket()
                for screenshot_key in screenshots_data:
                    try:
                        bucket.delete_object(screenshot_key)
                        logger.info(f"已删除OSS文件: {screenshot_key}")
                    except Exception as e:
                        logger.warning(f"删除OSS文件失败 {screenshot_key}: {e}")
            except Exception as e:
                logger.warning(f"处理screenshots数据失败: {e}")
        
        # 删除数据库记录（外键级联删除跟踪记录）
        cursor.execute("DELETE FROM news_red_telegraph WHERE id = %s", (news_id,))
        
        if cursor.rowcount == 0:
            return jsonify({
                'code': 1,
                'message': '新闻不存在'
            })
        
        conn.commit()
        
        return jsonify({
            'code': 0,
            'message': '新闻删除成功'
        })
        
    except Exception as e:
        logger.error(f"删除新闻失败: {e}")
        conn.rollback()
        return jsonify({
            'code': 1,
            'message': f'删除失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

# ========== 新闻处理流程API ==========

@news_bp.route('/news/process/unreviewed', methods=['GET'])
def get_unreviewed_news():
    """获取待校验的新闻列表"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 计算30天前的时间戳
        thirty_days_ago = int((datetime.now() - timedelta(days=30)).timestamp())
        
        # 查询最近30天内未校验的新闻数量
        cursor.execute("""
            SELECT COUNT(*) as total FROM news_process_tracking 
            WHERE ctime >= %s AND is_reviewed = 0
        """, (thirty_days_ago,))
        
        total_unreviewed = cursor.fetchone()['total']
        
        # 获取下一条待校验的新闻详情
        cursor.execute("""
            SELECT 
                nrt.id, nrt.ctime, nrt.title, nrt.content, 
                nrt.ai_analysis, nrt.message_score, nrt.message_label, nrt.message_type,
                npt.id as tracking_id,
                FROM_UNIXTIME(nrt.ctime) as formatted_time
            FROM news_process_tracking npt
            JOIN news_red_telegraph nrt ON npt.news_id = nrt.id
            WHERE npt.ctime >= %s AND npt.is_reviewed = 0
            ORDER BY nrt.ctime ASC
            LIMIT 1
        """, (thirty_days_ago,))
        
        current_news = cursor.fetchone()
        
        result_data = {
            'total_unreviewed': total_unreviewed,
            'current_news': None
        }
        
        if current_news:
            result_data['current_news'] = {
                'id': current_news['id'],
                'tracking_id': current_news['tracking_id'],
                'ctime': current_news['ctime'],
                'title': current_news['title'],
                'content': current_news['content'],
                'ai_analysis': current_news['ai_analysis'],
                'message_score': current_news['message_score'],
                'message_label': current_news['message_label'],
                'message_type': current_news['message_type'],
                'time': current_news['formatted_time'].strftime('%Y-%m-%d %H:%M:%S') if current_news['formatted_time'] else ''
            }
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': result_data
        })
        
    except Exception as e:
        logger.error(f"获取待校验新闻失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

@news_bp.route('/news/process/review', methods=['POST'])
def mark_news_reviewed():
    """标记新闻为已校验"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    data = request.get_json()
    tracking_id = data.get('tracking_id')
    
    if not tracking_id:
        return jsonify({
            'code': 1,
            'message': '缺少tracking_id参数'
        })
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 更新校验状态
        cursor.execute("""
            UPDATE news_process_tracking 
            SET is_reviewed = 1, review_time = NOW(), updated_at = NOW()
            WHERE id = %s
        """, (tracking_id,))
        
        if cursor.rowcount == 0:
            return jsonify({
                'code': 1,
                'message': '记录不存在'
            })
        
        conn.commit()
        
        return jsonify({
            'code': 0,
            'message': '校验状态更新成功'
        })
        
    except Exception as e:
        logger.error(f"更新校验状态失败: {e}")
        conn.rollback()
        return jsonify({
            'code': 1,
            'message': f'更新失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

@news_bp.route('/news/process/tracking-list', methods=['GET'])
def get_tracking_list():
    """获取需要跟踪的新闻列表（按天数分组）- 只返回硬消息且到达跟踪时间点的消息"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    get_oss_bucket = current_app.config['get_oss_bucket']
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 计算各个时间点的时间戳
        now = datetime.now()
        day3_ago = int((now - timedelta(days=3)).timestamp())
        day7_ago = int((now - timedelta(days=7)).timestamp())
        day14_ago = int((now - timedelta(days=14)).timestamp())
        day28_ago = int((now - timedelta(days=28)).timestamp())
        
        result_data = {
            'day3_list': [],
            'day7_list': [],
            'day14_list': [],
            'day28_list': []
        }
        
        # 3天跟踪列表：距今3天及以上的硬消息，且3天跟踪未完成
        cursor.execute("""
            SELECT 
                nrt.id, nrt.ctime, nrt.title, nrt.content, 
                nrt.ai_analysis, nrt.message_score, nrt.message_label, nrt.message_type,
                nrt.market_react, nrt.screenshots,
                npt.id as tracking_id,
                FROM_UNIXTIME(nrt.ctime) as formatted_time
            FROM news_process_tracking npt
            JOIN news_red_telegraph nrt ON npt.news_id = nrt.id
            WHERE nrt.ctime <= %s 
            AND nrt.message_label = 'hard'
            AND npt.is_reviewed = 1 
            AND npt.track_day3_done = 0
            ORDER BY nrt.ctime ASC
        """, (day3_ago,))
        
        for row in cursor.fetchall():
            result_data['day3_list'].append(format_tracking_news(row, get_oss_bucket))
        
        # 7天跟踪列表：距今7天及以上的硬消息，且7天跟踪未完成
        cursor.execute("""
            SELECT 
                nrt.id, nrt.ctime, nrt.title, nrt.content, 
                nrt.ai_analysis, nrt.message_score, nrt.message_label, nrt.message_type,
                nrt.market_react, nrt.screenshots,
                npt.id as tracking_id,
                FROM_UNIXTIME(nrt.ctime) as formatted_time
            FROM news_process_tracking npt
            JOIN news_red_telegraph nrt ON npt.news_id = nrt.id
            WHERE nrt.ctime <= %s 
            AND nrt.message_label = 'hard'
            AND npt.is_reviewed = 1 
            AND npt.track_day7_done = 0
            ORDER BY nrt.ctime ASC
        """, (day7_ago,))
        
        for row in cursor.fetchall():
            result_data['day7_list'].append(format_tracking_news(row, get_oss_bucket))
        
        # 14天跟踪列表：距今14天及以上的硬消息，且14天跟踪未完成
        cursor.execute("""
            SELECT 
                nrt.id, nrt.ctime, nrt.title, nrt.content, 
                nrt.ai_analysis, nrt.message_score, nrt.message_label, nrt.message_type,
                nrt.market_react, nrt.screenshots,
                npt.id as tracking_id,
                FROM_UNIXTIME(nrt.ctime) as formatted_time
            FROM news_process_tracking npt
            JOIN news_red_telegraph nrt ON npt.news_id = nrt.id
            WHERE nrt.ctime <= %s 
            AND nrt.message_label = 'hard'
            AND npt.is_reviewed = 1 
            AND npt.track_day14_done = 0
            ORDER BY nrt.ctime ASC
        """, (day14_ago,))
        
        for row in cursor.fetchall():
            result_data['day14_list'].append(format_tracking_news(row, get_oss_bucket))
        
        # 28天跟踪列表：距今28天及以上的硬消息，且28天跟踪未完成
        cursor.execute("""
            SELECT 
                nrt.id, nrt.ctime, nrt.title, nrt.content, 
                nrt.ai_analysis, nrt.message_score, nrt.message_label, nrt.message_type,
                nrt.market_react, nrt.screenshots,
                npt.id as tracking_id,
                FROM_UNIXTIME(nrt.ctime) as formatted_time
            FROM news_process_tracking npt
            JOIN news_red_telegraph nrt ON npt.news_id = nrt.id
            WHERE nrt.ctime <= %s 
            AND nrt.message_label = 'hard'
            AND npt.is_reviewed = 1 
            AND npt.track_day28_done = 0
            ORDER BY nrt.ctime ASC
        """, (day28_ago,))
        
        for row in cursor.fetchall():
            result_data['day28_list'].append(format_tracking_news(row, get_oss_bucket))
        
        # 统计信息
        total_count = (len(result_data['day3_list']) + 
                      len(result_data['day7_list']) + 
                      len(result_data['day14_list']) + 
                      len(result_data['day28_list']))
        
        return jsonify({
            'code': 0,
            'message': '获取成功',
            'data': {
                **result_data,
                'summary': {
                    'total_pending': total_count,
                    'day3_count': len(result_data['day3_list']),
                    'day7_count': len(result_data['day7_list']),
                    'day14_count': len(result_data['day14_list']),
                    'day28_count': len(result_data['day28_list'])
                }
            }
        })
        
    except Exception as e:
        logger.error(f"获取跟踪列表失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'获取失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

@news_bp.route('/news/process/update-tracking', methods=['POST'])
def update_tracking_status():
    """更新跟踪状态"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    data = request.get_json()
    tracking_id = data.get('tracking_id')
    track_type = data.get('track_type')  # day3, day7, day14, day28
    
    if not tracking_id or not track_type:
        return jsonify({
            'code': 1,
            'message': '缺少必要参数'
        })
    
    # 验证track_type
    valid_types = ['day3', 'day7', 'day14', 'day28']
    if track_type not in valid_types:
        return jsonify({
            'code': 1,
            'message': '无效的跟踪类型'
        })
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 构建动态SQL
        done_field = f"track_{track_type}_done"
        time_field = f"track_{track_type}_time"
        
        sql = f"""
            UPDATE news_process_tracking 
            SET {done_field} = 1, {time_field} = NOW(), updated_at = NOW()
            WHERE id = %s
        """
        
        cursor.execute(sql, (tracking_id,))
        
        if cursor.rowcount == 0:
            return jsonify({
                'code': 1,
                'message': '记录不存在'
            })
        
        conn.commit()
        
        return jsonify({
            'code': 0,
            'message': f'{track_type}跟踪状态更新成功'
        })
        
    except Exception as e:
        logger.error(f"更新跟踪状态失败: {e}")
        conn.rollback()
        return jsonify({
            'code': 1,
            'message': f'更新失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

@news_bp.route('/news/process/init-tracking', methods=['POST'])
def init_tracking_for_existing_news():
    """为现有新闻初始化跟踪记录"""
    from flask import current_app
    get_db_connection = current_app.config['get_db_connection']
    
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        # 查找没有跟踪记录的新闻
        cursor.execute("""
            SELECT nrt.id, nrt.ctime 
            FROM news_red_telegraph nrt
            LEFT JOIN news_process_tracking npt ON nrt.id = npt.news_id
            WHERE npt.news_id IS NULL
        """)
        
        missing_news = cursor.fetchall()
        
        if not missing_news:
            return jsonify({
                'code': 0,
                'message': '所有新闻都已有跟踪记录',
                'data': {'created_count': 0}
            })
        
        # 为这些新闻创建跟踪记录
        created_count = 0
        for news in missing_news:
            try:
                cursor.execute("""
                    INSERT INTO news_process_tracking (news_id, ctime)
                    VALUES (%s, %s)
                """, (news['id'], news['ctime']))
                created_count += 1
            except Exception as e:
                logger.warning(f"为新闻ID {news['id']} 创建跟踪记录失败: {e}")
        
        conn.commit()
        
        return jsonify({
            'code': 0,
            'message': f'成功为 {created_count} 条新闻创建跟踪记录',
            'data': {'created_count': created_count}
        })
        
    except Exception as e:
        logger.error(f"初始化跟踪记录失败: {e}")
        conn.rollback()
        return jsonify({
            'code': 1,
            'message': f'初始化失败: {str(e)}'
        })
    finally:
        cursor.close()
        conn.close()

# ========== OSS文件管理API ==========

@news_bp.route('/oss/upload-url', methods=['POST'])
def get_upload_url():
    """获取OSS上传签名URL"""
    from flask import current_app
    get_oss_bucket = current_app.config['get_oss_bucket']
    
    data = request.get_json()
    
    news_id = data.get('news_id')
    filename = data.get('filename')
    content_type = data.get('content_type', 'image/png')
    
    if not news_id or not filename:
        return jsonify({
            'code': 1,
            'message': '缺少必要参数: news_id 和 filename'
        })
    
    try:
        # 生成上传key
        object_key = generate_upload_key(news_id, filename)
        
        # 生成签名URL
        upload_info = generate_signed_upload_url(object_key, content_type, get_oss_bucket=get_oss_bucket)
        
        if not upload_info:
            return jsonify({
                'code': 1,
                'message': '生成上传URL失败'
            })
        
        return jsonify({
            'code': 0,
            'message': '获取上传URL成功',
            'data': upload_info
        })
        
    except Exception as e:
        logger.error(f"获取上传URL失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'获取上传URL失败: {str(e)}'
        })

@news_bp.route('/oss/access-url', methods=['POST'])
def get_access_url():
    """获取OSS访问URL"""
    from flask import current_app
    get_oss_bucket = current_app.config['get_oss_bucket']
    
    data = request.get_json()
    
    object_key = data.get('object_key')
    expires = data.get('expires', 3600)
    
    if not object_key:
        return jsonify({
            'code': 1,
            'message': '缺少必要参数: object_key'
        })
    
    try:
        access_url = generate_signed_access_url(object_key, expires, get_oss_bucket=get_oss_bucket)
        
        if not access_url:
            return jsonify({
                'code': 1,
                'message': '文件不存在或生成访问URL失败'
            })
        
        return jsonify({
            'code': 0,
            'message': '获取访问URL成功',
            'data': {
                'access_url': access_url,
                'expires': expires
            }
        })
        
    except Exception as e:
        logger.error(f"获取访问URL失败: {e}")
        return jsonify({
            'code': 1,
            'message': f'获取访问URL失败: {str(e)}'
        })

