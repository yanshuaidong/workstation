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
const TARGET_URL = 'https://www.reuters.com/markets/commodities/';

// 存储当前任务的数据发送结果（用于等待content script回报）
let pendingTaskResult = null;
let taskResultTimeout = null;

// 检查网站是否可达
async function checkWebsiteHealth() {
  console.log('🏥 正在检查Reuters网站健康状态...');
  
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 15000); // 15秒超时
    
    const response = await fetch(TARGET_URL, {
      method: 'HEAD',
      mode: 'no-cors', // 避免CORS问题
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);
    
    // no-cors模式下，response.ok不可靠，但如果没有抛出异常说明能连接
    console.log('✅ Reuters网站可达');
    return { reachable: true, error: null };
  } catch (error) {
    const errorMsg = error.name === 'AbortError' ? '连接超时(15秒)' : error.message;
    console.error('❌ Reuters网站不可达:', errorMsg);
    return { reachable: false, error: errorMsg };
  }
}

// 刷新Reuters页面并拦截数据
async function refreshReutersPage() {
  console.log('═══════════════════════════════════════════════');
  console.log('⏰ 定时任务触发 - 准备刷新Reuters页面');
  console.log('⏰ 触发时间:', new Date().toLocaleString('zh-CN'));
  
  // 初始化任务记录
  const taskRecord = {
    time: new Date().toISOString(),
    success: false,
    websiteReachable: false,
    websiteError: null,
    pageLoaded: false,
    dataSent: false,
    dataCount: 0,
    error: null
  };
  
  try {
    // 1. 首先检查网站是否可达
    const healthCheck = await checkWebsiteHealth();
    taskRecord.websiteReachable = healthCheck.reachable;
    taskRecord.websiteError = healthCheck.error;
    
    if (!healthCheck.reachable) {
      console.error('❌ Reuters网站不可达，跳过刷新');
      taskRecord.error = `网站不可达: ${healthCheck.error}`;
      await addTaskRecord(taskRecord);
      console.log('═══════════════════════════════════════════════');
      return;
    }
    
    // 2. 设置pending状态，等待content script回报数据发送结果
    pendingTaskResult = {
      tabId: null,
      startTime: Date.now(),
      resolve: null
    };
    
    // 创建Promise等待数据发送结果
    const dataResultPromise = new Promise((resolve) => {
      pendingTaskResult.resolve = resolve;
      // 60秒超时（给页面加载和API请求足够时间）
      taskResultTimeout = setTimeout(() => {
        console.warn('⚠️ 等待数据发送结果超时（60秒）');
        resolve({ dataSent: false, dataCount: 0, error: '等待数据超时' });
      }, 60000);
    });
    
    // 3. 查找或创建Reuters标签页
    const reutersTabs = await chrome.tabs.query({ url: 'https://www.reuters.com/*' });
    
    if (reutersTabs.length === 0) {
      console.log('⚠️ 未找到Reuters标签页，尝试打开新标签页...');
      
      const newTab = await chrome.tabs.create({
        url: TARGET_URL,
        active: false
      });
      pendingTaskResult.tabId = newTab.id;
      console.log('✅ 已创建新的Reuters标签页:', newTab.id);
      taskRecord.pageLoaded = true;
    } else {
      console.log(`✅ 找到 ${reutersTabs.length} 个Reuters标签页`);
      
      const targetTab = reutersTabs[0];
      pendingTaskResult.tabId = targetTab.id;
      console.log('🔄 正在刷新标签页:', targetTab.id, targetTab.url);
      
      await chrome.tabs.reload(targetTab.id);
      console.log('✅ 页面刷新命令已发送');
      taskRecord.pageLoaded = true;
    }
    
    // 4. 等待数据发送结果
    console.log('⏳ 等待content script回报数据发送结果...');
    const dataResult = await dataResultPromise;
    
    // 清理超时计时器
    if (taskResultTimeout) {
      clearTimeout(taskResultTimeout);
      taskResultTimeout = null;
    }
    pendingTaskResult = null;
    
    // 5. 更新任务记录
    taskRecord.dataSent = dataResult.dataSent;
    taskRecord.dataCount = dataResult.dataCount || 0;
    if (dataResult.error) {
      taskRecord.error = dataResult.error;
    }
    
    // 只有真正发送了数据才算成功
    taskRecord.success = taskRecord.dataSent && taskRecord.dataCount > 0;
    
    console.log(`📊 任务结果: 成功=${taskRecord.success}, 发送数据=${taskRecord.dataSent}, 数据条数=${taskRecord.dataCount}`);
    
    // 更新最后执行时间
    await chrome.storage.local.set({
      lastAutoRefreshTime: new Date().toISOString(),
      lastTaskSuccess: taskRecord.success,
      lastDataCount: taskRecord.dataCount
    });
    
  } catch (error) {
    console.error('❌ 自动刷新失败:', error);
    taskRecord.error = error.message;
    
    // 清理pending状态
    if (taskResultTimeout) {
      clearTimeout(taskResultTimeout);
      taskResultTimeout = null;
    }
    pendingTaskResult = null;
  }
  
  // 添加执行记录
  await addTaskRecord(taskRecord);
  
  console.log('═══════════════════════════════════════════════');
}

// 添加执行记录（接收详细的任务记录对象）
async function addTaskRecord(taskRecord) {
  const result = await chrome.storage.local.get(['taskRecords']);
  const records = result.taskRecords || [];
  
  // 确保taskRecord是对象格式
  const record = typeof taskRecord === 'object' ? taskRecord : {
    time: new Date().toISOString(),
    success: taskRecord,
    websiteReachable: true,
    websiteError: null,
    pageLoaded: true,
    dataSent: taskRecord,
    dataCount: 0,
    error: null
  };
  
  // 添加新记录到开头（最新的在前面）
  records.unshift(record);
  
  // 最多保留100条记录
  if (records.length > 100) {
    records.pop();
  }
  
  await chrome.storage.local.set({ taskRecords: records });
  
  // 详细日志
  console.log('📝 已添加执行记录:');
  console.log(`   成功: ${record.success ? '✅' : '❌'}`);
  console.log(`   网站可达: ${record.websiteReachable ? '✅' : '❌'} ${record.websiteError || ''}`);
  console.log(`   页面加载: ${record.pageLoaded ? '✅' : '❌'}`);
  console.log(`   数据发送: ${record.dataSent ? '✅' : '❌'}`);
  console.log(`   数据条数: ${record.dataCount}`);
  if (record.error) {
    console.log(`   错误: ${record.error}`);
  }
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
    console.log('   📊 发送数据条数:', request.data.dataCount || 0);
    console.log('   🔗 来源页面:', sender.tab?.url);
    console.log('═══════════════════════════════════════════════');
    
    // 如果有pending的任务在等待结果，通知它
    if (pendingTaskResult && pendingTaskResult.resolve) {
      console.log('📤 通知pending任务数据发送结果...');
      pendingTaskResult.resolve({
        dataSent: request.data.sentToServer,
        dataCount: request.data.dataCount || 0,
        error: request.data.serverError || null
      });
    }
    
    // 设置徽章通知
    const badgeText = request.data.sentToServer ? `${request.data.dataCount || '✓'}` : '!';
    const badgeColor = request.data.sentToServer ? '#4CAF50' : '#F44336';
    
    console.log('🎯 正在设置徽章通知...');
    chrome.action.setBadgeText({ text: badgeText }).then(() => {
      console.log('✅ 徽章文本已设置:', badgeText);
    }).catch(err => {
      console.error('❌ 设置徽章文本失败:', err);
    });
    
    chrome.action.setBadgeBackgroundColor({ color: badgeColor }).then(() => {
      console.log('✅ 徽章颜色已设置');
    }).catch(err => {
      console.error('❌ 设置徽章颜色失败:', err);
    });
    
    // 5秒后清除徽章
    console.log('⏱️ 5秒后将清除徽章...');
    setTimeout(() => {
      chrome.action.setBadgeText({ text: '' });
      console.log('🗑️ 徽章已清除');
    }, 5000);
    
    sendResponse({ success: true });
    console.log('✅ 已回复 content script');
  }
  // 处理网站连接失败的消息
  else if (request.type === 'PAGE_LOAD_FAILED') {
    console.log('═══════════════════════════════════════════════');
    console.log('❌ 页面加载失败!');
    console.log('   错误:', request.data.error);
    console.log('   URL:', request.data.url);
    console.log('═══════════════════════════════════════════════');
    
    // 通知pending任务
    if (pendingTaskResult && pendingTaskResult.resolve) {
      pendingTaskResult.resolve({
        dataSent: false,
        dataCount: 0,
        error: `页面加载失败: ${request.data.error}`
      });
    }
    
    // 设置错误徽章
    chrome.action.setBadgeText({ text: '!' });
    chrome.action.setBadgeBackgroundColor({ color: '#F44336' });
    setTimeout(() => {
      chrome.action.setBadgeText({ text: '' });
    }, 5000);
    
    sendResponse({ success: true });
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
      chrome.storage.local.get(['schedulerEnabled', 'schedulerInterval', 'schedulerStartTime', 'lastAutoRefreshTime', 'lastTaskSuccess', 'lastDataCount']),
      chrome.alarms.get(ALARM_NAME)
    ])
      .then(([config, alarm]) => {
        const status = {
          enabled: config.schedulerEnabled || false,
          interval: config.schedulerInterval || DEFAULT_INTERVAL,
          startTime: config.schedulerStartTime,
          lastRefreshTime: config.lastAutoRefreshTime,
          lastTaskSuccess: config.lastTaskSuccess,
          lastDataCount: config.lastDataCount || 0,
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
  // 手动检查网站健康状态
  else if (request.type === 'CHECK_WEBSITE_HEALTH') {
    console.log('🏥 手动检查网站健康状态');
    checkWebsiteHealth()
      .then(result => {
        console.log('🏥 健康检查结果:', result);
        sendResponse({ success: true, ...result });
      })
      .catch(err => {
        console.error('❌ 健康检查失败:', err);
        sendResponse({ success: false, reachable: false, error: err.message });
      });
    return true; // 异步响应
  }
  // 获取任务执行记录
  else if (request.type === 'GET_TASK_RECORDS') {
    console.log('📋 获取任务执行记录');
    chrome.storage.local.get(['taskRecords'])
      .then(result => {
        const records = result.taskRecords || [];
        console.log(`📋 返回 ${records.length} 条记录`);
        sendResponse({ success: true, records });
      })
      .catch(err => {
        console.error('❌ 获取记录失败:', err);
        sendResponse({ success: false, error: err.message });
      });
    return true; // 异步响应
  }
  // 手动触发一次刷新
  else if (request.type === 'MANUAL_REFRESH') {
    console.log('🔄 手动触发刷新');
    refreshReutersPage()
      .then(() => {
        sendResponse({ success: true });
      })
      .catch(err => {
        console.error('❌ 手动刷新失败:', err);
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
