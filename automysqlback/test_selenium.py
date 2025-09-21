#!/usr/bin/env python3
"""
Selenium 服务连接测试脚本
用于验证后端容器是否能正常连接到 Selenium Chrome 服务
"""

import os
import sys
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

def test_selenium_connection():
    """测试 Selenium 服务连接"""
    print("开始测试 Selenium 服务连接...")
    
    # 获取 Selenium 服务 URL
    selenium_url = os.environ.get('SELENIUM_REMOTE_URL', 'http://selenium-chrome:4444/wd/hub')
    print(f"Selenium URL: {selenium_url}")
    
    # 1. 测试 Selenium Grid 状态
    try:
        status_url = selenium_url.replace('/wd/hub', '/wd/hub/status')
        print(f"检查 Selenium Grid 状态: {status_url}")
        
        response = requests.get(status_url, timeout=10)
        response.raise_for_status()
        
        status_data = response.json()
        print(f"Selenium Grid 状态: {status_data.get('value', {}).get('ready', False)}")
        
        if not status_data.get('value', {}).get('ready', False):
            print("ERROR: Selenium Grid 未就绪")
            return False
            
    except Exception as e:
        print(f"ERROR: 无法连接到 Selenium Grid 状态接口: {e}")
        return False
    
    # 2. 测试创建 WebDriver 会话
    try:
        print("尝试创建 Chrome WebDriver 会话...")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        
        # 创建远程 WebDriver
        driver = webdriver.Remote(
            command_executor=selenium_url,
            options=chrome_options
        )
        
        print("WebDriver 会话创建成功")
        
        # 3. 测试基本功能
        print("测试基本浏览器功能...")
        driver.get("https://www.baidu.com")
        title = driver.title
        print(f"页面标题: {title}")
        
        if "百度" in title:
            print("SUCCESS: 浏览器功能正常")
            result = True
        else:
            print("WARNING: 页面标题异常")
            result = False
        
        # 关闭浏览器
        driver.quit()
        print("WebDriver 会话已关闭")
        
        return result
        
    except Exception as e:
        print(f"ERROR: WebDriver 测试失败: {e}")
        return False

def test_network_connectivity():
    """测试网络连通性"""
    print("\n检查网络连通性...")
    
    # 测试域名解析
    import socket
    try:
        socket.gethostbyname('selenium-chrome')
        print("SUCCESS: 可以解析 selenium-chrome 主机名")
    except Exception as e:
        print(f"ERROR: 无法解析 selenium-chrome 主机名: {e}")
        return False
    
    # 测试端口连通性
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex(('selenium-chrome', 4444))
        sock.close()
        
        if result == 0:
            print("SUCCESS: selenium-chrome:4444 端口可达")
            return True
        else:
            print(f"ERROR: selenium-chrome:4444 端口不可达，错误码: {result}")
            return False
    except Exception as e:
        print(f"ERROR: 端口测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("Selenium 服务连接测试")
    print("=" * 50)
    
    # 等待一下，确保服务完全启动
    print("等待 5 秒，确保服务完全启动...")
    time.sleep(5)
    
    # 测试网络连通性
    network_ok = test_network_connectivity()
    if not network_ok:
        print("\n网络连通性测试失败，请检查:")
        print("1. selenium-chrome 容器是否正在运行")
        print("2. 容器是否在同一网络中")
        print("3. 端口 4444 是否正常监听")
        sys.exit(1)
    
    # 测试 Selenium 连接
    selenium_ok = test_selenium_connection()
    if not selenium_ok:
        print("\nSelenium 服务测试失败，请检查:")
        print("1. Selenium 容器是否健康")
        print("2. Chrome 浏览器是否正常工作")
        print("3. 内存是否充足")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("SUCCESS: 所有测试通过！")
    print("Selenium 服务连接正常，可以正常使用爬虫功能")
    print("=" * 50)

if __name__ == "__main__":
    main() 