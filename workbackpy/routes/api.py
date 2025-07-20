from flask import Blueprint, request, jsonify
from controllers.example_controller import ExampleController
from controllers.futures_controller import FuturesController
from utils.response_handler import ResponseHandler

# 创建蓝图
api_bp = Blueprint('api', __name__)

# 示例路由
@api_bp.route('/test', methods=['GET'])
def test():
    """测试端点"""
    return ResponseHandler.success("API 测试成功", {"message": "Hello from Flask API!"})

@api_bp.route('/examples', methods=['GET'])
def get_examples():
    """获取示例数据"""
    try:
        data = ExampleController.get_all()
        return ResponseHandler.success("获取数据成功", data)
    except Exception as e:
        return ResponseHandler.error(f"获取数据失败: {str(e)}")

@api_bp.route('/examples', methods=['POST'])
def create_example():
    """创建示例数据"""
    try:
        data = request.get_json()
        if not data:
            return ResponseHandler.error("请求数据不能为空", 400)
        
        result = ExampleController.create(data)
        return ResponseHandler.success("创建成功", result, 201)
    except Exception as e:
        return ResponseHandler.error(f"创建失败: {str(e)}")

@api_bp.route('/examples/<int:example_id>', methods=['GET'])
def get_example(example_id):
    """根据 ID 获取示例数据"""
    try:
        data = ExampleController.get_by_id(example_id)
        if not data:
            return ResponseHandler.error("数据不存在", 404)
        return ResponseHandler.success("获取数据成功", data)
    except Exception as e:
        return ResponseHandler.error(f"获取数据失败: {str(e)}")

@api_bp.route('/examples/<int:example_id>', methods=['PUT'])
def update_example(example_id):
    """更新示例数据"""
    try:
        data = request.get_json()
        if not data:
            return ResponseHandler.error("请求数据不能为空", 400)
        
        result = ExampleController.update(example_id, data)
        if not result:
            return ResponseHandler.error("数据不存在", 404)
        return ResponseHandler.success("更新成功", result)
    except Exception as e:
        return ResponseHandler.error(f"更新失败: {str(e)}")

@api_bp.route('/examples/<int:example_id>', methods=['DELETE'])
def delete_example(example_id):
    """删除示例数据"""
    try:
        result = ExampleController.delete(example_id)
        if not result:
            return ResponseHandler.error("数据不存在", 404)
        return ResponseHandler.success("删除成功")
    except Exception as e:
        return ResponseHandler.error(f"删除失败: {str(e)}")

# 期货相关路由
futures_controller = FuturesController()

@api_bp.route('/futures/contracts', methods=['GET'])
def get_futures_contracts():
    """获取期货合约列表"""
    try:
        contracts = futures_controller.get_contracts()
        return ResponseHandler.success("获取合约列表成功", contracts)
    except Exception as e:
        return ResponseHandler.error(f"获取合约列表失败: {str(e)}")

@api_bp.route('/futures/history', methods=['GET'])
def get_futures_history():
    """获取期货历史数据"""
    try:
        symbol = request.args.get('symbol')
        period = request.args.get('period', 'daily')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if not symbol:
            return ResponseHandler.error("合约代码不能为空", 400)
        
        result = futures_controller.get_history(symbol, period, start_date, end_date)
        return ResponseHandler.success("获取历史数据成功", result)
    except Exception as e:
        return ResponseHandler.error(f"获取历史数据失败: {str(e)}")

@api_bp.route('/futures/periods', methods=['GET'])
def get_futures_periods():
    """获取周期选项"""
    try:
        periods = futures_controller.get_period_options()
        return ResponseHandler.success("获取周期选项成功", periods)
    except Exception as e:
        return ResponseHandler.error(f"获取周期选项失败: {str(e)}")

@api_bp.route('/futures/refresh-contracts', methods=['POST'])
def refresh_futures_contracts():
    """手动刷新合约数据"""
    try:
        result = futures_controller.refresh_contracts()
        return ResponseHandler.success("刷新成功", result)
    except Exception as e:
        return ResponseHandler.error(f"刷新失败: {str(e)}") 