// Popup Main Controller
import * as Storage from './popup-storage.js';
import * as UI from './popup-ui.js';

console.log("[Popup] 脚本加载");

// ==================== DOM 元素 ====================
let elements = {};

document.addEventListener('DOMContentLoaded', () => {
  // 获取所有DOM元素
  elements = {
    taskStatus: document.getElementById('taskStatus'),
    remainingCount: document.getElementById('remainingCount'),
    startTime: document.getElementById('startTime'),
    lastRunTime: document.getElementById('lastRunTime'),
    startBtn: document.getElementById('startBtn'),
    stopBtn: document.getElementById('stopBtn'),
    testBtn: document.getElementById('testBtn'),
    clearBtn: document.getElementById('clearBtn'),
    recordsContainer: document.getElementById('recordsContainer')
  };
  
  // 绑定事件
  elements.startBtn.addEventListener('click', handleStart);
  elements.stopBtn.addEventListener('click', handleStop);
  elements.testBtn.addEventListener('click', handleTest);
  elements.clearBtn.addEventListener('click', handleClear);
  
  // 初始化界面
  initUI();
});

// ==================== 初始化界面 ====================
async function initUI() {
  try {
    const config = await Storage.getTaskConfig();
    const records = await Storage.getExecutionRecords();
    
    UI.updateStatusDisplay(elements, config);
    UI.updateRecordsDisplay(elements.recordsContainer, records);
    UI.updateButtonStates(elements, config);
    
    console.log("[Popup] 界面初始化完成", { config, recordCount: records.length });
  } catch (error) {
    console.error("[Popup] 初始化失败:", error);
  }
}

// ==================== 事件处理 ====================
async function handleStart() {
  console.log("[Popup] 启动任务");
  
  try {
    const config = await Storage.getTaskConfig();
    
    // 检查是否已完成
    if (config.executedDays >= config.totalDays) {
      alert('任务已完成120次，无需再次启动');
      return;
    }
    
    // 更新配置
    const now = Date.now();
    config.isRunning = true;
    if (!config.startTime) {
      config.startTime = now;
    }
    
    await Storage.saveTaskConfig(config);
    
    // 通知 background.js 启动定时器
    chrome.runtime.sendMessage({ action: 'startScheduler' }, (response) => {
      if (chrome.runtime.lastError) {
        console.error("[Popup] 启动失败:", chrome.runtime.lastError);
        alert('启动失败: ' + chrome.runtime.lastError.message);
        return;
      }
      
      if (response && response.success) {
        console.log("[Popup] 任务已启动");
        alert('✅ 定时任务已启动！\n每天6次定时执行，共120次。\n\n下次执行时间: ' + response.nextRunTime);
        initUI(); // 刷新界面
      } else {
        alert('启动失败: ' + (response?.message || '未知错误'));
      }
    });
    
  } catch (error) {
    console.error("[Popup] 启动失败:", error);
    alert('启动失败: ' + error.message);
  }
}

async function handleStop() {
  console.log("[Popup] 停止任务");
  
  if (!confirm('确定要停止定时任务吗？\n（可以随时重新启动）')) {
    return;
  }
  
  try {
    const config = await Storage.getTaskConfig();
    config.isRunning = false;
    await Storage.saveTaskConfig(config);
    
    // 通知 background.js 停止定时器
    chrome.runtime.sendMessage({ action: 'stopScheduler' }, (response) => {
      if (chrome.runtime.lastError) {
        console.error("[Popup] 停止失败:", chrome.runtime.lastError);
        return;
      }
      
      if (response && response.success) {
        console.log("[Popup] 任务已停止");
        alert('✅ 定时任务已停止');
        initUI(); // 刷新界面
      }
    });
    
  } catch (error) {
    console.error("[Popup] 停止失败:", error);
    alert('停止失败: ' + error.message);
  }
}

async function handleTest() {
  console.log("[Popup] 测试执行");
  
  if (!confirm('确定要测试执行一次吗？\n这将立即执行一次任务，不会影响定时任务。')) {
    return;
  }
  
  try {
    // 禁用测试按钮，防止重复点击
    elements.testBtn.disabled = true;
    elements.testBtn.textContent = '测试执行中...';
    
    // 通知 background.js 执行测试
    chrome.runtime.sendMessage({ action: 'testExecute' }, (response) => {
      // 恢复按钮状态
      elements.testBtn.disabled = false;
      elements.testBtn.textContent = '🧪 测试执行一次';
      
      if (chrome.runtime.lastError) {
        console.error("[Popup] 测试失败:", chrome.runtime.lastError);
        alert('测试失败: ' + chrome.runtime.lastError.message);
        return;
      }
      
      if (response && response.success) {
        console.log("[Popup] 测试执行已启动");
        alert('✅ 测试任务已启动！\n请查看控制台日志了解执行进度。');
        // 等待一段时间后刷新界面（给任务执行时间）
        setTimeout(() => {
          initUI();
        }, 2000);
      } else {
        alert('测试失败: ' + (response?.message || '未知错误'));
      }
    });
    
  } catch (error) {
    console.error("[Popup] 测试失败:", error);
    elements.testBtn.disabled = false;
    elements.testBtn.textContent = '🧪 测试执行一次';
    alert('测试失败: ' + error.message);
  }
}

async function handleClear() {
  console.log("[Popup] 清空记录");
  
  if (!confirm('确定要清空所有执行记录吗？\n（此操作不可恢复）')) {
    return;
  }
  
  try {
    await Storage.saveExecutionRecords([]);
    initUI(); // 刷新界面
    console.log("[Popup] 记录已清空");
  } catch (error) {
    console.error("[Popup] 清空失败:", error);
    alert('清空失败: ' + error.message);
  }
}

// 监听来自 background 的消息（用于实时更新界面）
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log("[Popup] 收到消息:", request.action);
  
  if (request.action === 'taskExecuted') {
    // 任务执行完成，刷新界面
    initUI();
  }
});
