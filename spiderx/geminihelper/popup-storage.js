// Popup Storage Manager

const STORAGE_KEYS = {
  TASK_CONFIG: 'taskConfig',
  EXECUTION_RECORDS: 'executionRecords'
};

const TOTAL_DAYS = 30;

export async function getTaskConfig() {
  return new Promise((resolve) => {
    chrome.storage.local.get([STORAGE_KEYS.TASK_CONFIG], (result) => {
      const config = result[STORAGE_KEYS.TASK_CONFIG] || {
        isRunning: false,
        startTime: null,
        lastRunTime: null,
        executedDays: 0,
        totalDays: TOTAL_DAYS
      };
      resolve(config);
    });
  });
}

export async function saveTaskConfig(config) {
  return new Promise((resolve) => {
    chrome.storage.local.set({ [STORAGE_KEYS.TASK_CONFIG]: config }, () => {
      console.log("[Popup] 配置已保存:", config);
      resolve();
    });
  });
}

export async function getExecutionRecords() {
  return new Promise((resolve) => {
    chrome.storage.local.get([STORAGE_KEYS.EXECUTION_RECORDS], (result) => {
      const records = result[STORAGE_KEYS.EXECUTION_RECORDS] || [];
      resolve(records);
    });
  });
}

export async function saveExecutionRecords(records) {
  return new Promise((resolve) => {
    chrome.storage.local.set({ [STORAGE_KEYS.EXECUTION_RECORDS]: records }, () => {
      console.log("[Popup] 记录已保存，共", records.length, "条");
      resolve();
    });
  });
}

