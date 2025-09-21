import time
import json
import os
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
import logging
from datetime import datetime
import re

# 配置日志
log_file = '/app/logs/spider.log' if os.path.exists('/app/logs') else 'spider.log'
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class ClsSpider:
    def __init__(self, headless=True, server_mode=False):
        self.driver = None
        self.headless = headless
        self.server_mode = server_mode or self.detect_server_environment()
        self.network_logs = []
        self.collected_data = []
        
        # 服务器模式强制无头运行
        if self.server_mode:
            self.headless = True
            logger.info("检测到服务器环境，强制启用无头模式")
        
    def detect_server_environment(self):
        """检测是否在服务器环境中运行"""
        # 检查是否在Docker容器中
        if os.path.exists('/.dockerenv'):
            return True
            
        # 检查是否有DISPLAY环境变量（Linux图形环境）
        if os.name == 'posix' and not os.environ.get('DISPLAY'):
            return True
            
        # 检查是否在CI/CD环境中
        ci_vars = ['CI', 'CONTINUOUS_INTEGRATION', 'GITHUB_ACTIONS', 'GITLAB_CI']
        if any(os.environ.get(var) for var in ci_vars):
            return True
            
        return False
        
    def setup_driver(self):
        """设置Chrome驱动 - 服务器优化版"""
        chrome_options = Options()
        
        # 强制无头模式
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')
        chrome_options.add_argument('--disable-javascript')  # 如果不需要JS可以禁用
        chrome_options.add_argument('--disable-css')  # 禁用CSS加载
        
        # 服务器环境专用选项
        chrome_options.add_argument('--remote-debugging-port=9222')
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        chrome_options.add_argument('--disable-background-networking')
        chrome_options.add_argument('--disable-default-apps')
        chrome_options.add_argument('--disable-sync')
        chrome_options.add_argument('--metrics-recording-only')
        chrome_options.add_argument('--no-first-run')
        chrome_options.add_argument('--safebrowsing-disable-auto-update')
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        
        # 设置窗口大小
        chrome_options.add_argument('--window-size=1920,1080')
        
        # 用户代理
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 启用网络日志记录
        chrome_options.add_argument('--enable-logging')
        chrome_options.add_argument('--log-level=0')
        chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
        
        # 内存和性能优化
        chrome_options.add_argument('--memory-pressure-off')
        chrome_options.add_argument('--max_old_space_size=4096')
        
        # 尝试不同的Chrome路径
        chrome_paths = [
            '/usr/bin/google-chrome-stable',  # Docker/Linux
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser',
            '/usr/bin/chromium',
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",  # Windows
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ]
        
        chrome_found = False
        for chrome_path in chrome_paths:
            if os.path.exists(chrome_path):
                logger.info(f"找到Chrome浏览器: {chrome_path}")
                chrome_options.binary_location = chrome_path
                chrome_found = True
                break
        
        if not chrome_found:
            logger.warning("未找到Chrome浏览器二进制文件，尝试使用系统默认路径")
        
        try:
            # 首先尝试直接使用Chrome
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Chrome驱动初始化成功")
        except Exception as e:
            logger.warning(f"直接使用Chrome失败: {e}")
            try:
                # 使用webdriver-manager作为备选方案
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                logger.info("使用webdriver-manager初始化Chrome驱动成功")
            except Exception as e2:
                logger.error(f"Chrome驱动初始化失败: {e2}")
                logger.error("请确保已安装Chrome浏览器或在Docker中使用正确的基础镜像")
                raise
        
        # 设置超时时间
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
                    elif message['message']['method'] == 'Network.requestWillBeSent':
                        url = message['message']['params']['request']['url']
                        if 'cls.cn/v1/roll/get_roll_list' in url:
                            network_requests.append({
                                'url': url,
                                'timestamp': log['timestamp'],
                                'request': message['message']['params']['request']
                            })
                except (json.JSONDecodeError, KeyError) as e:
                    logger.debug(f"解析网络日志失败: {e}")
                    continue
            
            return network_requests
        except Exception as e:
            logger.error(f"获取网络日志失败: {e}")
            return []
    
    def extract_params_from_url(self, url):
        """从URL中提取所有参数"""
        params = {}
        if '?' in url:
            query_string = url.split('?')[1]
            for param in query_string.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    params[key] = value
        return params
    
    def click_jiahong_button(self):
        """点击"加红"按钮的服务器优化版本"""
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
            # 基于文本内容的选择器
            "//a[contains(text(), '加红')]",
            "//h3[contains(@class, 'level-2-nav')]//a[contains(text(), '加红')]",
            "//h3[@class='f-l f-s-17 level-2-nav']//a[@class='p-r d-b w-94 c-p c-ef9524']",
            
            # 基于class的选择器
            "//a[@class='p-r d-b w-94 c-p c-ef9524']",
            "//a[contains(@class, 'c-ef9524')]",
            
            # 更广泛的搜索
            "//*[contains(@class, 'level-2-nav')]//*[contains(text(), '加红')]",
            "//nav//*[contains(text(), '加红')]",
            "//*[@class='telegraph-nav']//*[contains(text(), '加红')]",
            
            # CSS选择器备选
            "h3.level-2-nav a",
            "a.c-ef9524",
            ".telegraph-nav a[href*='red']"
        ]
        
        for i, selector in enumerate(selectors):
            try:
                logger.info(f"尝试选择器 {i+1}: {selector}")
                
                if selector.startswith('//') or selector.startswith('/'):
                    # XPath选择器
                    elements = self.driver.find_elements(By.XPATH, selector)
                else:
                    # CSS选择器
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                
                if elements:
                    element = elements[0]
                    element_info = {
                        'tag': element.tag_name,
                        'text': element.text[:50],
                        'class': element.get_attribute('class'),
                        'href': element.get_attribute('href')
                    }
                    logger.info(f"找到元素: {element_info}")
                    
                    # 滚动到元素位置
                    try:
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                        time.sleep(1)
                    except Exception as e:
                        logger.debug(f"滚动到元素失败: {e}")
                    
                    # 尝试多种点击方式
                    click_methods = [
                        lambda: element.click(),
                        lambda: self.driver.execute_script("arguments[0].click();", element),
                        lambda: self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click', {bubbles: true}));", element)
                    ]
                    
                    for j, click_method in enumerate(click_methods):
                        try:
                            click_method()
                            logger.info(f"成功点击'加红'按钮 (方法 {j+1})")
                            return True
                        except Exception as click_error:
                            logger.debug(f"点击方法 {j+1} 失败: {click_error}")
                            continue
                else:
                    logger.debug(f"选择器 {i+1} 未找到元素")
                    
            except Exception as e:
                logger.warning(f"选择器 {i+1} 执行失败: {e}")
                continue
        
        # 最后尝试：查找所有链接中包含"红"字的元素
        try:
            logger.info("尝试查找所有包含'红'字的链接...")
            all_links = self.driver.find_elements(By.TAG_NAME, "a")
            for link in all_links:
                text = link.text.strip()
                href = link.get_attribute('href') or ''
                if ('红' in text or 'red' in text.lower() or 'red' in href.lower()) and len(text) < 10:
                    logger.info(f"找到可能的目标链接: '{text}', href: {href}")
                    try:
                        self.driver.execute_script("arguments[0].click();", link)
                        logger.info(f"成功点击链接: '{text}'")
                        return True
                    except Exception as e:
                        logger.debug(f"点击链接失败: {e}")
                        continue
        except Exception as e:
            logger.warning(f"查找链接失败: {e}")
        
        logger.error("未能找到或点击'加红'按钮")
        return False
    
    def format_news_data(self, news_item):
        """格式化新闻数据"""
        try:
            title = news_item.get('title', '无标题')
            content = news_item.get('content', news_item.get('brief', '无内容'))
            time_str = news_item.get('time', '')
            ctime = news_item.get('ctime', '')
            
            # 格式化时间
            if ctime:
                try:
                    dt = datetime.fromtimestamp(int(ctime))
                    formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                except:
                    formatted_time = time_str or ctime
            else:
                formatted_time = time_str
            
            # 清理HTML标签
            content = re.sub(r'<[^>]+>', '', content)
            title = re.sub(r'<[^>]+>', '', title)
            
            return {
                'title': title,
                'content': content,
                'time': formatted_time,
                'original_time': ctime,
                'raw_data': news_item
            }
        except Exception as e:
            logger.warning(f"格式化新闻数据失败: {e}")
            return {
                'title': '数据解析失败',
                'content': str(news_item),
                'time': '',
                'original_time': '',
                'raw_data': news_item
            }
    
    def save_data_to_txt(self, data, filename_prefix="财联社电报数据"):
        """保存数据到txt文件"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 如果在Docker环境中，保存到data目录
        if self.server_mode and os.path.exists('/app/data'):
            filename = f"/app/data/{filename_prefix}_{timestamp}.txt"
        else:
            filename = f"{filename_prefix}_{timestamp}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write(f"财联社电报数据采集报告\n")
                f.write(f"采集时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"运行环境: {'Docker/服务器' if self.server_mode else '本地'}\n")
                f.write("=" * 80 + "\n\n")
                
                if 'api_data' in data:
                    for i, api_item in enumerate(data['api_data']):
                        f.write(f"【API请求 {i+1}】\n")
                        f.write(f"URL: {api_item.get('url', 'N/A')}\n")
                        f.write(f"Sign: {api_item.get('sign', 'N/A')}\n")
                        f.write(f"Last Time: {api_item.get('last_time', 'N/A')}\n")
                        f.write(f"时间戳: {api_item.get('timestamp', 'N/A')}\n")
                        f.write("-" * 60 + "\n")
                        
                        if api_item.get('data') and 'data' in api_item['data']:
                            roll_data = api_item['data']['data'].get('roll_data', [])
                            f.write(f"新闻数据 ({len(roll_data)}条):\n\n")
                            
                            for j, news in enumerate(roll_data):
                                formatted_news = self.format_news_data(news)
                                f.write(f"  新闻 {j+1}:\n")
                                f.write(f"    标题: {formatted_news['title']}\n")
                                f.write(f"    时间: {formatted_news['time']}\n")
                                f.write(f"    内容: {formatted_news['content'][:200]}{'...' if len(formatted_news['content']) > 200 else ''}\n")
                                f.write(f"    完整内容: {formatted_news['content']}\n")
                                f.write("    " + "-" * 50 + "\n")
                        
                        f.write("\n" + "=" * 80 + "\n\n")
                
                # 保存原始JSON数据
                f.write("【原始JSON数据】\n")
                f.write(json.dumps(data, ensure_ascii=False, indent=2))
                
            logger.info(f"数据已保存到: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"保存数据到txt文件失败: {e}")
            return None
    
    def get_page_data(self, url="https://www.cls.cn/telegraph"):
        """获取页面数据和网络请求 - 服务器优化版"""
        try:
            logger.info(f"访问页面: {url}")
            self.driver.get(url)
            
            # 等待页面加载完成
            try:
                WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                logger.info("页面body元素加载完成")
            except TimeoutException:
                logger.warning("等待页面加载超时，继续执行...")
            
            logger.info("页面加载完成，等待6秒进行充分加载...")
            time.sleep(6)  # 按需求文档等待6秒
            
            # 获取页面基本信息
            try:
                page_title = self.driver.title
                current_url = self.driver.current_url
                logger.info(f"页面标题: {page_title}")
                logger.info(f"当前URL: {current_url}")
            except Exception as e:
                logger.warning(f"获取页面信息失败: {e}")
            
            # 尝试点击"加红"按钮
            click_success = self.click_jiahong_button()
            
            if click_success:
                logger.info("点击成功，等待网络请求...")
                time.sleep(5)  # 等待API请求完成
            else:
                logger.warning("点击失败，继续尝试其他方式触发请求...")
                # 尝试滚动和其他操作来触发请求
                try:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(3)
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(2)
                    
                    # 尝试刷新页面
                    logger.info("尝试刷新页面...")
                    self.driver.refresh()
                    time.sleep(5)
                except Exception as e:
                    logger.warning(f"页面操作失败: {e}")
            
            # 获取页面HTML
            html_content = self.driver.page_source
            logger.info(f"获取到HTML内容，长度: {len(html_content)}")
            
            # 获取网络请求日志
            network_requests = self.get_network_logs()
            logger.info(f"捕获到 {len(network_requests)} 个网络请求")
            
            # 处理API数据
            api_data = []
            for request in network_requests:
                url = request['url']
                params = self.extract_params_from_url(url)
                
                if params.get('sign'):
                    logger.info(f"发现API请求，sign: {params.get('sign')}, last_time: {params.get('last_time')}")
                    api_item = {
                        'url': url,
                        'sign': params.get('sign'),
                        'last_time': params.get('last_time'),
                        'app': params.get('app'),
                        'category': params.get('category'),
                        'timestamp': request['timestamp'],
                        'all_params': params
                    }
                    
                    # 尝试使用相同的请求参数获取数据
                    try:
                        response = self.make_api_request(url)
                        if response:
                            api_item['data'] = response
                            if 'data' in response and 'roll_data' in response['data']:
                                news_count = len(response['data']['roll_data'])
                                logger.info(f"成功获取API数据，包含 {news_count} 条新闻记录")
                            else:
                                logger.info("获取到API响应，但数据格式可能不同")
                    except Exception as e:
                        logger.warning(f"API请求失败: {e}")
                        api_item['error'] = str(e)
                    
                    api_data.append(api_item)
            
            # 如果没有获取到API数据，保存HTML用于调试
            if not api_data:
                if self.server_mode and os.path.exists('/app/data'):
                    debug_file = f"/app/data/debug_html_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                else:
                    debug_file = f"debug_html_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
                try:
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                    logger.info(f"调试HTML已保存到: {debug_file}")
                except Exception as e:
                    logger.warning(f"保存调试HTML失败: {e}")
            
            return {
                'html': html_content,
                'network_requests': network_requests,
                'api_data': api_data,
                'success': len(api_data) > 0,
                'page_title': page_title if 'page_title' in locals() else '',
                'current_url': current_url if 'current_url' in locals() else url
            }
            
        except Exception as e:
            logger.error(f"获取页面数据失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def make_api_request(self, url):
        """使用浏览器的cookies和headers发起API请求"""
        try:
            # 获取浏览器的cookies
            cookies = self.driver.get_cookies()
            cookie_dict = {cookie['name']: cookie['value'] for cookie in cookies}
            
            # 设置请求头（按照需求文档中的headers）
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
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"Linux"'
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
    
    def monitor_real_time(self, duration=60):
        """实时监控网络请求"""
        logger.info(f"开始实时监控，持续{duration}秒")
        
        start_time = time.time()
        collected_data = []
        processed_signs = set()
        
        while time.time() - start_time < duration:
            try:
                # 获取新的网络日志
                logs = self.driver.get_log('performance')
                
                for log in logs:
                    try:
                        message = json.loads(log['message'])
                        if message['message']['method'] == 'Network.responseReceived':
                            url = message['message']['params']['response']['url']
                            if 'cls.cn/v1/roll/get_roll_list' in url:
                                params = self.extract_params_from_url(url)
                                sign = params.get('sign')
                                
                                if sign and sign not in processed_signs:
                                    processed_signs.add(sign)
                                    logger.info(f"实时捕获API请求，sign: {sign}")
                                    
                                    # 尝试获取响应数据
                                    api_response = self.make_api_request(url)
                                    collected_data.append({
                                        'timestamp': time.time(),
                                        'url': url,
                                        'sign': sign,
                                        'params': params,
                                        'data': api_response
                                    })
                    except (json.JSONDecodeError, KeyError):
                        continue
                
                # 模拟用户活动以触发更多请求
                if int(time.time() - start_time) % 15 == 0:  # 每15秒活动一次
                    try:
                        # 随机滚动
                        scroll_height = self.driver.execute_script("return Math.floor(Math.random() * document.body.scrollHeight);")
                        self.driver.execute_script(f"window.scrollTo(0, {scroll_height});")
                        time.sleep(1)
                        
                        # 尝试再次点击加红按钮
                        if int(time.time() - start_time) % 30 == 0:  # 每30秒点击一次
                            self.click_jiahong_button()
                            time.sleep(2)
                    except Exception as e:
                        logger.debug(f"用户活动模拟失败: {e}")
                
                time.sleep(1)  # 每秒检查一次
                
            except Exception as e:
                logger.error(f"监控过程中出错: {e}")
                time.sleep(1)
        
        return collected_data
    
    def close(self):
        """关闭浏览器"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")

def main():
    # 检测运行环境
    server_mode = os.path.exists('/.dockerenv') or not os.environ.get('DISPLAY')
    
    if server_mode:
        print("🐳 检测到Docker/服务器环境")
        print("=" * 60)
        print("🕷️  财联社无头浏览器爬虫 (服务器版)")
        print("=" * 60)
        show_browser = False
    else:
        print("=" * 60)
        print("🕷️  财联社无头浏览器爬虫")
        print("=" * 60)
        print("此程序将模拟真实浏览器环境访问财联社网站")
        print("获取'加红'新闻数据并保存到txt文件")
        print()
        
        show_browser = input("是否显示浏览器界面？(y/N): ").lower().strip() == 'y'
    
    spider = ClsSpider(headless=not show_browser, server_mode=server_mode)
    
    try:
        # 初始化浏览器
        logger.info("正在初始化浏览器...")
        spider.setup_driver()
        
        # 获取页面数据
        logger.info("开始获取财联社电报页面数据...")
        result = spider.get_page_data()
        
        if result and result.get('success'):
            logger.info("🎉 数据获取成功!")
            logger.info(f"📄 HTML内容长度: {len(result['html'])}")
            logger.info(f"🌐 网络请求数量: {len(result['network_requests'])}")
            logger.info(f"📊 API数据数量: {len(result['api_data'])}")
            
            # 保存数据到txt文件
            txt_file = spider.save_data_to_txt(result)
            if txt_file:
                print(f"\n💾 数据已保存到: {txt_file}")
                
                # 显示一些示例数据
                total_news = 0
                for api_item in result['api_data']:
                    if api_item.get('data') and 'data' in api_item['data']:
                        roll_data = api_item['data']['data'].get('roll_data', [])
                        total_news += len(roll_data)
                        
                        print(f"\n📈 API数据预览:")
                        print(f"   Sign: {api_item['sign']}")
                        print(f"   分类: {api_item.get('category', 'N/A')}")
                        print(f"   新闻条数: {len(roll_data)}")
                        
                        # 显示前2条新闻标题
                        for i, news in enumerate(roll_data[:2]):
                            formatted_news = spider.format_news_data(news)
                            print(f"   📰 {i+1}. {formatted_news['title'][:60]}...")
                        
                        if len(roll_data) > 2:
                            print(f"   ... 还有 {len(roll_data)-2} 条新闻")
                        break
                
                print(f"\n📊 总计获取新闻: {total_news} 条")
            
            # 在服务器模式下不询问实时监控
            if not server_mode:
                # 询问是否进行实时监控
                print()
                monitor_choice = input("🔄 是否进行实时监控？(y/N): ").lower().strip()
                if monitor_choice == 'y':
                    duration = input("⏱️  监控时长（秒，默认30）: ").strip()
                    try:
                        duration = int(duration) if duration else 30
                    except ValueError:
                        duration = 30
                    
                    logger.info("开始实时监控...")
                    real_time_data = spider.monitor_real_time(duration=duration)
                    
                    if real_time_data:
                        # 保存实时数据
                        realtime_result = {'api_data': real_time_data}
                        realtime_file = spider.save_data_to_txt(realtime_result, "财联社实时监控数据")
                        print(f"\n💾 实时监控数据已保存到: {realtime_file}")
                        print(f"📊 实时捕获: {len(real_time_data)} 条记录")
        
        elif result:
            logger.warning("⚠️  获取到页面数据但未找到API请求")
            logger.info("可能需要手动检查页面结构或调整策略")
            
            # 仍然保存HTML用于调试
            if server_mode and os.path.exists('/app/data'):
                html_file = f"/app/data/debug_html_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            else:
                html_file = f"debug_html_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(result['html'])
            print(f"🔍 调试HTML已保存到: {html_file}")
        
        else:
            logger.error("❌ 未能获取页面数据，请检查网络连接和网站访问权限")
        
    except Exception as e:
        logger.error(f"💥 程序执行失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    finally:
        spider.close()
        print("\n🔚 程序执行完成")

if __name__ == "__main__":
    main()
