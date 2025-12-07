// Content Script (ISOLATED world) - 处理 Chrome API 调用
// 接收来自 MAIN world 的消息并保存到 chrome.storage

(function() {
  'use strict';
  
  const DEBUG_MODE = true;
  
  const safeLog = (...args) => {
    if (DEBUG_MODE) {
      console.log('[Reuters拦截器-桥接]', ...args);
    }
  };
  
  safeLog('🌉 桥接脚本已加载 (隔离世界)');
  
  // 本地服务器配置（路透社端口1125）
  const LOCAL_SERVER_URL = 'http://localhost:1125/api/capture';
  
  // Reuters URL前缀
  const REUTERS_URL_PREFIX = 'https://www.reuters.com';
  
  // 过滤数据，只保留需要的字段
  // 从路透社API响应中提取: title, published_time, url
  const filterCapturedData = (rawData) => {
    try {
      let articlesArray = [];
      
      // 路透社API响应结构: { result: { articles: [...] } }
      if (rawData.result && Array.isArray(rawData.result.articles)) {
        articlesArray = rawData.result.articles;
      } else if (Array.isArray(rawData.articles)) {
        articlesArray = rawData.articles;
      } else if (Array.isArray(rawData)) {
        articlesArray = rawData;
      }
      
      // 过滤并只保留需要的字段
      const filteredData = articlesArray.map(item => {
        // 获取URL（需要补全前缀）
        let url = item.canonical_url || item.url || '';
        if (url && !url.startsWith('http')) {
          url = REUTERS_URL_PREFIX + url;
        }
        
        return {
          title: item.title || item.web || item.headline || item.native || null,
          published_time: item.published_time || item.publishedAt || item.updated_time || null,
          url: url
        };
      }).filter(item => item.title && item.published_time); // 至少要有标题和发布时间才保留
      
      safeLog(`📊 数据过滤完成: ${articlesArray.length} 条 → ${filteredData.length} 条`);
      
      return {
        capturedData: filteredData
      };
    } catch (err) {
      console.error('❌ 数据过滤失败:', err);
      return { capturedData: [] };
    }
  };
  
  // 发送数据到本地服务器
  const sendToLocalServer = async (rawData) => {
    try {
      safeLog('🌐 正在发送数据到本地服务器:', LOCAL_SERVER_URL);
      
      // 过滤数据
      const filteredData = filterCapturedData(rawData);
      safeLog('📦 过滤后的数据条数:', filteredData.capturedData.length);
      
      if (filteredData.capturedData.length === 0) {
        safeLog('⚠️ 没有有效数据需要发送');
        return false;
      }
      
      const response = await fetch(LOCAL_SERVER_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(filteredData)
      });
      
      if (response.ok) {
        const result = await response.json();
        safeLog('✅ 数据已发送到本地服务器:', result);
        return true;
      } else {
        console.error('❌ 服务器响应错误:', response.status, response.statusText);
        return false;
      }
    } catch (err) {
      console.error('❌ 发送到本地服务器失败:', err.message);
      return false;
    }
  };
  
  // 监听来自主世界的消息
  window.addEventListener('message', async (event) => {
    // 只处理来自同一窗口的消息
    if (event.source !== window) {
      return;
    }
    
    const message = event.data;
    
    // 检查消息来源
    if (message.source !== 'reuters-interceptor') {
      return;
    }
    
    safeLog('📩 收到消息:', message.type);
    
    if (message.type === 'API_CAPTURED') {
      const { capturedData, capturedUrl, capturedTime, dataSize } = message.data;
      
      safeLog('📦 原始数据大小:', dataSize, 'bytes');
      
      try {
        // 1. 发送到本地服务器（发送过滤后的数据）
        const serverSuccess = await sendToLocalServer(capturedData);
        
        // 2. 浏览器只保存简要信息（时间和状态）
        safeLog('💾 正在保存简要记录到 chrome.storage...');
        await chrome.storage.local.set({
          lastCaptureTime: capturedTime,
          lastCaptureSuccess: serverSuccess,
          lastCaptureUrl: capturedUrl
        });
        
        safeLog('✅ 简要记录已保存到 storage');
        
        // 3. 通知 background script
        safeLog('📢 正在通知 background script...');
        await chrome.runtime.sendMessage({
          type: 'API_CAPTURED',
          data: {
            url: capturedUrl,
            dataSize: dataSize,
            time: capturedTime,
            sentToServer: serverSuccess
          }
        });
        
        safeLog('✅ 已通知 background script');
      } catch (err) {
        console.error('❌ 处理失败:', err);
      }
    }
  });
  
  safeLog('✅ 桥接脚本就绪，等待消息...');
  
})();

