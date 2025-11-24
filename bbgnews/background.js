// Background service worker
// 用于监听和处理扩展的后台事件

console.log('═══════════════════════════════════════════════');
console.log('🎬 Bloomberg News Interceptor Background Script 启动');
console.log('⏰ 启动时间:', new Date().toLocaleString('zh-CN'));
console.log('═══════════════════════════════════════════════');

chrome.runtime.onInstalled.addListener((details) => {
  console.log('═══════════════════════════════════════════════');
  console.log('✅ Bloomberg News Interceptor 已安装/更新');
  console.log('📝 安装原因:', details.reason);
  console.log('📝 Content Script 将自动在 Bloomberg 页面上运行');
  console.log('🎯 匹配域名: https://www.bloomberg.com/*');
  console.log('⚡ 运行时机: document_start (页面加载前)');
  console.log('═══════════════════════════════════════════════');
});

// 监听来自content script的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('📨 收到消息:', request.type);
  console.log('📍 来源标签页:', sender.tab?.id, sender.tab?.url);
  
  if (request.type === 'API_CAPTURED') {
    console.log('═══════════════════════════════════════════════');
    console.log('🎉 ✅ 收到拦截的API数据!');
    console.log('   📍 URL:', request.data.url);
    console.log('   📦 数据大小:', request.data.dataSize, 'bytes');
    console.log('   ⏰ 拦截时间:', request.data.time);
    console.log('   🔗 来源页面:', sender.tab?.url);
    console.log('═══════════════════════════════════════════════');
    
    // 设置徽章通知
    console.log('🎯 正在设置徽章通知...');
    chrome.action.setBadgeText({ text: '✓' }).then(() => {
      console.log('✅ 徽章文本已设置');
    }).catch(err => {
      console.error('❌ 设置徽章文本失败:', err);
    });
    
    chrome.action.setBadgeBackgroundColor({ color: '#4CAF50' }).then(() => {
      console.log('✅ 徽章颜色已设置');
    }).catch(err => {
      console.error('❌ 设置徽章颜色失败:', err);
    });
    
    // 3秒后清除徽章
    console.log('⏱️ 3秒后将清除徽章...');
    setTimeout(() => {
      chrome.action.setBadgeText({ text: '' });
      console.log('🗑️ 徽章已清除');
    }, 3000);
    
    sendResponse({ success: true });
    console.log('✅ 已回复 content script');
  } else {
    console.log('⚠️ 未知消息类型:', request.type);
    sendResponse({ success: false, error: 'Unknown message type' });
  }
  
  return true;
});

console.log('✅ Background Script 初始化完成，开始监听消息...');
