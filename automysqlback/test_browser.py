#!/usr/bin/env python3
"""
浏览器环境测试脚本
用于验证chromium和chromedriver是否正常工作
"""

import os
import sys
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_browser_basic():
    """基础浏览器测试"""
    logger.info("=== 基础浏览器环境测试 ===")
    
    # 检查文件存在性
    chrome_bin = os.environ.get('CHROME_BIN', '/usr/bin/chromium')
    chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
    
    logger.info(f"Chrome浏览器路径: {chrome_bin}")
    logger.info(f"ChromeDriver路径: {chromedriver_path}")
    
    if not os.path.exists(chrome_bin):
        logger.error(f"❌ Chrome浏览器不存在: {chrome_bin}")
        return False
    else:
        logger.info(f"✅ Chrome浏览器存在")
    
    if not os.path.exists(chromedriver_path):
        logger.error(f"❌ ChromeDriver不存在: {chromedriver_path}")
        return False
    else:
        logger.info(f"✅ ChromeDriver存在")
    
    return True

def test_browser_startup():
    """测试浏览器启动"""
    logger.info("=== 浏览器启动测试 ===")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1280,720')
    
    # 使用预装路径
    chrome_bin = os.environ.get('CHROME_BIN', '/usr/bin/chromium')
    chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
    
    chrome_options.binary_location = chrome_bin
    
    driver = None
    try:
        # 创建服务
        service = Service(executable_path=chromedriver_path)
        
        # 启动浏览器
        logger.info("正在启动浏览器...")
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        logger.info("✅ 浏览器启动成功")
        
        # 测试基本功能
        logger.info("测试基本导航功能...")
        driver.get("https://httpbin.org/get")
        
        # 等待页面加载
        time.sleep(2)
        
        # 检查页面标题
        title = driver.title
        logger.info(f"页面标题: {title}")
        
        if title:
            logger.info("✅ 页面导航测试成功")
            return True
        else:
            logger.error("❌ 页面导航测试失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 浏览器启动失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("浏览器已关闭")
            except:
                pass

def test_network_logging():
    """测试网络日志记录功能"""
    logger.info("=== 网络日志记录测试 ===")
    
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--enable-logging')
    chrome_options.add_argument('--log-level=0')
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    chrome_bin = os.environ.get('CHROME_BIN', '/usr/bin/chromium')
    chromedriver_path = os.environ.get('CHROMEDRIVER_PATH', '/usr/bin/chromedriver')
    
    chrome_options.binary_location = chrome_bin
    
    driver = None
    try:
        service = Service(executable_path=chromedriver_path)
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        logger.info("访问测试页面...")
        driver.get("https://httpbin.org/json")
        time.sleep(3)
        
        # 获取网络日志
        logs = driver.get_log('performance')
        logger.info(f"捕获到 {len(logs)} 条网络日志")
        
        if len(logs) > 0:
            logger.info("✅ 网络日志记录功能正常")
            return True
        else:
            logger.warning("⚠️ 未捕获到网络日志，可能影响财联社新闻爬取")
            return False
            
    except Exception as e:
        logger.error(f"❌ 网络日志测试失败: {e}")
        return False
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

def main():
    """主测试函数"""
    logger.info("开始浏览器环境测试...")
    
    success_count = 0
    total_tests = 3
    
    # 基础环境测试
    if test_browser_basic():
        success_count += 1
    
    # 浏览器启动测试
    if test_browser_startup():
        success_count += 1
    
    # 网络日志测试
    if test_network_logging():
        success_count += 1
    
    # 测试结果
    logger.info(f"=== 测试完成 ===")
    logger.info(f"通过测试: {success_count}/{total_tests}")
    
    if success_count == total_tests:
        logger.info("🎉 所有测试通过，浏览器环境配置正确！")
        return True
    else:
        logger.error("❌ 部分测试失败，请检查浏览器环境配置")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 