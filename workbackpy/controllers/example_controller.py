from services.example_service import ExampleService

class ExampleController:
    """示例控制器"""
    
    @staticmethod
    def get_all():
        """获取所有数据"""
        return ExampleService.get_all()
    
    @staticmethod
    def get_by_id(example_id):
        """根据 ID 获取数据"""
        return ExampleService.get_by_id(example_id)
    
    @staticmethod
    def create(data):
        """创建数据"""
        # 数据验证
        if not data.get('name'):
            raise ValueError("名称不能为空")
        
        return ExampleService.create(data)
    
    @staticmethod
    def update(example_id, data):
        """更新数据"""
        # 数据验证
        if not data.get('name'):
            raise ValueError("名称不能为空")
        
        return ExampleService.update(example_id, data)
    
    @staticmethod
    def delete(example_id):
        """删除数据"""
        return ExampleService.delete(example_id) 