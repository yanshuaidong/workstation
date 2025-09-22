#!/usr/bin/env python3
"""
财联社新闻爬虫 - 完整版本
功能：
1. 爬取财联社加红电报新闻
2. 数据入库到远程MySQL数据库
3. AI分析新闻内容

使用方法:
  python main.py crawl       - 只爬取新闻
  python main.py analyze [数量] - 只AI分析最新未分析的新闻
  python main.py full        - 完整流程：爬取 + AI分析
"""

import sys
import os
import time
import json
import logging
import traceback
import asyncio
import re
import requests
import aiohttp
import pymysql
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==================== 配置参数 ====================

# 数据库配置
DB_CONFIG = {
    'host': 'rm-bp1u701yzm0y42oh1vo.mysql.rds.aliyuncs.com',
    'port': 3306,
    'user': 'ysd',
    'password': 'Yan1234567',
    'database': 'futures',
    'charset': 'utf8mb4'
}

# AI API 配置
AI_API_KEY = "sk-qVU4OZNspU5cSTPONFBFD000t2Oy8Tq9U8h74Wm5Phnl8tsB"
AI_BASE_URL = "https://poloai.top/v1/chat/completions"

# ==================== 数据库操作函数 ====================

def get_db_connection():
    """获取数据库连接"""
    return pymysql.connect(**DB_CONFIG)

def save_news_to_db(news_data):
    """保存新闻数据到数据库"""
    if not news_data:
        return 0, 0
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    new_count = 0
    duplicate_count = 0
    
    try:
        for news_item in news_data:
            ctime = news_item.get('ctime')
            title = news_item.get('title', '')
            content = news_item.get('content', '')
            
            if not ctime or not title:
                continue
                
            try:
                # 清理HTML标签
                title = re.sub(r'<[^>]+>', '', title)
                content = re.sub(r'<[^>]+>', '', content)
                
                cursor.execute("""
                    INSERT INTO news_red_telegraph (ctime, title, content)
                    VALUES (%s, %s, %s)
                """, (ctime, title, content))
                
                new_count += 1
                logger.info(f"保存新闻: {title[:50]}...")
                
            except pymysql.IntegrityError as e:
                if e.args[0] == 1062:  # Duplicate entry
                    duplicate_count += 1
                    logger.debug(f"新闻已存在，跳过: {title[:50]}...")
                else:
                    logger.error(f"保存新闻时出错: {e}")
        
        conn.commit()
        logger.info(f"新闻保存完成: 新增{new_count}条, 重复{duplicate_count}条")
        return new_count, duplicate_count
        
    except Exception as e:
        logger.error(f"保存新闻数据失败: {e}")
        conn.rollback()
        return 0, 0
    finally:
        cursor.close()
        conn.close()

def get_unanalyzed_news(count=10):
    """获取未分析的新闻"""
    conn = get_db_connection()
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    
    try:
        cursor.execute("""
            SELECT id, title, content 
            FROM news_red_telegraph 
            WHERE ai_analysis IS NULL 
            ORDER BY ctime DESC 
            LIMIT %s
        """, (count,))
        
        news_list = cursor.fetchall()
        return news_list
        
    except Exception as e:
        logger.error(f"获取未分析新闻失败: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

def update_news_analysis_results(results):
    """更新新闻分析结果到数据库"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    success_count = 0
    failure_count = 0
    
    try:
        for result in results:
            try:
                cursor.execute("""
                    UPDATE news_red_telegraph 
                    SET ai_analysis = %s, updated_at = NOW()
                    WHERE id = %s
                """, (result['analysis'], result['id']))
                
                if result['success']:
                    success_count += 1
                else:
                    failure_count += 1
                    
            except Exception as e:
                logger.error(f"更新新闻分析结果失败 - ID: {result['id']}, 错误: {e}")
                failure_count += 1
        
        conn.commit()
        logger.info(f"批量更新完成: 成功 {success_count} 条, 失败 {failure_count} 条")
        return success_count, failure_count
        
    except Exception as e:
        logger.error(f"批量更新新闻分析结果失败: {e}")
        conn.rollback()
        return 0, len(results)
    finally:
        cursor.close()
        conn.close()

# ==================== AI分析函数 ====================

async def analyze_single_news_async(session, prompt, news_item):
    """异步分析单条新闻"""
    try:
        payload = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "你是一个财经消息分类助手。"},
                {"role": "user", "content": f"{prompt}\n\n新闻标题：{news_item['title']}\n新闻内容：{news_item['content']}"}
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        headers = {
            "Accept": "application/json",
            "Authorization": f"Bearer {AI_API_KEY}",
            'User-Agent': 'PoloAPI/1.0.0 (https://poloai.top)',
            "Content-Type": "application/json"
        }
        
        async with session.post(AI_BASE_URL, json=payload, headers=headers, timeout=60) as response:
            if response.status == 200:
                result = await response.json()
                analysis_result = result["choices"][0]["message"]["content"]
                logger.info(f"AI分析完成 - 新闻ID: {news_item['id']}, 结果: {analysis_result[:50]}...")
                return {
                    'id': news_item['id'],
                    'analysis': analysis_result[:1000],  # 限制长度
                    'success': True
                }
            else:
                logger.error(f"AI请求失败 - 新闻ID: {news_item['id']}, 状态码: {response.status}")
                return {
                    'id': news_item['id'],
                    'analysis': f"AI请求失败: HTTP {response.status}",
                    'success': False
                }
                
    except asyncio.TimeoutError:
        logger.warning(f"AI请求超时 - 新闻ID: {news_item['id']}")
        return {
            'id': news_item['id'],
            'analysis': "AI请求超时",
            'success': False
        }
    except Exception as e:
        logger.error(f"AI分析异常 - 新闻ID: {news_item['id']}, 错误: {e}")
        return {
            'id': news_item['id'],
            'analysis': f"AI分析异常: {str(e)[:100]}",
            'success': False
        }

async def batch_analyze_news_async(prompt, news_list):
    """批量异步分析新闻"""
    results = []
    
    async with aiohttp.ClientSession() as session:
        # 创建任务列表
        tasks = []
        for news_item in news_list:
            task = analyze_single_news_async(session, prompt, news_item)
            tasks.append(task)
        
        # 批量执行，但控制并发数量
        semaphore = asyncio.Semaphore(10)  # 限制并发数为10
        
        async def bounded_task(task):
            async with semaphore:
                return await task
        
        bounded_tasks = [bounded_task(task) for task in tasks]
        results = await asyncio.gather(*bounded_tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"任务执行异常 - 新闻ID: {news_list[i]['id']}, 错误: {result}")
                processed_results.append({
                    'id': news_list[i]['id'],
                    'analysis': f"任务执行异常: {str(result)[:100]}",
                    'success': False
                })
            else:
                processed_results.append(result)
        
        return processed_results

# ==================== 爬虫类和函数 ====================

class ClsNewsCrawler:
    """财联社加红电报新闻爬虫"""
    
    def __init__(self, headless=True):
        self.driver = None
        self.headless = headless
        self.network_logs = []
        
    def setup_driver(self):
        """设置Chrome驱动"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')
        
        # 基本配置
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--window-size=1280,720')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 启用网络日志记录
        chrome_options.add_argument('--enable-logging')
        chrome_options.add_argument('--log-level=0')
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        try:
            # 尝试使用系统默认的Chrome/Chromium
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome驱动初始化成功")
        except Exception as e:
            logger.error(f"Chrome驱动初始化失败: {e}")
            # 尝试指定ChromeDriver路径
            try:
                service = Service()  # 使用系统PATH中的chromedriver
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("使用系统PATH驱动初始化成功")
            except Exception as e2:
                logger.error(f"所有驱动初始化方案都失败: {e2}")
                raise
        
        self.driver.set_page_load_timeout(30)
        self.driver.implicitly_wait(10)
    
    def get_network_logs(self):
        """获取网络请求日志"""
        try:
            logs = self.driver.get_log('performance')
            network_requests = []
            
            for log in logs:
                try:
                    message = json.loads(log['message'])
                    if message['message']['method'] == 'Network.responseReceived':
                        url = message['message']['params']['response']['url']
                        if 'cls.cn/v1/roll/get_roll_list' in url:
                            network_requests.append({
                                'url': url,
                                'timestamp': log['timestamp'],
                                'response': message['message']['params']['response']
                            })
                except (json.JSONDecodeError, KeyError):
                    continue
            
            return network_requests
        except Exception as e:
            logger.error(f"获取网络日志失败: {e}")
            return []
    
    def extract_params_from_url(self, url):
        """从URL中提取参数"""
        params = {}
        if '?' in url:
            query_string = url.split('?')[1]
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value
        return params
    
    def click_jiahong_button(self):
        """点击加红按钮"""
        logger.info("开始寻找并点击'加红'按钮...")
        
        # 等待页面加载完成
        try:
            WebDriverWait(self.driver, 15).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
        except Exception as e:
            logger.warning(f"等待页面加载完成失败: {e}")
        
        # 多种选择器策略
        selectors = [
            "//a[contains(text(), '加红')]",
            "//h3[contains(@class, 'level-2-nav')]//a[contains(text(), '加红')]",
            "//h3[@class='f-l f-s-17 level-2-nav']//a[@class='p-r d-b w-94 c-p c-ef9524']",
            "//a[@class='p-r d-b w-94 c-p c-ef9524']",
            "//a[contains(@class, 'c-ef9524')]"
        ]
        
        for i, selector in enumerate(selectors):
            try:
                logger.info(f"尝试选择器 {i+1}: {selector}")
                elements = self.driver.find_elements(By.XPATH, selector)
                
                if elements:
                    element = elements[0]
                    logger.info(f"找到元素: {element.text[:50]}")
                    
                    # 滚动到元素位置
                    self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                    time.sleep(1)
                    
                    # 尝试点击
                    try:
                        element.click()
                        logger.info("成功点击'加红'按钮")
                        return True
                    except:
                        # 使用JavaScript点击
                        self.driver.execute_script("arguments[0].click();", element)
                        logger.info("使用JavaScript成功点击'加红'按钮")
                        return True
                        
            except Exception as e:
                logger.warning(f"选择器 {i+1} 执行失败: {e}")
                continue
        
        logger.error("未能找到或点击'加红'按钮")
        return False
    
    def make_api_request(self, url):
        """使用浏览器的cookies和headers发起API请求"""
        try:
            # 获取浏览器的cookies
            cookies = self.driver.get_cookies()
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            
            # 设置请求头
            headers = {
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'zh-CN,zh;q=0.9',
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Content-Type': 'application/json;charset=utf-8',
                'Pragma': 'no-cache',
                'Referer': 'https://www.cls.cn/telegraph',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-origin',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            logger.info(f"发起API请求: {url[:100]}...")
            response = requests.get(url, headers=headers, cookies=cookie_dict, timeout=15)
            response.raise_for_status()
            
            json_data = response.json()
            logger.info("API请求成功")
            return json_data
            
        except Exception as e:
            logger.error(f"API请求失败: {e}")
            return None
    
    def crawl_news(self):
        """爬取财联社加红电报新闻"""
        try:
            logger.info("开始爬取财联社加红电报新闻")
            
            # 访问页面
            url = "https://www.cls.cn/telegraph"
            logger.info(f"访问页面: {url}")
            self.driver.get(url)
            
            # 等待页面加载
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            logger.info("页面加载完成，等待6秒...")
            time.sleep(6)
            
            # 点击加红按钮
            click_success = self.click_jiahong_button()
            
            if click_success:
                logger.info("点击成功，等待网络请求...")
                time.sleep(5)
            else:
                logger.warning("点击失败，尝试其他方式...")
                # 尝试滚动页面触发请求
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)
            
            # 获取网络请求日志
            network_requests = self.get_network_logs()
            logger.info(f"捕获到 {len(network_requests)} 个网络请求")
            
            # 处理API数据
            news_data = []
            for request in network_requests:
                url = request['url']
                params = self.extract_params_from_url(url)
                
                if params.get('sign'):
                    logger.info(f"发现API请求，sign: {params.get('sign')}")
                    
                    # 尝试获取数据
                    try:
                        response = self.make_api_request(url)
                        if response and response.get('errno') == 0:
                            roll_data = response.get('data', {}).get('roll_data', [])
                            news_data.extend(roll_data)
                            logger.info(f"成功获取 {len(roll_data)} 条新闻")
                    except Exception as e:
                        logger.warning(f"API请求失败: {e}")
            
            return news_data
            
        except Exception as e:
            logger.error(f"爬取新闻失败: {e}")
            return []
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")

# ==================== 主业务函数 ====================

def crawl_cls_news():
    """爬取财联社新闻的主函数"""
    crawler = None
    try:
        logger.info("开始财联社新闻爬取任务")
        
        # 创建爬虫实例
        crawler = ClsNewsCrawler(headless=True)
        crawler.setup_driver()
        
        # 爬取新闻
        news_data = crawler.crawl_news()
        
        if news_data:
            # 保存到数据库
            new_count, duplicate_count = save_news_to_db(news_data)
            logger.info(f"爬取任务完成: 获取{len(news_data)}条新闻, 新增{new_count}条, 重复{duplicate_count}条")
            return new_count, duplicate_count, len(news_data)
        else:
            logger.warning("未获取到新闻数据")
            return 0, 0, 0
            
    except Exception as e:
        logger.error(f"爬取任务执行失败: {e}")
        logger.error(traceback.format_exc())
        return 0, 0, 0
    finally:
        if crawler:
            crawler.close()

def analyze_latest_news(count=10, prompt=None):
    """分析最新的未分析新闻"""
    if prompt is None:
        prompt = "请分析这条财经新闻是硬消息还是软消息，并简要说明原因。"
    
    try:
        logger.info(f"开始批量AI分析任务 - 数量: {count}")
        
        # 获取最新的未分析新闻
        news_list = get_unanalyzed_news(count)
        
        if not news_list:
            logger.warning("没有找到需要分析的新闻")
            return 0, 0
        
        logger.info(f"获取到 {len(news_list)} 条待分析新闻")
        
        # 异步批量分析
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            results = loop.run_until_complete(batch_analyze_news_async(prompt, news_list))
            
            # 更新数据库
            success_count, failure_count = update_news_analysis_results(results)
            logger.info(f"批量AI分析任务完成: 成功 {success_count} 条, 失败 {failure_count} 条")
            return success_count, failure_count
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error(f"批量分析任务执行失败: {e}")
        logger.error(traceback.format_exc())
        return 0, 0

# ==================== 主程序入口 ====================

def main():
    """主函数"""
    logger.info("=== 财联社新闻爬虫启动 ===")
    
    # 检查命令行参数
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "crawl":
            # 只爬取新闻
            logger.info("执行新闻爬取任务")
            new_count, duplicate_count, total_count = crawl_cls_news()
            logger.info(f"爬取完成: 总获取 {total_count} 条, 新增 {new_count} 条, 重复 {duplicate_count} 条")
            
        elif command == "analyze":
            # 只分析新闻
            count = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            logger.info(f"执行AI分析任务，分析数量: {count}")
            success_count, failure_count = analyze_latest_news(count)
            logger.info(f"分析完成: 成功 {success_count} 条, 失败 {failure_count} 条")
            
        elif command == "full":
            # 完整流程：爬取 + 分析
            logger.info("执行完整流程：爬取 + AI分析")
            
            # 1. 爬取新闻
            new_count, duplicate_count, total_count = crawl_cls_news()
            logger.info(f"爬取完成: 总获取 {total_count} 条, 新增 {new_count} 条, 重复 {duplicate_count} 条")
            
            # 2. 分析新闻（如果有新增的）
            if new_count > 0:
                logger.info(f"开始分析新增的 {new_count} 条新闻")
                success_count, failure_count = analyze_latest_news(new_count)
                logger.info(f"分析完成: 成功 {success_count} 条, 失败 {failure_count} 条")
            else:
                logger.info("没有新增新闻，跳过AI分析")
                
        else:
            print("使用方法:")
            print("  python main.py crawl       - 只爬取新闻")
            print("  python main.py analyze [数量] - 只AI分析最新未分析的新闻")
            print("  python main.py full        - 完整流程：爬取 + AI分析")
            sys.exit(1)
    else:
        # 默认执行完整流程
        logger.info("执行默认完整流程：爬取 + AI分析")
        
        # 1. 爬取新闻
        new_count, duplicate_count, total_count = crawl_cls_news()
        logger.info(f"爬取完成: 总获取 {total_count} 条, 新增 {new_count} 条, 重复 {duplicate_count} 条")
        
        # 2. 分析新闻（如果有新增的）
        if new_count > 0:
            logger.info(f"开始分析新增的 {new_count} 条新闻")
            success_count, failure_count = analyze_latest_news(new_count)
            logger.info(f"分析完成: 成功 {success_count} 条, 失败 {failure_count} 条")
        else:
            logger.info("没有新增新闻，跳过AI分析")
    
    logger.info("=== 任务完成 ===")

if __name__ == '__main__':
    main()