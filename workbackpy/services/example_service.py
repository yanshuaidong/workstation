from datetime import datetime

class ExampleService:
    """示例服务层 - 模拟数据操作"""
    
    # 模拟数据存储
    _data = [
        {"id": 1, "name": "示例 1", "description": "这是第一个示例", "created_at": "2024-01-01T00:00:00"},
        {"id": 2, "name": "示例 2", "description": "这是第二个示例", "created_at": "2024-01-02T00:00:00"}
    ]
    _next_id = 3
    
    @classmethod
    def get_all(cls):
        """获取所有数据"""
        return cls._data
    
    @classmethod
    def get_by_id(cls, example_id):
        """根据 ID 获取数据"""
        return next((item for item in cls._data if item['id'] == example_id), None)
    
    @classmethod
    def create(cls, data):
        """创建数据"""
        new_item = {
            'id': cls._next_id,
            'name': data['name'],
            'description': data.get('description', ''),
            'created_at': datetime.now().isoformat()
        }
        cls._data.append(new_item)
        cls._next_id += 1
        return new_item
    
    @classmethod
    def update(cls, example_id, data):
        """更新数据"""
        item = cls.get_by_id(example_id)
        if not item:
            return None
        
        item['name'] = data.get('name', item['name'])
        item['description'] = data.get('description', item['description'])
        item['updated_at'] = datetime.now().isoformat()
        return item
    
    @classmethod
    def delete(cls, example_id):
        """删除数据"""
        item = cls.get_by_id(example_id)
        if not item:
            return None
        
        cls._data.remove(item)
        return True 