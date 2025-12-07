// Background service worker
// 用于监听和处理扩展的后台事件
// 注意：只接收和处理简要信息（时间、状态），不保存具体数据

console.log('═══════════════════════════════════════════════');
console.log('🎬 Reuters News Interceptor Background Script 启动');
console.log('⏰ 启动时间:', new Date().toLocaleString('zh-CN'));
console.log('═══════════════════════════════════════════════');

// ==================== 定时任务管理 ====================
const ALARM_NAME = 'reuters-auto-refresh';
const DEFAULT_INTERVAL = 60; // 默认60分钟（1小时）

// 刷新Reuters页面并拦截数据
async function refreshReutersPage() {
  console.log('═══════════════════════════════════════════════');
  console.log('⏰ 定时任务触发 - 准备刷新Reuters页面');
  console.log('⏰ 触发时间:', new Date().toLocaleString('zh-CN'));
  
  let success = false;
  
  try {
    // 查找所有Reuters标签页
    const reutersTabs = await chrome.tabs.query({ url: 'https://www.reuters.com/*' });
    
    if (reutersTabs.length === 0) {
      console.log('⚠️ 未找到Reuters标签页，尝试打开新标签页...');
      
      // 打开Reuters Markets Commodities页面（目标页面）
      const newTab = await chrome.tabs.create({
        url: 'https://www.reuters.com/markets/commodities/',
        active: false // 后台打开
      });
      console.log('✅ 已创建新的Reuters标签页:', newTab.id);
      
      // 等待页面加载完成，content script会自动注入并拦截
      console.log('⏳ 等待页面加载并拦截数据...');
      success = true;
    } else {
      console.log(`✅ 找到 ${reutersTabs.length} 个Reuters标签页`);
      
      // 刷新第一个Reuters标签页
      const targetTab = reutersTabs[0];
      console.log('🔄 正在刷新标签页:', targetTab.id, targetTab.url);
      
      await chrome.tabs.reload(targetTab.id);
      console.log('✅ 页面刷新完成，content script将自动拦截数据');
      success = true;
    }
    
    // 更新最后执行时间
    await chrome.storage.local.set({
      lastAutoRefreshTime: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('❌ 自动刷新失败:', error);
    success = false;
  }
  
  // 添加执行记录
  await addTaskRecord(success);
  
  console.log('═══════════════════════════════════════════════');
}

// 添加执行记录
async function addTaskRecord(success) {
  const result = await chrome.storage.local.get(['taskRecords']);
  const records = result.taskRecords || [];
  
  // 添加新记录到开头（最新的在前面）
  records.unshift({
    time: new Date().toISOString(),
    success: success
  });
  
  // 最多保留100条记录
  if (records.length > 100) {
    records.pop();
  }
  
  await chrome.storage.local.set({ taskRecords: records });
  console.log('📝 已添加执行记录:', success ? '成功' : '失败');
}

// 创建或更新定时任务
async function createAlarm(intervalMinutes) {
  console.log('⏰ 创建定时任务，间隔:', intervalMinutes, '分钟');
  
  // 清除已存在的alarm
  await chrome.alarms.clear(ALARM_NAME);
  
  // 创建新的alarm
  await chrome.alarms.create(ALARM_NAME, {
    delayInMinutes: intervalMinutes,
    periodInMinutes: intervalMinutes
  });
  
  // 保存配置
  await chrome.storage.local.set({
    schedulerEnabled: true,
    schedulerInterval: intervalMinutes,
    schedulerStartTime: new Date().toISOString()
  });
  
  console.log('✅ 定时任务已创建');
  
  // 立即执行第一次
  console.log('🚀 立即执行第一次爬虫任务...');
  await refreshReutersPage();
}

// 停止定时任务
async function stopAlarm() {
  console.log('🛑 停止定时任务');
  await chrome.alarms.clear(ALARM_NAME);
  await chrome.storage.local.set({
    schedulerEnabled: false,
    schedulerStopTime: new Date().toISOString()
  });
  console.log('✅ 定时任务已停止');
}

// 监听alarm触发
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === ALARM_NAME) {
    console.log('🔔 定时器触发:', alarm.name);
    refreshReutersPage();
  }
});

// ==================== 原有功能 ====================

chrome.runtime.onInstalled.addListener((details) => {
  console.log('═══════════════════════════════════════════════');
  console.log('✅ Reuters News Interceptor 已安装/更新');
  console.log('📝 安装原因:', details.reason);
  console.log('📝 Content Script 将自动在 Reuters 页面上运行');
  console.log('🎯 匹配域名: https://www.reuters.com/*');
  console.log('⚡ 运行时机: document_start (页面加载前)');
  console.log('═══════════════════════════════════════════════');
});

// 扩展启动时，检查并恢复定时任务
chrome.runtime.onStartup.addListener(async () => {
  console.log('═══════════════════════════════════════════════');
  console.log('🚀 Chrome 启动 - 检查定时任务状态');
  
  try {
    const config = await chrome.storage.local.get(['schedulerEnabled', 'schedulerInterval']);
    
    if (config.schedulerEnabled) {
      const interval = config.schedulerInterval || DEFAULT_INTERVAL;
      console.log('🔄 恢复定时任务，间隔:', interval, '分钟');
      await createAlarm(interval);
      console.log('✅ 定时任务已恢复');
    } else {
      console.log('ℹ️ 定时任务未启用，无需恢复');
    }
  } catch (error) {
    console.error('❌ 恢复定时任务失败:', error);
  }
  
  console.log('═══════════════════════════════════════════════');
});

// 监听来自content script和popup的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('📨 收到消息:', request.type);
  console.log('📍 来源:', sender.tab?.id ? `标签页 ${sender.tab.id}` : 'Popup');
  
  if (request.type === 'API_CAPTURED') {
    console.log('═══════════════════════════════════════════════');
    console.log('🎉 ✅ 收到拦截的API数据!');
    console.log('   📍 URL:', request.data.url);
    console.log('   📦 原始数据大小:', request.data.dataSize, 'bytes');
    console.log('   ⏰ 拦截时间:', request.data.time);
    console.log('   🌐 发送到服务器:', request.data.sentToServer ? '✅ 成功' : '❌ 失败');
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
  } 
  // 处理定时任务控制消息
  else if (request.type === 'START_SCHEDULER') {
    console.log('🟢 收到启动定时任务请求，间隔:', request.interval, '分钟');
    createAlarm(request.interval || DEFAULT_INTERVAL)
      .then(() => {
        console.log('✅ 定时任务启动成功');
        sendResponse({ success: true });
      })
      .catch(err => {
        console.error('❌ 启动定时任务失败:', err);
        sendResponse({ success: false, error: err.message });
      });
    return true; // 异步响应
  } 
  else if (request.type === 'STOP_SCHEDULER') {
    console.log('🔴 收到停止定时任务请求');
    stopAlarm()
      .then(() => {
        console.log('✅ 定时任务停止成功');
        sendResponse({ success: true });
      })
      .catch(err => {
        console.error('❌ 停止定时任务失败:', err);
        sendResponse({ success: false, error: err.message });
      });
    return true; // 异步响应
  }
  else if (request.type === 'GET_SCHEDULER_STATUS') {
    console.log('📊 查询定时任务状态');
    Promise.all([
      chrome.storage.local.get(['schedulerEnabled', 'schedulerInterval', 'schedulerStartTime', 'lastAutoRefreshTime']),
      chrome.alarms.get(ALARM_NAME)
    ])
      .then(([config, alarm]) => {
        const status = {
          enabled: config.schedulerEnabled || false,
          interval: config.schedulerInterval || DEFAULT_INTERVAL,
          startTime: config.schedulerStartTime,
          lastRefreshTime: config.lastAutoRefreshTime,
          nextRefreshTime: alarm ? new Date(alarm.scheduledTime).toISOString() : null
        };
        console.log('📊 定时任务状态:', status);
        sendResponse({ success: true, status });
      })
      .catch(err => {
        console.error('❌ 获取状态失败:', err);
        sendResponse({ success: false, error: err.message });
      });
    return true; // 异步响应
  }
  else {
    console.log('⚠️ 未知消息类型:', request.type);
    sendResponse({ success: false, error: 'Unknown message type' });
  }
  
  return true;
});

console.log('✅ Background Script 初始化完成，开始监听消息...');
