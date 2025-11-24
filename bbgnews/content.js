// Content Script - 在Bloomberg页面加载时自动注入
// 拦截 fetch 和 XMLHttpRequest 请求

(function() {
  'use strict';
  
  // 调试模式开关 - 设为 false 可关闭所有日志
  const DEBUG_MODE = true;  // 改为 false 进入隐蔽模式
  
  // 安全的日志函数 - 只在调试模式下输出
  const safeLog = (...args) => {
    if (DEBUG_MODE) {
      console.log(...args);
    }
  };
  
  safeLog('═══════════════════════════════════════════════');
  safeLog('🚀 Bloomberg API拦截器已加载');
  safeLog('📍 当前页面:', window.location.href);
  safeLog('⏰ 加载时间:', new Date().toLocaleString('zh-CN'));
  safeLog('═══════════════════════════════════════════════');
  
  const TARGET_API = '/lineup-next/api/stories';
  let requestCounter = 0;
  
  // 拦截 fetch 请求
  const originalFetch = window.fetch;
  safeLog('🔧 正在安装 Fetch 拦截器...');
  
  window.fetch = async function(...args) {
    requestCounter++;
    const requestId = requestCounter;
    const url = typeof args[0] === 'string' ? args[0] : args[0]?.url || '';
    
    safeLog(`📡 [请求 #${requestId}] Fetch 请求:`, url);
    
    // 检查是否匹配目标 API
    const isTargetApi = url.includes(TARGET_API);
    if (isTargetApi) {
      safeLog(`🎯 [请求 #${requestId}] ✅ 匹配目标 API!`);
      safeLog(`🎯 [请求 #${requestId}] 完整URL:`, url);
    } else {
      safeLog(`📡 [请求 #${requestId}] ❌ 不匹配 (需要包含: ${TARGET_API})`);
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
          safeLog(`📦 [请求 #${requestId}] 数据内容:`, data);
          
          // 保存到 chrome.storage
          safeLog(`💾 [请求 #${requestId}] 正在保存到 storage...`);
          chrome.storage.local.set({ 
            capturedData: data,
            capturedUrl: url,
            capturedTime: new Date().toISOString()
          }).then(() => {
            safeLog(`✅ [请求 #${requestId}] 数据已保存到 storage`);
            
            // 通知 background script
            safeLog(`📢 [请求 #${requestId}] 正在通知 background script...`);
            chrome.runtime.sendMessage({
              type: 'API_CAPTURED',
              data: {
                url: url,
                dataSize: JSON.stringify(data).length,
                time: new Date().toISOString()
              }
            }).then(() => {
              safeLog(`✅ [请求 #${requestId}] 已通知 background script`);
            }).catch(err => {
              // 错误总是要记录的
              console.error(`❌ [请求 #${requestId}] 通知 background 失败:`, err);
            });
          }).catch(err => {
            console.error(`❌ [请求 #${requestId}] 保存到storage失败:`, err);
          });
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
    const isTargetApi = this._url && this._url.includes(TARGET_API);
    
    if (isTargetApi) {
      safeLog('🎯 [XHR] ✅ 匹配目标 API:', this._url);
      
      this.addEventListener('load', function() {
        safeLog('✅ [XHR] 响应已接收，状态:', this.status);
        
        try {
          safeLog('📦 [XHR] 正在解析 JSON...');
          const data = JSON.parse(this.responseText);
          safeLog('📦 [XHR] JSON 解析成功!');
          safeLog('📦 [XHR] 数据大小:', this.responseText.length, 'bytes');
          safeLog('📦 [XHR] 数据内容:', data);
          
          safeLog('💾 [XHR] 正在保存到 storage...');
          chrome.storage.local.set({ 
            capturedData: data,
            capturedUrl: this._url,
            capturedTime: new Date().toISOString()
          }).then(() => {
            safeLog('✅ [XHR] 数据已保存到 storage');
            
            chrome.runtime.sendMessage({
              type: 'API_CAPTURED',
              data: {
                url: this._url,
                dataSize: this.responseText.length,
                time: new Date().toISOString()
              }
            }).then(() => {
              safeLog('✅ [XHR] 已通知 background script');
            }).catch(err => {
              console.error('❌ [XHR] 通知 background 失败:', err);
            });
          }).catch(err => {
            console.error('❌ [XHR] 保存到storage失败:', err);
          });
        } catch (e) {
          console.error('❌ [XHR] 解析 JSON 失败:', e);
        }
      });
      
      this.addEventListener('error', function() {
        console.error('❌ [XHR] 请求失败');
      });
    } else {
      safeLog('📡 [XHR] ❌ 不匹配:', this._url);
    }
    
    return originalXHRSend.apply(this, args);
  };
  
  safeLog('✅ XHR 拦截器安装完成');
  safeLog('═══════════════════════════════════════════════');
  safeLog('🎯 监控目标 API:', TARGET_API);
  safeLog('✅ 拦截器已就绪，等待 API 请求...');
  safeLog('💡 提示: 所有网络请求都会被记录，匹配目标 API 的会被拦截');
  safeLog('═══════════════════════════════════════════════');
  
})();

