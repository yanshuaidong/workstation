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
  // 返回: { success: boolean, dataCount: number, error: string|null }
  const sendToLocalServer = async (rawData) => {
    try {
      safeLog('🌐 正在发送数据到本地服务器:', LOCAL_SERVER_URL);
      
      // 过滤数据
      const filteredData = filterCapturedData(rawData);
      const dataCount = filteredData.capturedData.length;
      safeLog('📦 过滤后的数据条数:', dataCount);
      
      if (dataCount === 0) {
        safeLog('⚠️ 没有有效数据需要发送');
        return { success: false, dataCount: 0, error: '没有有效数据' };
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
        return { success: true, dataCount: dataCount, error: null };
      } else {
        const errorMsg = `服务器响应错误: ${response.status} ${response.statusText}`;
        console.error('❌', errorMsg);
        return { success: false, dataCount: 0, error: errorMsg };
      }
    } catch (err) {
      const errorMsg = `发送失败: ${err.message}`;
      console.error('❌ 发送到本地服务器失败:', err.message);
      return { success: false, dataCount: 0, error: errorMsg };
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
        const serverResult = await sendToLocalServer(capturedData);
        
        // 2. 浏览器只保存简要信息（时间、状态、数据条数）
        safeLog('💾 正在保存简要记录到 chrome.storage...');
        await chrome.storage.local.set({
          lastCaptureTime: capturedTime,
          lastCaptureSuccess: serverResult.success,
          lastCaptureUrl: capturedUrl,
          lastCaptureDataCount: serverResult.dataCount,
          lastCaptureError: serverResult.error
        });
        
        safeLog('✅ 简要记录已保存到 storage');
        safeLog(`   发送成功: ${serverResult.success}, 数据条数: ${serverResult.dataCount}`);
        
        // 3. 通知 background script（包含数据条数）
        safeLog('📢 正在通知 background script...');
        await chrome.runtime.sendMessage({
          type: 'API_CAPTURED',
          data: {
            url: capturedUrl,
            dataSize: dataSize,
            time: capturedTime,
            sentToServer: serverResult.success,
            dataCount: serverResult.dataCount,
            serverError: serverResult.error
          }
        });
        
        safeLog('✅ 已通知 background script');
      } catch (err) {
        console.error('❌ 处理失败:', err);
        
        // 通知background处理失败
        try {
          await chrome.runtime.sendMessage({
            type: 'API_CAPTURED',
            data: {
              url: capturedUrl,
              dataSize: dataSize,
              time: capturedTime,
              sentToServer: false,
              dataCount: 0,
              serverError: err.message
            }
          });
        } catch (e) {
          console.error('❌ 通知background失败:', e);
        }
      }
    }
  });
  
  // 监听页面加载错误
  window.addEventListener('error', (event) => {
    safeLog('⚠️ 页面错误:', event.message);
  });
  
  // 检测页面是否成功加载（用于检测网络问题）
  if (document.readyState === 'complete') {
    safeLog('✅ 页面已完全加载');
  } else {
    window.addEventListener('load', () => {
      safeLog('✅ 页面加载完成');
    });
    
    // 检测页面加载失败（如网络错误）
    window.addEventListener('error', async (event) => {
      if (event.target === window || event.target === document) {
        console.error('❌ 页面加载失败');
        try {
          await chrome.runtime.sendMessage({
            type: 'PAGE_LOAD_FAILED',
            data: {
              url: window.location.href,
              error: event.message || '页面加载失败'
            }
          });
        } catch (e) {
          console.error('❌ 通知页面加载失败时出错:', e);
        }
      }
    }, true);
  }
  
  safeLog('✅ 桥接脚本就绪，等待消息...');
  
})();

