console.log('═══════════════════════════════════════════════');
console.log('📱 Popup 窗口已打开');
console.log('⏰ 打开时间:', new Date().toLocaleString('zh-CN'));
console.log('═══════════════════════════════════════════════');

// 显示状态消息
function showStatus(message, type = 'info') {
  console.log(`📢 状态消息 [${type}]:`, message);
  const statusDiv = document.getElementById('status');
  statusDiv.textContent = message;
  statusDiv.className = `status ${type}`;
  
  // 3秒后自动隐藏
  setTimeout(() => {
    statusDiv.classList.add('hidden');
  }, 3000);
}

// 格式化JSON显示
function displayJSON(data) {
  console.log('🎨 正在格式化显示数据...');
  console.log('📦 原始数据:', data);
  
  const jsonDisplay = document.getElementById('jsonDisplay');
  try {
    const formatted = JSON.stringify(data, null, 2);
    console.log('✅ JSON 格式化成功，字符数:', formatted.length);
    
    jsonDisplay.textContent = formatted;
    
    // 添加时间戳
    const timestamp = document.createElement('div');
    timestamp.className = 'timestamp';
    timestamp.textContent = `\n拦截时间: ${new Date().toLocaleString('zh-CN')}`;
    jsonDisplay.appendChild(timestamp);
    
    console.log('✅ 数据已显示在界面上');
    showStatus('✅ 成功拦截到API响应！', 'success');
  } catch (e) {
    console.error('❌ JSON 格式化失败:', e);
    jsonDisplay.textContent = '解析JSON失败: ' + e.message;
    showStatus('❌ JSON解析失败', 'error');
  }
}

// 刷新页面按钮
document.getElementById('refreshBtn').addEventListener('click', async () => {
  console.log('═══════════════════════════════════════════════');
  console.log('🔄 用户点击了刷新按钮');
  
  try {
    console.log('🔍 正在查询当前标签页...');
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    console.log('📍 当前标签页:', tab.id, tab.url);
    
    if (!tab.url.includes('bloomberg.com')) {
      console.warn('⚠️ 当前不在 Bloomberg 网站');
      showStatus('⚠️ 请在Bloomberg网站上使用此插件', 'error');
      return;
    }
    
    console.log('✅ 在 Bloomberg 网站，准备刷新...');
    showStatus('🔄 正在刷新页面，拦截器已自动激活...', 'info');
    
    // 清除旧数据
    console.log('🗑️ 正在清除旧数据...');
    await chrome.storage.local.remove('capturedData');
    document.getElementById('jsonDisplay').textContent = '';
    console.log('✅ 旧数据已清除');
    
    // 刷新页面（content script 会自动注入）
    console.log('🔄 正在刷新标签页...');
    await chrome.tabs.reload(tab.id);
    console.log('✅ 刷新命令已发送');
    console.log('═══════════════════════════════════════════════');
    
  } catch (error) {
    console.error('❌ 刷新失败:', error);
    showStatus('❌ 操作失败: ' + error.message, 'error');
  }
});

// 清除数据按钮
document.getElementById('clearBtn').addEventListener('click', async () => {
  console.log('═══════════════════════════════════════════════');
  console.log('🗑️ 用户点击了清除按钮');
  console.log('🗑️ 正在清除存储的数据...');
  
  await chrome.storage.local.remove('capturedData');
  document.getElementById('jsonDisplay').textContent = '';
  
  console.log('✅ 数据已清除');
  console.log('═══════════════════════════════════════════════');
  showStatus('🗑️ 数据已清除', 'info');
});

// 监听storage变化，自动更新显示
console.log('👂 开始监听 storage 变化...');
chrome.storage.onChanged.addListener((changes, namespace) => {
  console.log('📢 Storage 发生变化:', namespace, changes);
  
  if (namespace === 'local' && changes.capturedData) {
    const newData = changes.capturedData.newValue;
    console.log('🔔 检测到新的拦截数据!');
    console.log('📦 新数据:', newData);
    
    if (newData) {
      displayJSON(newData);
    }
  }
});

// 页面加载时，检查是否有已保存的数据
console.log('🔍 检查是否有已保存的数据...');
chrome.storage.local.get(['capturedData', 'capturedUrl', 'capturedTime'], (result) => {
  console.log('📦 Storage 中的数据:', result);
  
  if (result.capturedData) {
    console.log('✅ 发现已保存的数据，准备显示...');
    console.log('📍 URL:', result.capturedUrl);
    console.log('⏰ 时间:', result.capturedTime);
    displayJSON(result.capturedData);
  } else {
    console.log('ℹ️ 暂无已保存的数据');
  }
});

// 检查当前标签页
console.log('🔍 检查当前标签页...');
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  if (tabs[0]) {
    const url = tabs[0].url;
    console.log('📍 当前标签页 URL:', url);
    
    if (!url.includes('bloomberg.com')) {
      console.warn('⚠️ 当前不在 Bloomberg 网站');
      showStatus('ℹ️ 请导航到 bloomberg.com 网站', 'info');
    } else {
      console.log('✅ 当前在 Bloomberg 网站');
    }
  }
});

console.log('✅ Popup 初始化完成');
console.log('═══════════════════════════════════════════════');

