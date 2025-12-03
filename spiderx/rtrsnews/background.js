/**
 * Background Service Worker - 扩展控制中心
 * 职责：
 * 1. 消息路由和调度
 * 2. 与Flask后端通信
 * 3. 状态管理和持久化
 * 4. 错误处理和重试逻辑
 */

const CONFIG = {
  API_BASE_URL: 'http://localhost:1125',
  MAX_RETRY_TIMES: 3,
  RETRY_DELAY: 1000, // 毫秒
  STORAGE_KEY: {
    ARTICLES: 'articles_history',
    SETTINGS: 'scraper_settings',
    STATS: 'scraper_stats'
  }
};

// 初始化扩展
chrome.runtime.onInstalled.addListener(() => {
  console.log('Reuters News Scraper 已安装');
  // 初始化默认配置
  chrome.storage.local.set({
    [CONFIG.STORAGE_KEY.SETTINGS]: {
      autoSave: true,
      apiUrl: CONFIG.API_BASE_URL
    },
    [CONFIG.STORAGE_KEY.STATS]: {
      totalArticles: 0,
      lastSaveTime: null
    }
  });
});

/**
 * 消息路由器 - 处理来自popup和content script的消息
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Background收到消息:', request.action);
  
  switch (request.action) {
    case 'extractContent':
      handleExtractContent(sendResponse);
      return true; // 异步响应
      
    case 'saveArticle':
      handleSaveArticle(request.data, sendResponse);
      return true;
      
    case 'getArticlesList':
      handleGetArticlesList(sendResponse);
      return true;
      
    case 'getSettings':
      handleGetSettings(sendResponse);
      return true;
      
    case 'updateSettings':
      handleUpdateSettings(request.settings, sendResponse);
      return true;
      
    case 'getStats':
      handleGetStats(sendResponse);
      return true;
      
    case 'checkServerHealth':
      handleCheckServerHealth(sendResponse);
      return true;
      
    default:
      sendResponse({ success: false, error: '未知的操作类型' });
      return false;
  }
});

/**
 * 处理内容提取请求
 */
async function handleExtractContent(sendResponse) {
  try {
    // 获取当前活动的tab
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab) {
      sendResponse({ 
        success: false, 
        error: '无法获取当前标签页' 
      });
      return;
    }
    
    // 检查是否是有效的URL
    if (!tab.url || !tab.url.startsWith('http')) {
      sendResponse({ 
        success: false, 
        error: '当前页面不是有效的网页' 
      });
      return;
    }
    
    // 向content script发送提取指令
    const response = await chrome.tabs.sendMessage(tab.id, { 
      action: 'doExtractContent' 
    });
    
    if (response.success) {
      // 组装完整数据
      const articleData = {
        url: tab.url,
        title: tab.title,
        paragraphs: response.data.paragraphs,
        timestamp: new Date().toISOString(),
        count: response.data.count
      };
      
      sendResponse({ 
        success: true, 
        data: articleData 
      });
    } else {
      sendResponse(response);
    }
  } catch (error) {
    console.error('提取内容失败:', error);
    sendResponse({ 
      success: false, 
      error: error.message || '无法连接到页面' 
    });
  }
}

/**
 * 处理保存文章请求（带重试机制）
 */
async function handleSaveArticle(articleData, sendResponse) {
  try {
    // 获取配置
    const settings = await getSettings();
    const apiUrl = settings.apiUrl || CONFIG.API_BASE_URL;
    
    // 尝试保存到服务器
    const result = await saveToServerWithRetry(apiUrl, articleData);
    
    if (result.success) {
      // 更新统计信息
      await updateStats(articleData);
      
      // 保存到本地历史记录（可选）
      await saveToLocalHistory(articleData, result.filename);
      
      sendResponse({
        success: true,
        message: '文章保存成功',
        filename: result.filename,
        paragraph_count: articleData.paragraphs.length
      });
    } else {
      sendResponse({
        success: false,
        error: result.error
      });
    }
  } catch (error) {
    console.error('保存文章失败:', error);
    sendResponse({
      success: false,
      error: error.message
    });
  }
}

/**
 * 带重试机制的保存到服务器
 */
async function saveToServerWithRetry(apiUrl, articleData, retryCount = 0) {
  try {
    const response = await fetch(`${apiUrl}/save-article`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(articleData)
    });
    
    if (!response.ok) {
      throw new Error(`服务器返回错误: ${response.status}`);
    }
    
    const result = await response.json();
    return { success: true, ...result };
    
  } catch (error) {
    console.error(`保存失败 (尝试 ${retryCount + 1}/${CONFIG.MAX_RETRY_TIMES}):`, error);
    
    // 重试逻辑
    if (retryCount < CONFIG.MAX_RETRY_TIMES - 1) {
      await sleep(CONFIG.RETRY_DELAY * (retryCount + 1)); // 递增延迟
      return saveToServerWithRetry(apiUrl, articleData, retryCount + 1);
    }
    
    return { 
      success: false, 
      error: `保存失败（已重试${CONFIG.MAX_RETRY_TIMES}次）: ${error.message}` 
    };
  }
}

/**
 * 获取文章列表
 */
async function handleGetArticlesList(sendResponse) {
  try {
    const settings = await getSettings();
    const apiUrl = settings.apiUrl || CONFIG.API_BASE_URL;
    
    const response = await fetch(`${apiUrl}/articles`);
    const data = await response.json();
    
    sendResponse(data);
  } catch (error) {
    console.error('获取文章列表失败:', error);
    sendResponse({ 
      success: false, 
      error: error.message 
    });
  }
}

/**
 * 获取配置
 */
async function handleGetSettings(sendResponse) {
  const settings = await getSettings();
  sendResponse({ success: true, settings });
}

async function getSettings() {
  const result = await chrome.storage.local.get(CONFIG.STORAGE_KEY.SETTINGS);
  return result[CONFIG.STORAGE_KEY.SETTINGS] || {
    autoSave: true,
    apiUrl: CONFIG.API_BASE_URL
  };
}

/**
 * 更新配置
 */
async function handleUpdateSettings(newSettings, sendResponse) {
  try {
    await chrome.storage.local.set({
      [CONFIG.STORAGE_KEY.SETTINGS]: newSettings
    });
    sendResponse({ success: true });
  } catch (error) {
    sendResponse({ success: false, error: error.message });
  }
}

/**
 * 获取统计信息
 */
async function handleGetStats(sendResponse) {
  const result = await chrome.storage.local.get(CONFIG.STORAGE_KEY.STATS);
  const stats = result[CONFIG.STORAGE_KEY.STATS] || {
    totalArticles: 0,
    lastSaveTime: null
  };
  sendResponse({ success: true, stats });
}

/**
 * 更新统计信息
 */
async function updateStats(articleData) {
  const result = await chrome.storage.local.get(CONFIG.STORAGE_KEY.STATS);
  const stats = result[CONFIG.STORAGE_KEY.STATS] || { totalArticles: 0 };
  
  stats.totalArticles += 1;
  stats.lastSaveTime = new Date().toISOString();
  stats.lastArticleTitle = articleData.title;
  
  await chrome.storage.local.set({
    [CONFIG.STORAGE_KEY.STATS]: stats
  });
}

/**
 * 保存到本地历史记录
 */
async function saveToLocalHistory(articleData, filename) {
  const result = await chrome.storage.local.get(CONFIG.STORAGE_KEY.ARTICLES);
  const history = result[CONFIG.STORAGE_KEY.ARTICLES] || [];
  
  // 添加新记录（保留最近50条）
  history.unshift({
    filename,
    title: articleData.title,
    url: articleData.url,
    paragraphCount: articleData.paragraphs.length,
    savedAt: new Date().toISOString()
  });
  
  // 限制历史记录数量
  if (history.length > 50) {
    history.length = 50;
  }
  
  await chrome.storage.local.set({
    [CONFIG.STORAGE_KEY.ARTICLES]: history
  });
}

/**
 * 检查服务器健康状态
 */
async function handleCheckServerHealth(sendResponse) {
  try {
    const settings = await getSettings();
    const apiUrl = settings.apiUrl || CONFIG.API_BASE_URL;
    
    const response = await fetch(`${apiUrl}/health`, {
      method: 'GET',
      signal: AbortSignal.timeout(3000) // 3秒超时
    });
    
    if (response.ok) {
      const data = await response.json();
      sendResponse({ 
        success: true, 
        status: 'online',
        message: data.message 
      });
    } else {
      throw new Error('服务器响应异常');
    }
  } catch (error) {
    sendResponse({ 
      success: false, 
      status: 'offline',
      error: error.message 
    });
  }
}

// 工具函数
function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

console.log('Background Service Worker 已启动');

