// Content Script (MAIN world) - 在主页面环境中拦截请求
// 通过 postMessage 与 isolated world 通信

(function() {
  'use strict';
  
  // 调试模式开关
  const DEBUG_MODE = true;
  
  const safeLog = (...args) => {
    if (DEBUG_MODE) {
      console.log('[Bloomberg拦截器-主世界]', ...args);
    }
  };
  
  safeLog('═══════════════════════════════════════════════');
  safeLog('🚀 Bloomberg API拦截器已加载 (主世界)');
  safeLog('📍 当前页面:', window.location.href);
  safeLog('⏰ 加载时间:', new Date().toLocaleString('zh-CN'));
  safeLog('═══════════════════════════════════════════════');
  
  const TARGET_API = '/lineup-next/api/stories';
  let requestCounter = 0;
  
  // 判断是否是目标 API（列表请求，不是详情请求）
  const isTargetRequest = (url) => {
    // 必须包含目标 API 路径
    if (!url.includes(TARGET_API)) {
      return false;
    }
    // 必须包含 types 参数（列表请求特征）
    // 不能包含 id 参数（详情请求特征）
    return url.includes('types=') && !url.includes('id=');
  };
  
  // 向 isolated world 发送消息的辅助函数
  const sendToExtension = (data) => {
    window.postMessage({
      source: 'bloomberg-interceptor',
      ...data
    }, '*');
  };
  
  // 拦截 fetch 请求
  const originalFetch = window.fetch;
  safeLog('🔧 正在安装 Fetch 拦截器...');
  
  window.fetch = async function(...args) {
    requestCounter++;
    const requestId = requestCounter;
    const url = typeof args[0] === 'string' ? args[0] : args[0]?.url || '';
    
    safeLog(`📡 [请求 #${requestId}] Fetch 请求:`, url);
    
    // 检查是否匹配目标 API
    const isTargetApi = isTargetRequest(url);
    if (isTargetApi) {
      safeLog(`🎯 [请求 #${requestId}] ✅ 匹配目标列表API!`);
      safeLog(`🎯 [请求 #${requestId}] 完整URL:`, url);
    }
    
    // 调用原始 fetch
    try {
      const response = await originalFetch.apply(this, args);
      safeLog(`✅ [请求 #${requestId}] 响应状态:`, response.status, response.statusText);
      
      // 检查是否是目标 API
      if (isTargetApi) {
        safeLog(`🎯 [请求 #${requestId}] 开始处理目标 API 响应...`);
        
        // 克隆响应以便读取数据
        const clonedResponse = response.clone();
        
        try {
          safeLog(`📦 [请求 #${requestId}] 正在解析 JSON...`);
          const data = await clonedResponse.json();
          safeLog(`📦 [请求 #${requestId}] JSON 解析成功!`);
          safeLog(`📦 [请求 #${requestId}] 数据大小:`, JSON.stringify(data).length, 'bytes');
          
          // 通过 postMessage 发送到 isolated world
          safeLog(`📢 [请求 #${requestId}] 正在发送数据到扩展...`);
          sendToExtension({
            type: 'API_CAPTURED',
            data: {
              capturedData: data,
              capturedUrl: url,
              capturedTime: new Date().toISOString(),
              dataSize: JSON.stringify(data).length
            }
          });
          safeLog(`✅ [请求 #${requestId}] 数据已发送`);
        } catch (e) {
          console.error(`❌ [请求 #${requestId}] 解析 JSON 失败:`, e);
        }
      }
      
      return response;
    } catch (err) {
      console.error(`❌ [请求 #${requestId}] Fetch 请求失败:`, err);
      throw err;
    }
  };
  
  safeLog('✅ Fetch 拦截器安装完成');
  
  // 拦截 XMLHttpRequest
  safeLog('🔧 正在安装 XHR 拦截器...');
  const originalXHROpen = XMLHttpRequest.prototype.open;
  const originalXHRSend = XMLHttpRequest.prototype.send;
  
  XMLHttpRequest.prototype.open = function(method, url, ...rest) {
    this._url = url;
    this._method = method;
    safeLog(`📡 [XHR] 请求准备: ${method} ${url}`);
    return originalXHROpen.apply(this, [method, url, ...rest]);
  };
  
  XMLHttpRequest.prototype.send = function(...args) {
    const isTargetApi = this._url && isTargetRequest(this._url);
    
    if (isTargetApi) {
      safeLog('🎯 [XHR] ✅ 匹配目标列表API:', this._url);
      
      this.addEventListener('load', function() {
        safeLog('✅ [XHR] 响应已接收，状态:', this.status);
        
        try {
          safeLog('📦 [XHR] 正在解析 JSON...');
          const data = JSON.parse(this.responseText);
          safeLog('📦 [XHR] JSON 解析成功!');
          safeLog('📦 [XHR] 数据大小:', this.responseText.length, 'bytes');
          
          safeLog('📢 [XHR] 正在发送数据到扩展...');
          sendToExtension({
            type: 'API_CAPTURED',
            data: {
              capturedData: data,
              capturedUrl: this._url,
              capturedTime: new Date().toISOString(),
              dataSize: this.responseText.length
            }
          });
          safeLog('✅ [XHR] 数据已发送');
        } catch (e) {
          console.error('❌ [XHR] 解析 JSON 失败:', e);
        }
      });
      
      this.addEventListener('error', function() {
        console.error('❌ [XHR] 请求失败');
      });
    }
    
    return originalXHRSend.apply(this, args);
  };
  
  safeLog('✅ XHR 拦截器安装完成');
  safeLog('═══════════════════════════════════════════════');
  safeLog('🎯 监控目标:', TARGET_API);
  safeLog('📋 拦截条件: 包含 types= 参数，不包含 id= 参数');
  safeLog('✅ 拦截器已就绪，等待列表请求...');
  safeLog('═══════════════════════════════════════════════');
  
})();

