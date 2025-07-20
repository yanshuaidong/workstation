import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import json

class HttpClient:
    """HTTP 客户端工具类"""
    
    def __init__(self, timeout=30, retries=3):
        """
        初始化 HTTP 客户端
        
        Args:
            timeout: 请求超时时间（秒）
            retries: 重试次数
        """
        self.timeout = timeout
        self.session = requests.Session()
        
        # 配置重试策略
        retry_strategy = Retry(
            total=retries,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def get(self, url, params=None, headers=None):
        """GET 请求"""
        try:
            response = self.session.get(
                url, 
                params=params, 
                headers=headers, 
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json() if response.content else None
        except requests.exceptions.RequestException as e:
            raise Exception(f"GET 请求失败: {str(e)}")
    
    def post(self, url, data=None, json_data=None, headers=None):
        """POST 请求"""
        try:
            response = self.session.post(
                url, 
                data=data, 
                json=json_data, 
                headers=headers, 
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json() if response.content else None
        except requests.exceptions.RequestException as e:
            raise Exception(f"POST 请求失败: {str(e)}")
    
    def put(self, url, data=None, json_data=None, headers=None):
        """PUT 请求"""
        try:
            response = self.session.put(
                url, 
                data=data, 
                json=json_data, 
                headers=headers, 
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json() if response.content else None
        except requests.exceptions.RequestException as e:
            raise Exception(f"PUT 请求失败: {str(e)}")
    
    def delete(self, url, headers=None):
        """DELETE 请求"""
        try:
            response = self.session.delete(
                url, 
                headers=headers, 
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json() if response.content else None
        except requests.exceptions.RequestException as e:
            raise Exception(f"DELETE 请求失败: {str(e)}")
    
    def close(self):
        """关闭会话"""
        self.session.close() 