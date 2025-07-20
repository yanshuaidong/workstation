from flask import jsonify
from datetime import datetime

class ResponseHandler:
    """统一响应处理器"""
    
    @staticmethod
    def success(message="操作成功", data=None, status_code=200):
        """成功响应"""
        response = {
            "success": True,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        return jsonify(response), status_code
    
    @staticmethod
    def error(message="操作失败", status_code=400, error_code=None):
        """错误响应"""
        response = {
            "success": False,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "error_code": error_code
        }
        return jsonify(response), status_code
    
    @staticmethod
    def paginated_success(message="获取数据成功", data=None, pagination=None, status_code=200):
        """分页成功响应"""
        response = {
            "success": True,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "data": data,
            "pagination": pagination
        }
        return jsonify(response), status_code 