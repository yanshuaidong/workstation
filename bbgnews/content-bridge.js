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
  
  // 发送数据到本地服务器
  const sendToLocalServer = async (data) => {
    try {
      safeLog('🌐 正在发送数据到本地服务器:', LOCAL_SERVER_URL);
      
      const response = await fetch(LOCAL_SERVER_URL, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
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
      
      safeLog('💾 正在保存到 chrome.storage...');
      safeLog('📦 数据大小:', dataSize, 'bytes');
      
      try {
        // 1. 保存到 chrome.storage（作为备份）
        await chrome.storage.local.set({
          capturedData,
          capturedUrl,
          capturedTime
        });
        
        safeLog('✅ 数据已保存到 storage');
        
        // 2. 发送到本地服务器
        const serverSuccess = await sendToLocalServer({
          capturedData,
          capturedUrl,
          capturedTime,
          dataSize
        });
        
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

