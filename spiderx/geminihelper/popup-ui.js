// Popup UI Manager

const TASK_STATUS = {
  IDLE: '未启动',
  RUNNING: '运行中',
  STOPPED: '已停止'
};

function formatDateTime(timestamp) {
  if (!timestamp) return '--';
  
  const date = new Date(timestamp);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  
  return `${year}-${month}-${day} ${hours}:${minutes}`;
}

export function updateStatusDisplay(elements, config) {
  // 任务状态
  if (config.isRunning) {
    elements.taskStatus.textContent = TASK_STATUS.RUNNING;
    elements.taskStatus.style.color = '#28a745';
  } else if (config.executedDays > 0) {
    elements.taskStatus.textContent = TASK_STATUS.STOPPED;
    elements.taskStatus.style.color = '#dc3545';
  } else {
    elements.taskStatus.textContent = TASK_STATUS.IDLE;
    elements.taskStatus.style.color = '#6c757d';
  }
  
  // 剩余次数
  const remaining = config.totalDays - config.executedDays;
  elements.remainingCount.textContent = `${remaining}/${config.totalDays}`;
  
  // 启动时间
  elements.startTime.textContent = config.startTime ? formatDateTime(config.startTime) : '--';
  
  // 上次执行时间
  elements.lastRunTime.textContent = config.lastRunTime ? formatDateTime(config.lastRunTime) : '--';
}

export function updateButtonStates(elements, config) {
  const isRunning = config.isRunning;
  const isCompleted = config.executedDays >= config.totalDays;
  
  elements.startBtn.disabled = isRunning || isCompleted;
  elements.stopBtn.disabled = !isRunning;
  
  if (isCompleted) {
    elements.startBtn.textContent = '已完成';
  } else {
    elements.startBtn.textContent = '启动任务';
  }
}

export function updateRecordsDisplay(container, records) {
  if (records.length === 0) {
    container.innerHTML = '<div class="empty-message">暂无执行记录</div>';
    return;
  }
  
  // 构建表格（最新的在前面）
  const sortedRecords = [...records].reverse();
  
  let html = '<table class="records-table">';
  html += '<thead><tr>';
  html += '<th style="width: 15%">序号</th>';
  html += '<th style="width: 50%">执行时间</th>';
  html += '<th style="width: 35%">状态</th>';
  html += '</tr></thead>';
  html += '<tbody>';
  
  sortedRecords.forEach((record, index) => {
    const actualIndex = records.length - index;
    const statusClass = record.success ? 'status-success' : 'status-error';
    const statusText = record.success ? '成功' : '失败';
    
    html += '<tr>';
    html += `<td>#${actualIndex}</td>`;
    html += `<td>${formatDateTime(record.time)}</td>`;
    html += `<td><span class="status-badge ${statusClass}">${statusText}</span></td>`;
    html += '</tr>';
  });
  
  html += '</tbody></table>';
  container.innerHTML = html;
}

