// Background service worker
// 用于监听和处理扩展的后台事件
// 注意：只接收和处理简要信息（时间、状态），不保存具体数据

console.log('═══════════════════════════════════════════════');
console.log('🎬 Bloomberg News Interceptor Background Script 启动');
console.log('⏰ 启动时间:', new Date().toLocaleString('zh-CN'));
console.log('═══════════════════════════════════════════════');

// ==================== 配置 ====================
const ALARM_NAME = 'bloomberg-auto-refresh';
const DEFAULT_INTERVAL = 60; // 默认60分钟（1小时）
const TARGET_URL = 'https://www.bloomberg.com/latest';
const TARGET_URL_PATTERN = 'https://www.bloomberg.com/latest*';

// 跟踪正在监控的标签页，避免重复重定向
const monitoredTabs = new Map(); // tabId -> { lastRedirectTime, redirectCount }
const REDIRECT_COOLDOWN = 5000; // 5秒冷却时间
const MAX_REDIRECTS = 5; // 最大重定向次数
const REDIRECT_DELAY = 2000; // 重定向前等待2秒，模拟人工操作

// 刷新Bloomberg页面并拦截数据
async function refreshBloombergPage() {
  console.log('═══════════════════════════════════════════════');
  console.log('⏰ 定时任务触发 - 准备刷新Bloomberg页面');
  console.log('⏰ 触发时间:', new Date().toLocaleString('zh-CN'));
  console.log('🎯 目标页面:', TARGET_URL);
  
  let success = false;
  
  try {
    // 优先查找 /latest 页面
    let targetTabs = await chrome.tabs.query({ url: TARGET_URL_PATTERN });
    
    if (targetTabs.length === 0) {
      // 如果没有 /latest 页面，查找其他 Bloomberg 页面
      const bloombergTabs = await chrome.tabs.query({ url: 'https://www.bloomberg.com/*' });
      
      if (bloombergTabs.length === 0) {
        console.log('⚠️ 未找到Bloomberg标签页，尝试打开新标签页...');
        
        // 直接打开 /latest 页面
        const newTab = await chrome.tabs.create({
          url: TARGET_URL,
          active: false // 后台打开
        });
        console.log('✅ 已创建新的Bloomberg标签页:', newTab.id);
        console.log('🎯 目标URL:', TARGET_URL);
        
        // 开始监控这个标签页
        startMonitoringTab(newTab.id);
        
        // 等待页面加载完成，content script会自动注入并拦截
        console.log('⏳ 等待页面加载并拦截数据...');
        success = true;
      } else {
        // 有 Bloomberg 页面但不是 /latest，导航到 /latest
        const targetTab = bloombergTabs[0];
        console.log('🔄 发现Bloomberg页面但非/latest，正在导航到目标页面...');
        console.log('   当前URL:', targetTab.url);
        console.log('   目标URL:', TARGET_URL);
        
        await chrome.tabs.update(targetTab.id, { url: TARGET_URL });
        startMonitoringTab(targetTab.id);
        
        console.log('✅ 已导航到 /latest 页面');
        success = true;
      }
    } else {
      console.log(`✅ 找到 ${targetTabs.length} 个Bloomberg /latest 标签页`);
      
      // 刷新第一个 /latest 标签页
      const targetTab = targetTabs[0];
      console.log('🔄 正在刷新标签页:', targetTab.id, targetTab.url);
      
      await chrome.tabs.reload(targetTab.id);
      startMonitoringTab(targetTab.id);
      
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
    
    // 刷新失败时也添加一条记录
    await addCaptureRecord(false, 0, new Date().toISOString());
  }
  
  // 注意：成功时的记录在收到 API_CAPTURED 消息时添加
  
  console.log('═══════════════════════════════════════════════');
}

// ==================== 页面重定向保护 ====================

// 开始监控标签页
function startMonitoringTab(tabId) {
  monitoredTabs.set(tabId, {
    lastRedirectTime: 0,
    redirectCount: 0,
    startTime: Date.now()
  });
  console.log('👁️ 开始监控标签页:', tabId);
}

// 停止监控标签页
function stopMonitoringTab(tabId) {
  monitoredTabs.delete(tabId);
  console.log('🛑 停止监控标签页:', tabId);
}

// 检查是否应该重定向
function shouldRedirect(tabId) {
  const tabInfo = monitoredTabs.get(tabId);
  if (!tabInfo) return false;
  
  const now = Date.now();
  
  // 检查冷却时间
  if (now - tabInfo.lastRedirectTime < REDIRECT_COOLDOWN) {
    console.log('⏳ 重定向冷却中，跳过...');
    return false;
  }
  
  // 检查重定向次数（每10分钟重置）
  if (now - tabInfo.startTime > 600000) {
    tabInfo.redirectCount = 0;
    tabInfo.startTime = now;
  }
  
  if (tabInfo.redirectCount >= MAX_REDIRECTS) {
    console.log('⚠️ 达到最大重定向次数，跳过...');
    return false;
  }
  
  return true;
}

// 记录重定向
function recordRedirect(tabId) {
  const tabInfo = monitoredTabs.get(tabId);
  if (tabInfo) {
    tabInfo.lastRedirectTime = Date.now();
    tabInfo.redirectCount++;
    console.log(`📊 标签页 ${tabId} 重定向次数: ${tabInfo.redirectCount}`);
  }
}

// 检查URL是否是目标页面
function isTargetPage(url) {
  if (!url) return false;
  return url.startsWith('https://www.bloomberg.com/latest');
}

// 检查URL是否是Bloomberg域名
function isBloombergDomain(url) {
  if (!url) return false;
  return url.startsWith('https://www.bloomberg.com/');
}

// 监听标签页URL变化
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  // 只在URL变化且页面加载完成时处理
  if (changeInfo.status !== 'complete') return;
  if (!tab.url) return;
  
  // 检查是否是我们监控的标签页
  if (!monitoredTabs.has(tabId)) {
    // 如果是 Bloomberg 域名但不是目标页面，也尝试处理
    if (isBloombergDomain(tab.url) && !isTargetPage(tab.url)) {
      // 查询是否启用了定时任务
      chrome.storage.local.get(['schedulerEnabled']).then(config => {
        if (config.schedulerEnabled) {
          console.log('═══════════════════════════════════════════════');
          console.log('🔍 检测到Bloomberg页面离开了目标区域');
          console.log('   当前URL:', tab.url);
          console.log('   目标URL:', TARGET_URL);
          
          // 开始监控并尝试重定向
          startMonitoringTab(tabId);
          
          if (shouldRedirect(tabId)) {
            // 添加随机延迟，模拟人工操作
            const delay = REDIRECT_DELAY + Math.random() * 3000;
            console.log(`🔄 ${(delay/1000).toFixed(1)}秒后重定向回目标页面...`);
            
            setTimeout(() => {
              chrome.tabs.update(tabId, { url: TARGET_URL }).then(() => {
                recordRedirect(tabId);
                console.log('✅ 重定向成功');
              }).catch(err => {
                console.error('❌ 重定向失败:', err);
              });
            }, delay);
          }
          console.log('═══════════════════════════════════════════════');
        }
      });
    }
    return;
  }
  
  // 已监控的标签页
  if (!isTargetPage(tab.url) && isBloombergDomain(tab.url)) {
    console.log('═══════════════════════════════════════════════');
    console.log('⚠️ 监控的标签页离开了目标页面!');
    console.log('   标签页ID:', tabId);
    console.log('   当前URL:', tab.url);
    console.log('   目标URL:', TARGET_URL);
    
    if (shouldRedirect(tabId)) {
      // 添加随机延迟，模拟人工操作
      const delay = REDIRECT_DELAY + Math.random() * 3000; // 2-5秒随机延迟
      console.log(`🔄 ${(delay/1000).toFixed(1)}秒后重定向回目标页面...`);
      
      setTimeout(() => {
        chrome.tabs.update(tabId, { url: TARGET_URL }).then(() => {
          recordRedirect(tabId);
          console.log('✅ 重定向成功');
        }).catch(err => {
          console.error('❌ 重定向失败:', err);
        });
      }, delay);
    }
    console.log('═══════════════════════════════════════════════');
  } else if (isTargetPage(tab.url)) {
    console.log('✅ 标签页已在目标页面:', tab.url);
  }
});

// 监听标签页关闭，清理监控数据
chrome.tabs.onRemoved.addListener((tabId) => {
  if (monitoredTabs.has(tabId)) {
    stopMonitoringTab(tabId);
  }
});

// 添加捕获记录（从 content script 收到数据时调用）
async function addCaptureRecord(serverSuccess, newsCount, captureTime) {
  const result = await chrome.storage.local.get(['taskRecords']);
  const records = result.taskRecords || [];
  
  // 添加新记录到开头（最新的在前面）
  records.unshift({
    time: captureTime || new Date().toISOString(),
    success: serverSuccess,
    newsCount: newsCount || 0
  });
  
  // 最多保留100条记录
  if (records.length > 100) {
    records.pop();
  }
  
  await chrome.storage.local.set({ taskRecords: records });
  console.log('📝 已添加捕获记录:', serverSuccess ? '成功' : '失败', '数据条数:', newsCount);
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
  await refreshBloombergPage();
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
    // 添加0-5分钟的随机延迟，避免固定间隔被检测
    const randomDelay = Math.random() * 5 * 60 * 1000; // 0-5分钟
    console.log('🔔 定时器触发:', alarm.name);
    console.log(`⏳ 添加随机延迟: ${(randomDelay/1000/60).toFixed(1)}分钟`);
    
    setTimeout(() => {
      refreshBloombergPage();
    }, randomDelay);
  }
});

// ==================== 原有功能 ====================

chrome.runtime.onInstalled.addListener((details) => {
  console.log('═══════════════════════════════════════════════');
  console.log('✅ Bloomberg News Interceptor 已安装/更新');
  console.log('📝 安装原因:', details.reason);
  console.log('📝 Content Script 将自动在 Bloomberg 页面上运行');
  console.log('🎯 匹配域名: https://www.bloomberg.com/*');
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
    console.log('   📊 数据条数:', request.data.newsCount);
    console.log('   ⏰ 拦截时间:', request.data.time);
    console.log('   🌐 发送到服务器:', request.data.sentToServer ? '✅ 成功' : '❌ 失败');
    console.log('   🔗 来源页面:', sender.tab?.url);
    console.log('═══════════════════════════════════════════════');
    
    // 添加到 taskRecords（记录发送结果和数据条数）
    addCaptureRecord(request.data.sentToServer, request.data.newsCount, request.data.time);
    
    // 设置徽章通知
    console.log('🎯 正在设置徽章通知...');
    const badgeText = request.data.sentToServer ? '✓' : '✗';
    const badgeColor = request.data.sentToServer ? '#4CAF50' : '#f44336';
    
    chrome.action.setBadgeText({ text: badgeText }).then(() => {
      console.log('✅ 徽章文本已设置');
    }).catch(err => {
      console.error('❌ 设置徽章文本失败:', err);
    });
    
    chrome.action.setBadgeBackgroundColor({ color: badgeColor }).then(() => {
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
