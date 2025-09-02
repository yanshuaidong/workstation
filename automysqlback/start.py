#!/usr/bin/env python3
"""
期货数据更新系统启动脚本
使用方法：python start.py
"""

import sys
import os
import time

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == '__main__':
    try:
        # 导入并启动应用
        from app import app, init_database, scheduler, setup_scheduler
        
        print("=" * 50)
        print("期货数据更新系统启动中...")
        print("端口: 7001")
        print("数据库: 阿里云RDS MySQL")
        print("=" * 50)
        
        # 初始化数据库
        print("初始化数据库...")
        init_database()
        
        # 启动定时任务调度器
        print("启动定时任务调度器...")
        scheduler.start()
        
        # 等待调度器完全启动
        time.sleep(1)
        
        # 设置定时任务
        print("配置定时任务...")
        try:
            setup_scheduler()
        except Exception as scheduler_error:
            print(f"配置定时任务时出现警告: {scheduler_error}")
            print("系统将继续运行，但定时任务可能不可用")
        
        print("系统启动完成！")
        print("访问地址: http://localhost:7001")
        print("按 Ctrl+C 停止服务")
        print("=" * 50)
        
        # 启动Flask应用
        app.run(host='0.0.0.0', port=7001, debug=False)
        
    except KeyboardInterrupt:
        print("\n正在关闭系统...")
        if 'scheduler' in locals():
            scheduler.shutdown()
        print("系统已关闭")
    except Exception as e:
        print(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)