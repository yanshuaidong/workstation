// Background Service Worker - 核心调度逻辑
console.log("[Background] ========== ChatGPT Helper Background Service Worker 已启动 ==========");

// ==================== 常量定义 ====================
const BACKEND_URL = 'http://localhost:1126';
const CHATGPT_URL = 'https://chatgpt.com';
const ALARM_NAME = 'chatgpt_daily_task';
const STORAGE_KEYS = {
  TASK_CONFIG: 'taskConfig',
  EXECUTION_RECORDS: 'executionRecords'
};

// ==================== 插件安装/更新事件 ====================
chrome.runtime.onInstalled.addListener((details) => {
  console.log("[Background] 插件安装/更新事件:", details.reason);
  
  if (details.reason === 'install') {
    console.log("[Background] 首次安装");
    initializeStorage();
  } else if (details.reason === 'update') {
    console.log("[Background] 从版本", details.previousVersion, "更新到当前版本");
  }
  
  // 检查是否有正在运行的任务
  chrome.storage.local.get([STORAGE_KEYS.TASK_CONFIG], (result) => {
    const config = result[STORAGE_KEYS.TASK_CONFIG];
    if (config && config.isRunning) {
      console.log("[Background] 检测到运行中的任务，重新启动定时器");
      handleStartScheduler();
    }
  });
});

// ==================== 初始化存储 ====================
function initializeStorage() {
  const defaultConfig = {
    isRunning: false,
    startTime: null,
    lastRunTime: null,
    executedDays: 0,
    totalDays: 120
  };
  
  chrome.storage.local.set({
    [STORAGE_KEYS.TASK_CONFIG]: defaultConfig,
    [STORAGE_KEYS.EXECUTION_RECORDS]: []
  }, () => {
    console.log("[Background] 存储已初始化");
  });
}

// ==================== 监听来自 Popup 的消息 ====================
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log("[Background] 收到消息:", request.action);
  
  if (request.action === 'startScheduler') {
    handleStartScheduler().then(sendResponse);
    return true; // 异步响应
  }
  
  if (request.action === 'stopScheduler') {
    handleStopScheduler().then(sendResponse);
    return true;
  }
  
  if (request.action === 'saveResult') {
    handleSaveResult(request).then(sendResponse);
    return true;
  }
  
  if (request.action === 'testExecute') {
    handleTestExecute().then(sendResponse);
    return true;
  }
});

// ==================== 启动定时器 ====================
async function handleStartScheduler() {
  try {
    console.log("[Background] 启动定时器...");
    
    // 清除已有的定时器
    await chrome.alarms.clear(ALARM_NAME);
    
    // 定义执行时间点：2点、6点、10点、14点、18点、22点（与Gemini错开2小时）
    const executionHours = [2, 6, 10, 14, 18, 22];
    
    // 找到下一个执行时间
    const now = new Date();
    const currentHour = now.getHours();
    
    let nextHour = executionHours.find(hour => hour > currentHour);
    const nextRun = new Date();
    
    if (nextHour) {
      // 今天还有执行时间
      nextRun.setHours(nextHour, 0, 0, 0);
    } else {
      // 今天没有了，设置为明天第一个执行时间
      nextRun.setDate(nextRun.getDate() + 1);
      nextRun.setHours(executionHours[0], 0, 0, 0);
    }
    
    const delayInMinutes = (nextRun.getTime() - now.getTime()) / (1000 * 60);
    
    // 创建定时器（每4小时执行一次）
    await chrome.alarms.create(ALARM_NAME, {
      delayInMinutes: delayInMinutes,
      periodInMinutes: 4 * 60 // 4小时
    });
    
    console.log("[Background] 定时器已创建");
    console.log("[Background] 执行时间点:", executionHours.join('点、') + '点');
    console.log("[Background] 下次执行时间:", nextRun.toLocaleString('zh-CN'));
    
    return {
      success: true,
      message: '定时器已启动（每天6次：2点、6点、10点、14点、18点、22点）',
      nextRunTime: nextRun.toLocaleString('zh-CN')
    };
    
  } catch (error) {
    console.error("[Background] 启动定时器失败:", error);
    return {
      success: false,
      message: error.message
    };
  }
}

// ==================== 停止定时器 ====================
async function handleStopScheduler() {
  try {
    console.log("[Background] 停止定时器...");
    await chrome.alarms.clear(ALARM_NAME);
    console.log("[Background] 定时器已清除");
    
    return {
      success: true,
      message: '定时器已停止'
    };
    
  } catch (error) {
    console.error("[Background] 停止定时器失败:", error);
    return {
      success: false,
      message: error.message
    };
  }
}

// ==================== 定时器触发事件 ====================
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === ALARM_NAME) {
    console.log("[Background] ========== 定时任务触发 ==========");
    console.log("[Background] 触发时间:", new Date().toLocaleString('zh-CN'));
    
    executeScheduledTask();
  }
});

// ==================== 执行定时任务主流程 ====================
async function executeScheduledTask(isTest = false) {
  console.log(`[Background] 开始执行定时任务${isTest ? ' (测试模式)' : ''}`);
  
  try {
    // 1. 检查任务状态（测试模式下跳过检查）
    const config = await getTaskConfig();
    
    if (!isTest) {
    if (!config.isRunning) {
      console.log("[Background] 任务未运行，跳过执行");
      return;
    }
    
    if (config.executedDays >= config.totalDays) {
      console.log("[Background] 任务已完成，停止执行");
      await handleStopScheduler();
      return;
      }
    }
    
    // 2. 从后端获取待分析任务
    console.log("[Background] 步骤1: 获取待分析任务...");
    const tasksData = await fetchTasksFromBackend();
    
    if (!tasksData.success) {
      throw new Error('获取任务失败: ' + (tasksData.message || '未知错误'));
    }
    
    // 检查是否有任务
    if (!tasksData.tasks || tasksData.tasks.length === 0) {
      console.log("[Background] ⚠️  没有待分析的任务，跳过本次执行");
      return;
    }
    
    const taskList = tasksData.tasks;
    console.log(`[Background] 获取到 ${taskList.length} 个待分析任务`);
    
    // 3. 打开或找到 ChatGPT 标签页
    console.log("[Background] 步骤2: 打开 ChatGPT 标签页...");
    const tabId = await ensureChatGPTTab();
    console.log(`[Background] ChatGPT 标签页 ID: ${tabId}`);
    
    // 等待 Content Script 准备就绪
    console.log("[Background] 等待 Content Script 准备就绪...");
    const isReady = await waitForContentScriptReady(tabId);
    
    if (!isReady) {
      throw new Error('Content Script 未能准备就绪，请刷新 ChatGPT 页面后重试');
    }
    console.log("[Background] Content Script 已准备就绪");
    
    // 4. 逐个处理任务
    console.log("[Background] 步骤3: 开始处理任务...");
    const results = [];
    
    for (let i = 0; i < taskList.length; i++) {
      const task = taskList[i];
      console.log(`[Background] 处理 ${i + 1}/${taskList.length}: ${task.title}`);
      
      try {
        // 执行单个任务 (通过 Content Script)
        const result = await executePrompt(tabId, task.prompt, task.title, task.id);
        results.push({ 
          task_id: task.id,
          title: task.title, 
          success: true, 
          result 
        });
        
        console.log(`[Background] ✓ ${task.title} 执行成功`);
        
        // 等待一下再执行下一个
        await sleep(3000);
        
      } catch (error) {
        console.error(`[Background] ✗ ${task.title} 执行失败:`, error);
        results.push({ 
          task_id: task.id,
          title: task.title, 
          success: false, 
          error: error.message 
        });
      }
    }
    
    // 5. 更新任务配置（测试模式下不更新）
    if (!isTest) {
    config.executedDays += 1;
    config.lastRunTime = Date.now();
    await saveTaskConfig(config);
    } else {
      // 测试模式下只更新 lastRunTime
      config.lastRunTime = Date.now();
      await saveTaskConfig(config);
    }
    
    // 6. 保存执行记录
    await addExecutionRecord({
      time: Date.now(),
      success: results.every(r => r.success),
      results: results,
      isTest: isTest
    });
    
    console.log(`[Background] ========== 定时任务执行完成${isTest ? ' (测试模式)' : ''} ==========`);
    console.log(`[Background] 成功: ${results.filter(r => r.success).length}/${results.length}`);
    
    // 通知 popup 刷新界面
    chrome.runtime.sendMessage({ action: 'taskExecuted' }).catch(() => {
      // Popup 可能未打开，忽略错误
    });
    
    // 如果任务已完成，停止定时器（测试模式下不执行）
    if (!isTest && config.executedDays >= config.totalDays) {
      console.log("[Background] 🎉 所有任务已完成！");
      await handleStopScheduler();
      config.isRunning = false;
      await saveTaskConfig(config);
    }
    
  } catch (error) {
    console.error("[Background] 定时任务执行失败:", error);
    
    // 保存失败记录
    await addExecutionRecord({
      time: Date.now(),
      success: false,
      error: error.message
    });
  }
}

// ==================== 从后端获取待分析任务 ====================
async function fetchTasksFromBackend() {
  try {
    console.log("[Background] 请求后端获取待分析任务...");
    const response = await fetch(`${BACKEND_URL}/get-tasks`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    console.log("[Background] 后端返回:", data);
    
    return data;
    
  } catch (error) {
    console.error("[Background] 获取任务失败:", error);
    return {
      success: false,
      message: error.message,
      count: 0,
      tasks: []
    };
  }
}

// ==================== 确保 ChatGPT 标签页存在 ====================
async function ensureChatGPTTab() {
  // 查找已有的 ChatGPT 标签页
  const tabs = await chrome.tabs.query({ url: [`${CHATGPT_URL}/*`, 'https://chat.openai.com/*'] });
  
  if (tabs.length > 0) {
    const tab = tabs[0];
    console.log("[Background] 找到已有的 ChatGPT 标签页:", tab.id);
    
    // 激活该标签页
    await chrome.tabs.update(tab.id, { active: true });
    await chrome.windows.update(tab.windowId, { focused: true });
    
    return tab.id;
  }
  
  // 没有找到，创建新标签页
  console.log("[Background] 创建新的 ChatGPT 标签页");
  const tab = await chrome.tabs.create({ url: CHATGPT_URL, active: true });
  
  // 等待页面加载
  await waitForTabLoad(tab.id);
  
  return tab.id;
}

// ==================== 等待标签页加载完成 ====================
function waitForTabLoad(tabId) {
  return new Promise((resolve) => {
    const listener = (updatedTabId, changeInfo) => {
      if (updatedTabId === tabId && changeInfo.status === 'complete') {
        chrome.tabs.onUpdated.removeListener(listener);
        console.log("[Background] 标签页加载完成");
        resolve();
      }
    };
    
    chrome.tabs.onUpdated.addListener(listener);
    
    // 超时保护
    setTimeout(() => {
      chrome.tabs.onUpdated.removeListener(listener);
      resolve();
    }, 15000);
  });
}

// ==================== 等待 Content Script 准备就绪 ====================
async function waitForContentScriptReady(tabId, maxRetries = 10) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const isReady = await new Promise((resolve) => {
        chrome.tabs.sendMessage(tabId, { action: 'PING' }, (response) => {
          if (chrome.runtime.lastError) {
            resolve(false);
          } else {
            resolve(response && response.ready);
          }
        });
      });
      
      if (isReady) {
        return true;
      }
      
      console.log(`[Background] Content Script 未就绪，尝试注入... (${i + 1}/${maxRetries})`);
      
      // 尝试注入 Content Script
      if (i === 0 || i === 3) {
        try {
          await chrome.scripting.executeScript({
            target: { tabId: tabId },
            files: ['content-script.js']
          });
          console.log("[Background] Content Script 已手动注入");
        } catch (injectError) {
          console.log("[Background] 注入失败（可能已存在）:", injectError.message);
        }
      }
      
      await sleep(1000);
      
    } catch (error) {
      console.log(`[Background] 检查失败，重试中... (${i + 1}/${maxRetries})`);
      await sleep(1000);
    }
  }
  
  return false;
}

// ==================== 执行单个任务 (通过消息发送给 Content Script) ====================
async function executePrompt(tabId, promptText, title, taskId) {
  console.log(`[Background] 发送消息给 Content Script: ${title} (任务ID: ${taskId})`);
  
  return new Promise((resolve, reject) => {
    chrome.tabs.sendMessage(tabId, {
      action: 'EXECUTE_PROMPT',
      prompt: promptText,
      title: title,
      task_id: taskId
    }, (response) => {
      if (chrome.runtime.lastError) {
        // 可能是 Content Script 还没加载完成，重试一次? 
        // 或者直接报错
        console.error("[Background] 消息发送失败:", chrome.runtime.lastError);
        reject(new Error('无法连接到页面脚本: ' + chrome.runtime.lastError.message));
        return;
      }
      
      if (response && response.success) {
        resolve(response.result);
      } else {
        reject(new Error(response?.error || '执行失败'));
      }
    });
  });
}

// ==================== 测试执行 ====================
async function handleTestExecute() {
  try {
    console.log("[Background] ========== 测试执行开始 ==========");
    
    // 直接执行一次任务（不检查 isRunning 状态，因为是测试）
    await executeScheduledTask(true);
    
    return {
      success: true,
      message: '测试任务已启动'
    };
    
  } catch (error) {
    console.error("[Background] 测试执行失败:", error);
    return {
      success: false,
      message: error.message
    };
  }
}

// ==================== 保存结果（来自手动执行） ====================
async function handleSaveResult(request) {
  try {
    console.log("[Background] 手动保存结果，内容长度:", request.content?.length);
    
    const response = await fetch(`${BACKEND_URL}/save-result`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: request.title || '手动执行',
        content: request.content
      })
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    console.log("[Background] 保存成功:", data);
    
    return {
      success: true,
      message: '结果已保存'
    };
    
  } catch (error) {
    console.error("[Background] 保存失败:", error);
    return {
      success: false,
      message: '无法连接到后端服务: ' + error.message
    };
  }
}

// ==================== 存储操作 ====================
function getTaskConfig() {
  return new Promise((resolve) => {
    chrome.storage.local.get([STORAGE_KEYS.TASK_CONFIG], (result) => {
      resolve(result[STORAGE_KEYS.TASK_CONFIG] || {
        isRunning: false,
        startTime: null,
        lastRunTime: null,
        executedDays: 0,
        totalDays: 120
      });
    });
  });
}

function saveTaskConfig(config) {
  return new Promise((resolve) => {
    chrome.storage.local.set({ [STORAGE_KEYS.TASK_CONFIG]: config }, resolve);
  });
}

function addExecutionRecord(record) {
  return new Promise((resolve) => {
    chrome.storage.local.get([STORAGE_KEYS.EXECUTION_RECORDS], (result) => {
      const records = result[STORAGE_KEYS.EXECUTION_RECORDS] || [];
      records.push(record);
      
      // 最多保留100条记录
      if (records.length > 100) {
        records.shift();
      }
      
      chrome.storage.local.set({ [STORAGE_KEYS.EXECUTION_RECORDS]: records }, resolve);
    });
  });
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

console.log("[Background] 所有函数已加载完成");

