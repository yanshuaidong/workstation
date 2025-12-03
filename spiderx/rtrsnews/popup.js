/**
 * Popup UI Controller - 扩展弹出界面
 * 职责：
 * 1. 用户界面交互
 * 2. 配置管理
 * 3. 状态展示
 * 4. 历史记录查看
 */

// ==================== 初始化 ====================

document.addEventListener('DOMContentLoaded', () => {
  initUI();
  checkServerHealth();
  loadStats();
  loadSettings();
  
  // 每30秒检查一次服务器状态
  setInterval(checkServerHealth, 30000);
});

// ==================== 标签页切换 ====================

document.querySelectorAll('.tab').forEach(tab => {
  tab.addEventListener('click', (e) => {
    const tabName = e.target.dataset.tab;
    switchTab(tabName);
  });
});

function switchTab(tabName) {
  // 切换标签样式
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');
  
  // 切换内容
  document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
  document.getElementById(`${tabName}Tab`).classList.add('active');
  
  // 加载对应数据
  if (tabName === 'history') {
    loadHistory();
  }
}

// ==================== 提取文章功能 ====================

document.getElementById('extractBtn').addEventListener('click', async () => {
  const button = document.getElementById('extractBtn');
  const btnText = document.getElementById('btnText');
  const messageDiv = document.getElementById('message');
  const previewDiv = document.getElementById('preview');
  
  // 禁用按钮
  button.disabled = true;
  btnText.textContent = '⏳ 提取中...';
  
  // 显示处理信息
  showMessage('正在提取文章内容...', 'info');
  previewDiv.style.display = 'none';
  
  try {
    // 通过background提取内容
    const extractResponse = await sendMessageToBackground({
      action: 'extractContent'
    });
    
    if (!extractResponse.success) {
      throw new Error(extractResponse.error || '提取失败');
    }
    
    const articleData = extractResponse.data;
    
    // 显示预览
    showPreview(articleData);
    
    // 保存文章
    showMessage('正在保存到服务器...', 'info');
    
    const saveResponse = await sendMessageToBackground({
      action: 'saveArticle',
      data: articleData
    });
    
    if (saveResponse.success) {
      showMessage(
        `✓ 成功保存 ${articleData.count} 个段落到 ${saveResponse.filename}`, 
        'success'
      );
      
      // 更新统计信息
      loadStats();
    } else {
      throw new Error(saveResponse.error || '保存失败');
    }
    
  } catch (error) {
    console.error('操作失败:', error);
    showMessage(`✗ ${error.message}`, 'error');
  } finally {
    // 恢复按钮
    button.disabled = false;
    btnText.textContent = '📥 提取当前文章';
  }
});

// ==================== 设置功能 ====================

document.getElementById('saveSettings').addEventListener('click', async () => {
  const apiUrl = document.getElementById('apiUrl').value.trim();
  
  if (!apiUrl) {
    showMessage('请输入API地址', 'error');
    return;
  }
  
  try {
    const response = await sendMessageToBackground({
      action: 'updateSettings',
      settings: {
        apiUrl: apiUrl,
        autoSave: true
      }
    });
    
    if (response.success) {
      showMessage('✓ 设置已保存', 'success');
      checkServerHealth(); // 重新检查服务器
    }
  } catch (error) {
    showMessage(`✗ ${error.message}`, 'error');
  }
});

document.getElementById('testConnection').addEventListener('click', async () => {
  showMessage('正在测试连接...', 'info');
  await checkServerHealth();
});

// ==================== 工具函数 ====================

/**
 * 初始化UI
 */
function initUI() {
  console.log('Popup UI 初始化');
}

/**
 * 检查服务器健康状态
 */
async function checkServerHealth() {
  try {
    const response = await sendMessageToBackground({
      action: 'checkServerHealth'
    });
    
    const statusDot = document.getElementById('serverStatus');
    const statusText = document.getElementById('serverText');
    
    if (response.success && response.status === 'online') {
      statusDot.className = 'status-dot online';
      statusText.textContent = '在线';
    } else {
      statusDot.className = 'status-dot offline';
      statusText.textContent = '离线';
    }
  } catch (error) {
    const statusDot = document.getElementById('serverStatus');
    const statusText = document.getElementById('serverText');
    statusDot.className = 'status-dot offline';
    statusText.textContent = '离线';
  }
}

/**
 * 加载统计信息
 */
async function loadStats() {
  try {
    const response = await sendMessageToBackground({
      action: 'getStats'
    });
    
    if (response.success) {
      document.getElementById('totalArticles').textContent = 
        response.stats.totalArticles || 0;
    }
  } catch (error) {
    console.error('加载统计信息失败:', error);
  }
}

/**
 * 加载设置
 */
async function loadSettings() {
  try {
    const response = await sendMessageToBackground({
      action: 'getSettings'
    });
    
    if (response.success) {
      document.getElementById('apiUrl').value = 
        response.settings.apiUrl || 'http://localhost:1125';
    }
  } catch (error) {
    console.error('加载设置失败:', error);
  }
}

/**
 * 加载历史记录
 */
async function loadHistory() {
  try {
    const response = await sendMessageToBackground({
      action: 'getArticlesList'
    });
    
    const historyList = document.getElementById('historyList');
    
    if (response.success && response.articles && response.articles.length > 0) {
      historyList.innerHTML = response.articles.map(article => `
        <div class="history-item" title="${article.url}">
          <div class="history-title">${escapeHtml(article.title || '无标题')}</div>
          <div class="history-meta">
            ${article.paragraph_count || 0} 个段落 • 
            ${formatDate(article.saved_at)}
          </div>
        </div>
      `).join('');
    } else {
      historyList.innerHTML = `
        <div class="empty-state">
          <div>📚</div>
          <div>暂无历史记录</div>
        </div>
      `;
    }
  } catch (error) {
    console.error('加载历史记录失败:', error);
  }
}

/**
 * 显示预览
 */
function showPreview(articleData) {
  const previewDiv = document.getElementById('preview');
  const { paragraphs, count, totalChars } = articleData;
  
  const previewContent = `
    <strong>提取成功</strong><br>
    共 ${count} 个段落，总字数: ${totalChars || '未知'}<br><br>
    ${paragraphs.slice(0, 3).map((p, i) => `
      <div class="preview-item">
        <strong>段落 ${i + 1}:</strong><br>
        ${escapeHtml(p.substring(0, 150))}${p.length > 150 ? '...' : ''}
      </div>
    `).join('')}
    ${count > 3 ? `<div style="text-align:center;color:#6c757d;"><em>...还有 ${count - 3} 个段落</em></div>` : ''}
  `;
  
  previewDiv.innerHTML = previewContent;
  previewDiv.style.display = 'block';
}

/**
 * 显示消息
 */
function showMessage(text, type = 'info') {
  const messageDiv = document.getElementById('message');
  messageDiv.textContent = text;
  messageDiv.className = `msg-${type}`;
  messageDiv.style.display = 'block';
  
  // 自动隐藏成功消息
  if (type === 'success') {
    setTimeout(() => {
      messageDiv.style.display = 'none';
    }, 3000);
  }
}

/**
 * 发送消息到background
 */
function sendMessageToBackground(message) {
  return new Promise((resolve, reject) => {
    chrome.runtime.sendMessage(message, (response) => {
      if (chrome.runtime.lastError) {
        reject(new Error(chrome.runtime.lastError.message));
      } else {
        resolve(response);
      }
    });
  });
}

/**
 * HTML转义
 */
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}

/**
 * 格式化日期
 */
function formatDate(dateString) {
  if (!dateString) return '未知';
  
  const date = new Date(dateString);
  const now = new Date();
  const diff = now - date;
  
  // 小于1分钟
  if (diff < 60000) {
    return '刚刚';
  }
  // 小于1小时
  if (diff < 3600000) {
    return `${Math.floor(diff / 60000)} 分钟前`;
  }
  // 小于24小时
  if (diff < 86400000) {
    return `${Math.floor(diff / 3600000)} 小时前`;
  }
  // 小于7天
  if (diff < 604800000) {
    return `${Math.floor(diff / 86400000)} 天前`;
  }
  
  // 超过7天，显示具体日期
  return date.toLocaleDateString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
}

console.log('Popup UI 脚本已加载');

