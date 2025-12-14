console.log('═══════════════════════════════════════════════');
console.log('📱 Popup 窗口已打开');
console.log('⏰ 打开时间:', new Date().toLocaleString('zh-CN'));
console.log('═══════════════════════════════════════════════');

// ==================== 定时任务功能 ====================

// 格式化时间显示
function formatTime(isoString) {
  if (!isoString) return '-';
  const date = new Date(isoString);
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

// 格式化短时间（只显示时分秒）
function formatShortTime(isoString) {
  if (!isoString) return '-';
  const date = new Date(isoString);
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
}

// 生成状态徽章HTML
function getBadgeHtml(isSuccess, successText = '✓', failText = '✗') {
  if (isSuccess === undefined || isSuccess === null) {
    return '<span class="badge badge-warning">-</span>';
  }
  return isSuccess 
    ? `<span class="badge badge-success">${successText}</span>`
    : `<span class="badge badge-fail">${failText}</span>`;
}

// 更新执行记录表格（详细版）
async function updateRecordsTable() {
  const result = await chrome.storage.local.get(['taskRecords']);
  const records = result.taskRecords || [];
  
  const tbody = document.getElementById('recordsTableBody');
  
  if (records.length === 0) {
    tbody.innerHTML = '<tr><td colspan="8" class="empty-records">暂无执行记录</td></tr>';
    return;
  }
  
  // 最新的记录在上面，显示详细信息
  tbody.innerHTML = records.map((record, index) => {
    // 兼容旧格式的记录
    const websiteReachable = record.websiteReachable !== undefined ? record.websiteReachable : true;
    const pageLoaded = record.pageLoaded !== undefined ? record.pageLoaded : true;
    const dataSent = record.dataSent !== undefined ? record.dataSent : record.success;
    const dataCount = record.dataCount !== undefined ? record.dataCount : '-';
    const error = record.error || record.websiteError || '';
    
    return `
      <tr>
        <td>${records.length - index}</td>
        <td>${formatShortTime(record.time)}</td>
        <td>${getBadgeHtml(websiteReachable, '可达', '不可达')}</td>
        <td>${getBadgeHtml(pageLoaded, '✓', '✗')}</td>
        <td>${getBadgeHtml(dataSent, '✓', '✗')}</td>
        <td class="data-count">${dataCount}</td>
        <td>${getBadgeHtml(record.success, '成功', '失败')}</td>
        <td class="error-cell" title="${error}">${error || '-'}</td>
      </tr>
    `;
  }).join('');
}

// 更新健康状态显示
async function updateHealthStatus() {
  console.log('🏥 更新健康状态显示...');
  
  try {
    const result = await chrome.storage.local.get([
      'lastTaskSuccess', 
      'lastDataCount',
      'lastCaptureSuccess',
      'lastCaptureDataCount',
      'lastCaptureError'
    ]);
    
    const lastTaskResultText = document.getElementById('lastTaskResultText');
    const lastDataCountText = document.getElementById('lastDataCountText');
    
    // 上次任务结果
    if (result.lastTaskSuccess !== undefined) {
      if (result.lastTaskSuccess) {
        lastTaskResultText.textContent = '✅ 成功';
        lastTaskResultText.className = 'status-value active';
      } else {
        lastTaskResultText.textContent = '❌ 失败';
        lastTaskResultText.className = 'status-value error';
      }
    }
    
    // 上次发送数据条数
    if (result.lastDataCount !== undefined) {
      lastDataCountText.textContent = `${result.lastDataCount} 条`;
      lastDataCountText.className = result.lastDataCount > 0 ? 'status-value active' : 'status-value warning';
    } else if (result.lastCaptureDataCount !== undefined) {
      lastDataCountText.textContent = `${result.lastCaptureDataCount} 条`;
      lastDataCountText.className = result.lastCaptureDataCount > 0 ? 'status-value active' : 'status-value warning';
    }
    
  } catch (error) {
    console.error('❌ 更新健康状态失败:', error);
  }
}

// 更新定时任务状态显示
async function updateSchedulerStatus() {
  console.log('🔄 更新定时任务状态...');
  
  try {
    const response = await chrome.runtime.sendMessage({ type: 'GET_SCHEDULER_STATUS' });
    
    if (response.success) {
      const { status } = response;
      console.log('📊 定时任务状态:', status);
      
      // 更新UI
      const statusText = document.getElementById('statusText');
      const startTimeText = document.getElementById('startTimeText');
      const lastRefreshText = document.getElementById('lastRefreshText');
      const nextRefreshText = document.getElementById('nextRefreshText');
      const startBtn = document.getElementById('startSchedulerBtn');
      const stopBtn = document.getElementById('stopSchedulerBtn');
      const intervalInput = document.getElementById('intervalInput');
      
      if (status.enabled) {
        statusText.textContent = '🟢 运行中';
        statusText.className = 'status-value active';
        startBtn.disabled = true;
        stopBtn.disabled = false;
        intervalInput.disabled = true;
        intervalInput.value = status.interval;
      } else {
        statusText.textContent = '⚪ 未启动';
        statusText.className = 'status-value inactive';
        startBtn.disabled = false;
        stopBtn.disabled = true;
        intervalInput.disabled = false;
      }
      
      startTimeText.textContent = formatTime(status.startTime);
      lastRefreshText.textContent = formatTime(status.lastRefreshTime);
      nextRefreshText.textContent = formatTime(status.nextRefreshTime);
      
      // 更新健康状态显示（使用status中的信息）
      const lastTaskResultText = document.getElementById('lastTaskResultText');
      const lastDataCountText = document.getElementById('lastDataCountText');
      
      if (status.lastTaskSuccess !== undefined) {
        if (status.lastTaskSuccess) {
          lastTaskResultText.textContent = '✅ 成功';
          lastTaskResultText.className = 'status-value active';
        } else {
          lastTaskResultText.textContent = '❌ 失败';
          lastTaskResultText.className = 'status-value error';
        }
      }
      
      if (status.lastDataCount !== undefined) {
        lastDataCountText.textContent = `${status.lastDataCount} 条`;
        lastDataCountText.className = status.lastDataCount > 0 ? 'status-value active' : 'status-value warning';
      }
      
      console.log('✅ 状态显示已更新');
    }
  } catch (error) {
    console.error('❌ 更新状态失败:', error);
  }
}

// ==================== 健康检查功能 ====================

// 检查网站健康状态
document.getElementById('checkHealthBtn').addEventListener('click', async () => {
  console.log('═══════════════════════════════════════════════');
  console.log('🏥 检查网站健康状态');
  
  const btn = document.getElementById('checkHealthBtn');
  const websiteHealthText = document.getElementById('websiteHealthText');
  
  btn.disabled = true;
  btn.textContent = '⏳ 检测中...';
  websiteHealthText.textContent = '检测中...';
  websiteHealthText.className = 'status-value';
  
  try {
    const response = await chrome.runtime.sendMessage({ type: 'CHECK_WEBSITE_HEALTH' });
    
    if (response.reachable) {
      websiteHealthText.textContent = '✅ 可达';
      websiteHealthText.className = 'status-value active';
      console.log('✅ 网站可达');
    } else {
      websiteHealthText.textContent = `❌ 不可达: ${response.error || '未知错误'}`;
      websiteHealthText.className = 'status-value error';
      console.log('❌ 网站不可达:', response.error);
    }
  } catch (error) {
    websiteHealthText.textContent = `❌ 检测失败: ${error.message}`;
    websiteHealthText.className = 'status-value error';
    console.error('❌ 检测失败:', error);
  } finally {
    btn.disabled = false;
    btn.textContent = '🔍 检查网站状态';
  }
  
  console.log('═══════════════════════════════════════════════');
});

// 手动刷新一次
document.getElementById('manualRefreshBtn').addEventListener('click', async () => {
  console.log('═══════════════════════════════════════════════');
  console.log('🔄 手动刷新一次');
  
  const btn = document.getElementById('manualRefreshBtn');
  
  btn.disabled = true;
  btn.textContent = '⏳ 刷新中...';
  
  try {
    const response = await chrome.runtime.sendMessage({ type: 'MANUAL_REFRESH' });
    
    if (response.success) {
      console.log('✅ 手动刷新已触发');
      // 等待一下再更新状态，让background有时间处理
      setTimeout(async () => {
        await updateSchedulerStatus();
        await updateRecordsTable();
        await updateHealthStatus();
      }, 2000);
    } else {
      console.error('❌ 手动刷新失败:', response.error);
      alert('刷新失败: ' + response.error);
    }
  } catch (error) {
    console.error('❌ 手动刷新出错:', error);
    alert('刷新失败: ' + error.message);
  } finally {
    btn.disabled = false;
    btn.textContent = '🔄 手动刷新一次';
  }
  
  console.log('═══════════════════════════════════════════════');
});

// 启动定时任务
document.getElementById('startSchedulerBtn').addEventListener('click', async () => {
  console.log('═══════════════════════════════════════════════');
  console.log('▶️ 启动定时任务');
  
  const interval = parseInt(document.getElementById('intervalInput').value);
  
  if (!interval || interval < 1 || interval > 1440) {
    alert('请输入有效的时间间隔（1-1440分钟）');
    return;
  }
  
  console.log('⏰ 设置间隔:', interval, '分钟');
  
  try {
    const response = await chrome.runtime.sendMessage({
      type: 'START_SCHEDULER',
      interval: interval
    });
    
    if (response.success) {
      console.log('✅ 定时任务启动成功，已立即执行第一次');
      await updateSchedulerStatus();
      await updateRecordsTable();
    } else {
      console.error('❌ 启动失败:', response.error);
      alert('启动失败: ' + response.error);
    }
  } catch (error) {
    console.error('❌ 启动定时任务出错:', error);
    alert('启动失败: ' + error.message);
  }
  
  console.log('═══════════════════════════════════════════════');
});

// 停止定时任务
document.getElementById('stopSchedulerBtn').addEventListener('click', async () => {
  console.log('═══════════════════════════════════════════════');
  console.log('⏸️ 停止定时任务');
  
  try {
    const response = await chrome.runtime.sendMessage({ type: 'STOP_SCHEDULER' });
    
    if (response.success) {
      console.log('✅ 定时任务已停止');
      await updateSchedulerStatus();
    } else {
      console.error('❌ 停止失败:', response.error);
      alert('停止失败: ' + response.error);
    }
  } catch (error) {
    console.error('❌ 停止定时任务出错:', error);
    alert('停止失败: ' + error.message);
  }
  
  console.log('═══════════════════════════════════════════════');
});

// 清空执行记录
document.getElementById('clearRecordsBtn').addEventListener('click', async () => {
  if (confirm('确定要清空所有执行记录吗？')) {
    await chrome.storage.local.set({ taskRecords: [] });
    await updateRecordsTable();
    console.log('✅ 执行记录已清空');
  }
});

// ==================== 测试功能 ====================

// 测试按钮 - 立即处理所有待处理新闻
document.getElementById('testProcessBtn').addEventListener('click', async () => {
  console.log('═══════════════════════════════════════════════');
  console.log('🧪 测试：立即处理所有待处理新闻');
  
  const btn = document.getElementById('testProcessBtn');
  const resultDiv = document.getElementById('testResult');
  
  // 禁用按钮，显示加载状态
  btn.disabled = true;
  btn.textContent = '⏳ 处理中...';
  resultDiv.className = 'test-result loading';
  resultDiv.textContent = '正在调用AI处理新闻，请稍候（可能需要30-60秒）...';
  
  try {
    // Reuters使用端口1125
    const response = await fetch('http://localhost:1125/api/process_test', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    const data = await response.json();
    console.log('📊 处理结果:', data);
    
    if (data.success) {
      resultDiv.className = 'test-result success';
      if (data.processed > 0) {
        resultDiv.textContent = `✅ 处理成功！已处理 ${data.processed} 条新闻，任务ID: ${data.task_id}`;
      } else {
        resultDiv.textContent = `ℹ️ ${data.message}`;
      }
      console.log('✅ 测试处理成功');
    } else {
      resultDiv.className = 'test-result error';
      resultDiv.textContent = `❌ 处理失败: ${data.message}`;
      console.error('❌ 测试处理失败:', data.message);
    }
  } catch (error) {
    console.error('❌ 请求失败:', error);
    resultDiv.className = 'test-result error';
    resultDiv.textContent = `❌ 请求失败: ${error.message}。请确保后端服务已启动（端口1125）`;
  } finally {
    // 恢复按钮状态
    btn.disabled = false;
    btn.textContent = '🚀 立即处理所有待处理新闻';
  }
  
  console.log('═══════════════════════════════════════════════');
});

// 监听storage变化，更新记录表格和状态
console.log('👂 开始监听 storage 变化...');
chrome.storage.onChanged.addListener((changes, namespace) => {
  console.log('📢 Storage 发生变化:', namespace, changes);
  
  if (namespace === 'local') {
    if (changes.taskRecords) {
      console.log('🔔 检测到新的执行记录');
      updateRecordsTable();
    }
    if (changes.capturedData || changes.schedulerEnabled || changes.lastAutoRefreshTime || 
        changes.lastTaskSuccess || changes.lastDataCount) {
      updateSchedulerStatus();
      updateHealthStatus();
    }
  }
});

// 初始化
console.log('🔄 初始化界面...');
updateSchedulerStatus();
updateRecordsTable();
updateHealthStatus();

// 启动时自动检查一次网站健康状态
setTimeout(async () => {
  console.log('🏥 启动时自动检查网站健康状态...');
  try {
    const response = await chrome.runtime.sendMessage({ type: 'CHECK_WEBSITE_HEALTH' });
    const websiteHealthText = document.getElementById('websiteHealthText');
    
    if (response.reachable) {
      websiteHealthText.textContent = '✅ 可达';
      websiteHealthText.className = 'status-value active';
    } else {
      websiteHealthText.textContent = `❌ 不可达: ${response.error || '未知错误'}`;
      websiteHealthText.className = 'status-value error';
    }
  } catch (error) {
    console.error('❌ 自动健康检查失败:', error);
  }
}, 500);

// 每5秒自动更新一次状态
setInterval(() => {
  updateSchedulerStatus();
  updateHealthStatus();
}, 5000);

console.log('✅ Popup 初始化完成');
console.log('═══════════════════════════════════════════════');
