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

// 更新执行记录表格
async function updateRecordsTable() {
  const result = await chrome.storage.local.get(['taskRecords']);
  const records = result.taskRecords || [];
  
  const tbody = document.getElementById('recordsTableBody');
  
  if (records.length === 0) {
    tbody.innerHTML = '<tr><td colspan="3" class="empty-records">暂无执行记录</td></tr>';
    return;
  }
  
  // 最新的记录在上面
  tbody.innerHTML = records.map((record, index) => `
    <tr>
      <td>#${records.length - index}</td>
      <td>${formatTime(record.time)}</td>
      <td><span class="badge-${record.success ? 'success' : 'fail'}">${record.success ? '✓ 成功' : '✗ 失败'}</span></td>
    </tr>
  `).join('');
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
  await updateRecordsTable();
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
      
      console.log('✅ 状态显示已更新');
    }
  } catch (error) {
    console.error('❌ 更新状态失败:', error);
  }
}

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
    const response = await fetch('http://localhost:1123/api/process_test', {
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
    resultDiv.textContent = `❌ 请求失败: ${error.message}。请确保后端服务已启动（端口1123）`;
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
    if (changes.capturedData || changes.schedulerEnabled || changes.lastAutoRefreshTime) {
      updateSchedulerStatus();
    }
  }
});

// 初始化
console.log('🔄 初始化界面...');
updateSchedulerStatus();
updateRecordsTable();

// 每5秒自动更新一次状态
setInterval(updateSchedulerStatus, 5000);

console.log('✅ Popup 初始化完成');
console.log('═══════════════════════════════════════════════');

