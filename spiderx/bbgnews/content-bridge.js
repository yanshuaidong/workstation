// Content Script (ISOLATED world) - 处理 Chrome API 调用
// 接收来自 MAIN world 的消息并保存到 chrome.storage

(function() {
  'use strict';
  
  const DEBUG_MODE = true;
  
  const safeLog = (...args) => {
    if (DEBUG_MODE) {
      console.log('[Bloomberg拦截器-桥接]', ...args);
    }
  };
  
  safeLog('🌉 桥接脚本已加载 (隔离世界)');
  
  // 本地服务器配置
  const LOCAL_SERVER_URL = 'http://localhost:1123/api/capture';
  
  // 过滤数据，只保留需要的字段
  const filterCapturedData = (rawData) => {
    try {
      // 假设 rawData 是一个包含新闻列表的对象
      // 需要找到数组字段并提取所需信息
      let newsArray = [];
      
      // 尝试从不同可能的结构中提取数据
      if (Array.isArray(rawData)) {
        newsArray = rawData;
      } else if (rawData.stories && Array.isArray(rawData.stories)) {
        newsArray = rawData.stories;
      } else if (rawData.data && Array.isArray(rawData.data)) {
        newsArray = rawData.data;
      } else if (rawData.results && Array.isArray(rawData.results)) {
        newsArray = rawData.results;
      }
      
      // 过滤并只保留需要的字段
      const filteredData = newsArray.map(item => ({
        publishedAt: item.publishedAt || item.published_at || item.date || null,
        brand: item.brand || item.source || null,
        headline: item.headline || item.title || null
      })).filter(item => item.headline); // 至少要有标题才保留
      
      safeLog(`📊 数据过滤完成: ${newsArray.length} 条 → ${filteredData.length} 条`);
      
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
    if (message.source !== 'bloomberg-interceptor') {
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

