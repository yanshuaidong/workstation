// Content Script (MAIN world) - 在主页面环境中拦截请求
// 通过 postMessage 与 isolated world 通信

(function() {
  'use strict';
  
  console.log('[Reuters拦截器] 已加载');
  
  // 目标API路径
  const TARGET_API = '/pf/api/v3/content/fetch/articles-by-section-alias-or-id-v1';
  let captureCounter = 0;
  
  // 用于检测重复请求的缓存
  const recentRequests = new Map();
  let activeRequests = new Set(); // 正在处理中的请求
  
  // 判断是否是目标 API
  const isTargetRequest = (url) => {
    if (!url.includes(TARGET_API)) {
      return false;
    }
    // 确保是 commodities 相关的请求
    return url.includes('commodities') || url.includes('markets');
  };
  
  // 生成请求指纹（基于URL参数）
  const getRequestFingerprint = (url) => {
    try {
      const urlObj = new URL(url, window.location.origin);
      // 提取query参数
      const queryParam = urlObj.searchParams.get('query');
      if (queryParam) {
        const queryObj = JSON.parse(decodeURIComponent(queryParam));
        return `${queryObj.section_id}_${queryObj.size}_${queryObj.orderby}`;
      }
      return url;
    } catch (e) {
      return url;
    }
  };
  
  // 检查是否应该处理这个请求
  const shouldProcessRequest = (fingerprint) => {
    const now = Date.now();
    
    // 清理超过10秒的旧记录
    for (const [key, timestamp] of recentRequests.entries()) {
      if (now - timestamp > 10000) {
        recentRequests.delete(key);
      }
    }
    
    // 如果正在处理中，拒绝
    if (activeRequests.has(fingerprint)) {
      return { allow: false, reason: '正在处理中' };
    }
    
    // 如果最近处理过（10秒内），拒绝
    if (recentRequests.has(fingerprint)) {
      const lastTime = recentRequests.get(fingerprint);
      const elapsed = now - lastTime;
      return { allow: false, reason: `${elapsed}ms前已处理` };
    }
    
    return { allow: true };
  };
  
  // 向 isolated world 发送消息的辅助函数
  const sendToExtension = (data) => {
    window.postMessage({
      source: 'reuters-interceptor',
      ...data
    }, '*');
  };
  
  // 拦截 fetch 请求
  const originalFetch = window.fetch;
  
  window.fetch = async function(...args) {
    const url = typeof args[0] === 'string' ? args[0] : args[0]?.url || '';
    const isTargetApi = isTargetRequest(url);
    
    // 调用原始 fetch
    try {
      const response = await originalFetch.apply(this, args);
      
      // 只处理目标 API
      if (isTargetApi) {
        const fingerprint = getRequestFingerprint(url);
        
        // 提前检查是否应该处理
        const check = shouldProcessRequest(fingerprint);
        if (!check.allow) {
          console.warn(`[Reuters拦截器] 🚫 跳过重复 (Fetch): ${check.reason}`);
          return response;
        }
        
        // 标记为正在处理
        activeRequests.add(fingerprint);
        
        try {
          const clonedResponse = response.clone();
          const data = await clonedResponse.json();
          const dataSize = JSON.stringify(data).length;
          
          captureCounter++;
          console.log(`[Reuters拦截器] ✅ 捕获 #${captureCounter} (Fetch): ${dataSize} bytes`);
          
          // 记录本次请求
          recentRequests.set(fingerprint, Date.now());
          
          // 发送到扩展
          sendToExtension({
            type: 'API_CAPTURED',
            data: {
              capturedData: data,
              capturedUrl: url,
              capturedTime: new Date().toISOString(),
              dataSize,
              captureMethod: 'fetch',
              captureId: captureCounter
            }
          });
        } catch (e) {
          console.error('[Reuters拦截器] ❌ JSON解析失败:', e.message);
        } finally {
          // 处理完成，移除活动标记
          activeRequests.delete(fingerprint);
        }
      }
      
      return response;
    } catch (err) {
      throw err;
    }
  };
  
  // 拦截 XMLHttpRequest
  const originalXHROpen = XMLHttpRequest.prototype.open;
  const originalXHRSend = XMLHttpRequest.prototype.send;
  
  XMLHttpRequest.prototype.open = function(method, url, ...rest) {
    this._url = url;
    this._method = method;
    return originalXHROpen.apply(this, [method, url, ...rest]);
  };
  
  XMLHttpRequest.prototype.send = function(...args) {
    const isTargetApi = this._url && isTargetRequest(this._url);
    
    if (isTargetApi) {
      const fingerprint = getRequestFingerprint(this._url);
      
      this.addEventListener('load', function() {
        // 检查是否应该处理
        const check = shouldProcessRequest(fingerprint);
        if (!check.allow) {
          console.warn(`[Reuters拦截器] 🚫 跳过重复 (XHR): ${check.reason}`);
          return;
        }
        
        // 标记为正在处理
        activeRequests.add(fingerprint);
        
        try {
          const data = JSON.parse(this.responseText);
          const dataSize = this.responseText.length;
          
          captureCounter++;
          console.log(`[Reuters拦截器] ✅ 捕获 #${captureCounter} (XHR): ${dataSize} bytes`);
          
          // 记录本次请求
          recentRequests.set(fingerprint, Date.now());
          
          sendToExtension({
            type: 'API_CAPTURED',
            data: {
              capturedData: data,
              capturedUrl: this._url,
              capturedTime: new Date().toISOString(),
              dataSize,
              captureMethod: 'xhr',
              captureId: captureCounter
            }
          });
        } catch (e) {
          console.error('[Reuters拦截器] ❌ JSON解析失败:', e.message);
        } finally {
          // 处理完成，移除活动标记
          activeRequests.delete(fingerprint);
        }
      });
    }
    
    return originalXHRSend.apply(this, args);
  };
  
  console.log('[Reuters拦截器] ✅ 已就绪，监控目标:', TARGET_API);
  
})();

