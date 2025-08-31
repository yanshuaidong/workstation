<template>
  <div class="futures-update">
    <!-- 标题栏 -->
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span>期货数据更新系统</span>
          <el-tag :type="systemStatus.type">{{ systemStatus.text }}</el-tag>
        </div>
      </template>

      <!-- 全局控制区 -->
      <el-row :gutter="20" class="control-row">
        <!-- 自动更新设置 -->
        <el-col :span="6">
          <el-card shadow="never" class="setting-card">
            <template #header>自动更新设置</template>
            <el-switch
              v-model="settings.auto_update_enabled"
              @change="updateSettings"
              active-text="启用自动更新"
              inactive-text="手动更新"
            />
            <br><br>
            <el-time-picker
              v-model="dailyUpdateTime"
              @change="onTimeChange"
              format="HH:mm"
              placeholder="选择更新时间"
              :disabled="!settings.auto_update_enabled"
              style="width: 100%"
            />
          </el-card>
        </el-col>

        <!-- 并发控制 -->
        <el-col :span="6">
          <el-card shadow="never" class="setting-card">
            <template #header>并发设置</template>
            <el-switch
              v-model="settings.multithread_enabled"
              @change="updateSettings"
              active-text="多线程"
              inactive-text="单线程"
            />
            <br><br>
            <el-select
              v-model="settings.concurrency"
              @change="updateSettings"
              placeholder="并发数"
              :disabled="!settings.multithread_enabled"
              style="width: 100%"
            >
              <el-option label="5" :value="5" />
              <el-option label="10" :value="10" />
              <el-option label="15" :value="15" />
              <el-option label="20" :value="20" />
            </el-select>
          </el-card>
        </el-col>

        <!-- 超时设置 -->
        <el-col :span="6">
          <el-card shadow="never" class="setting-card">
            <template #header>超时设置</template>
            <el-select
              v-model="settings.timeout_seconds"
              @change="updateSettings"
              placeholder="超时时间"
              style="width: 100%"
            >
              <el-option label="30秒" :value="30" />
              <el-option label="60秒" :value="60" />
              <el-option label="90秒" :value="90" />
              <el-option label="120秒" :value="120" />
            </el-select>
          </el-card>
        </el-col>

        <!-- 日期范围 -->
        <el-col :span="6">
          <el-card shadow="never" class="setting-card">
            <template #header>数据日期范围</template>
            <el-date-picker
              v-model="dateRange"
              type="daterange"
              range-separator="至"
              start-placeholder="开始日期"
              end-placeholder="结束日期"
              format="YYYY-MM-DD"
              value-format="YYYY-MM-DD"
              style="width: 100%"
            />
          </el-card>
        </el-col>
      </el-row>

      <!-- 第二行：日志刷新控制 -->
      <el-row :gutter="20" class="control-row" style="margin-top: 20px;">
        <!-- 日志自动刷新设置 -->
        <el-col :span="6">
          <el-card shadow="never" class="setting-card">
            <template #header>日志自动刷新</template>
            <el-switch
              v-model="autoRefreshEnabled"
              @change="toggleAutoRefresh"
              active-text="启用自动刷新"
              inactive-text="手动刷新"
            />
            <br><br>
            <el-select
              v-model="refreshInterval"
              @change="updateRefreshInterval"
              placeholder="刷新间隔"
              :disabled="!autoRefreshEnabled"
              style="width: 100%"
            >
              <el-option label="5秒" :value="5000" />
              <el-option label="10秒" :value="10000" />
              <el-option label="30秒" :value="30000" />
              <el-option label="60秒" :value="60000" />
            </el-select>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 合约列表维护区块 -->
    <el-card class="contracts-card">
      <template #header>
        <div class="card-header">
          <span>合约列表维护</span>
          <div>
            <el-button
              type="primary"
              @click="updateContractsList"
              :loading="contractsLoading"
              icon="Refresh"
            >
              更新合约列表
            </el-button>
          </div>
        </div>
      </template>

      <div class="contracts-status">
        <el-descriptions :column="4" border>
          <el-descriptions-item label="上次更新时间">
            {{ formatTime(contractsUpdateLog.last_update_time) || '未更新' }}
          </el-descriptions-item>
          <el-descriptions-item label="更新方式">
            <el-tag :type="contractsUpdateLog.update_method === 'auto' ? 'success' : 'primary'">
              {{ contractsUpdateLog.update_method === 'auto' ? '自动更新' : '手动更新' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="更新结果">
            <el-tag :type="contractsUpdateLog.status === 'success' ? 'success' : 'danger'">
              {{ contractsUpdateLog.status === 'success' ? '成功' : '失败' }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="耗时">
            {{ formatDuration(contractsUpdateLog.duration_ms) || '-' }}
          </el-descriptions-item>
        </el-descriptions>
        
        <!-- 显示错误信息（如果有） -->
        <div v-if="contractsUpdateLog.error_message" class="error-message">
          <el-alert
            :title="contractsUpdateLog.error_message"
            type="error"
            show-icon
            :closable="false"
            style="margin-top: 15px;"
          />
        </div>
      </div>
    </el-card>

    <!-- 主连历史数据更新区块 -->
    <el-card class="history-card">
      <template #header>
        <div class="card-header">
          <span>主连历史数据更新</span>
          <div>
            <el-button
              type="success"
              @click="updateAllHistory"
              :loading="historyLoading"
              icon="Download"
            >
              更新全部历史数据
            </el-button>
          </div>
        </div>
      </template>

      <!-- 历史数据表格 -->
      <el-table
        :data="historyLogs"
        v-loading="historyLogsLoading"
        stripe
        style="width: 100%"
        max-height="600"
      >
        <el-table-column type="index" label="序号" width="60" :index="indexMethod" />
        <el-table-column prop="name" label="合约名称" width="150" />
        <el-table-column prop="contract_symbol" label="合约代码" width="120" />
        <el-table-column prop="target_table" label="目标表名" width="150" />
        <el-table-column label="开始时间" width="180">
          <template #default="scope">
            {{ formatTime(scope.row.start_time) }}
          </template>
        </el-table-column>
        <el-table-column label="结束时间" width="180">
          <template #default="scope">
            {{ formatTime(scope.row.end_time) }}
          </template>
        </el-table-column>
        <el-table-column label="更新区间" width="200">
          <template #default="scope">
            <span v-if="scope.row.data_start_date && scope.row.data_end_date">
              {{ scope.row.data_start_date }} 至 {{ scope.row.data_end_date }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="scope">
            <el-tag :type="getStatusType(scope.row.status)">
              {{ getStatusText(scope.row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="重试次数" width="100">
          <template #default="scope">
            {{ scope.row.retry_count || 0 }}
          </template>
        </el-table-column>
        <el-table-column label="失败原因" min-width="200">
          <template #default="scope">
            <span v-if="scope.row.status === 'failure' && scope.row.error_message" class="error-text">
              {{ scope.row.error_message }}
            </span>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="scope">
            <el-button
              v-if="scope.row.status === 'failure'"
              type="warning"
              size="small"
              @click="retrySingle(scope.row)"
              :loading="scope.row.retrying"
            >
              重试
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 统计信息 -->
      <div class="history-summary" style="margin-top: 20px;">
        <el-row :gutter="20">
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">总合约数</div>
              <div class="summary-value">{{ historyLogs.length }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">成功数量</div>
              <div class="summary-value success">{{ successCount }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">失败数量</div>
              <div class="summary-value danger">{{ failureCount }}</div>
            </div>
          </el-col>
          <el-col :span="6">
            <div class="summary-item">
              <div class="summary-label">成功率</div>
              <div class="summary-value">{{ successRate }}%</div>
            </div>
          </el-col>
        </el-row>
      </div>
    </el-card>
  </div>
</template>

<script>
import { request7002 } from '@/utils/request'
import {
  getSettingsApi,
  updateSettingsApi,
  updateContractsListApi,
  getListUpdateLogApi,
  updateAllHistoryApi,
  retrySingleHistoryApi,
  getHistoryLogsApi
} from '@/api'

export default {
  name: 'FuturesUpdate',
  data() {
    return {
      // 系统状态
      systemStatus: {
        type: 'success',
        text: '系统正常'
      },
      
      // 设置
      settings: {
        auto_update_enabled: false,
        daily_update_time: '17:00',
        multithread_enabled: true,
        concurrency: 5,
        timeout_seconds: 60
      },
      
      // 时间选择器的值
      dailyUpdateTime: null,
      
      // 日期范围（默认近一个月）
      dateRange: [],
      
      // 合约列表相关
      contractsLoading: false,
      contractsUpdateLog: {},
      
      // 历史数据相关
      historyLoading: false,
      historyLogsLoading: false,
      historyLogs: [],
      
      // 自动刷新控制
      autoRefreshEnabled: false, // 默认关闭自动刷新
      refreshInterval: 10000, // 默认10秒
      
      // 定时器
      refreshTimer: null
    }
  },
  
  computed: {
    // 成功数量
    successCount() {
      return this.historyLogs.filter(log => log.status === 'success').length
    },
    
    // 失败数量
    failureCount() {
      return this.historyLogs.filter(log => log.status === 'failure').length
    },
    
    // 成功率
    successRate() {
      if (this.historyLogs.length === 0) return 0
      return Math.round((this.successCount / this.historyLogs.length) * 100)
    }
  },
  
  async mounted() {
    await this.loadSettings()
    this.initDateRange()
    this.parseTimeString()
    await this.loadContractsUpdateLog()
    await this.loadHistoryLogs()
    // 默认不启动定时器，由用户手动开启
  },
  
  beforeUnmount() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer)
    }
  },
  
  methods: {
    // 初始化日期范围（默认近一个月）
    initDateRange() {
      const end = new Date()
      const start = new Date()
      start.setDate(start.getDate() - 30)
      
      this.dateRange = [
        start.toISOString().split('T')[0],
        end.toISOString().split('T')[0]
      ]
    },
    
    // 解析时间字符串为Date对象
    parseTimeString() {
      if (this.settings.daily_update_time) {
        const [hours, minutes] = this.settings.daily_update_time.split(':')
        const today = new Date()
        today.setHours(parseInt(hours), parseInt(minutes), 0, 0)
        this.dailyUpdateTime = today
      }
    },
    
    // 时间变化处理
    onTimeChange(value) {
      if (value) {
        const hours = value.getHours().toString().padStart(2, '0')
        const minutes = value.getMinutes().toString().padStart(2, '0')
        this.settings.daily_update_time = `${hours}:${minutes}`
        this.updateSettings()
      }
    },
    
    // 加载系统设置
    async loadSettings() {
      try {
        const response = await request7002.get(getSettingsApi.replace('http://localhost:7002', ''))
        if (response.code === 0) {
          this.settings = { ...this.settings, ...response.data }
          this.parseTimeString()
        }
      } catch (error) {
        console.error('加载设置失败:', error)
        this.$message.error('加载设置失败')
      }
    },
    
    // 更新设置
    async updateSettings() {
      try {
        const response = await request7002.post(updateSettingsApi.replace('http://localhost:7002', ''), this.settings)
        if (response.code === 0) {
          this.$message.success('设置已更新')
        }
      } catch (error) {
        console.error('更新设置失败:', error)
        this.$message.error('更新设置失败')
      }
    },
    
    // 加载合约列表更新记录
    async loadContractsUpdateLog() {
      try {
        const response = await request7002.get(getListUpdateLogApi.replace('http://localhost:7002', ''))
        if (response.code === 0) {
          this.contractsUpdateLog = response.data || {}
        }
      } catch (error) {
        console.error('加载合约更新记录失败:', error)
      }
    },
    
    // 更新合约列表
    async updateContractsList() {
      this.contractsLoading = true
      try {
        const response = await request7002.post(updateContractsListApi.replace('http://localhost:7002', ''))
        
        if (response.code === 0) {
          this.$message.success(`合约列表更新成功！新增: ${response.data.new_count}`)
          await this.loadContractsUpdateLog()
          await this.loadHistoryLogs() // 重新加载历史日志
        } else {
          this.$message.error(`更新失败: ${response.message}`)
        }
      } catch (error) {
        console.error('更新合约列表失败:', error)
        this.$message.error(`更新合约列表失败: ${error.message}`)
      } finally {
        this.contractsLoading = false
        // 无论成功失败都重新加载记录
        await this.loadContractsUpdateLog()
      }
    },
    
    // 加载历史数据日志
    async loadHistoryLogs() {
      this.historyLogsLoading = true
      try {
        const response = await request7002.get(getHistoryLogsApi.replace('http://localhost:7002', ''))
        if (response.code === 0) {
          this.historyLogs = response.data || []
        }
      } catch (error) {
        console.error('加载历史日志失败:', error)
      } finally {
        this.historyLogsLoading = false
      }
    },
    
    // 更新全部历史数据
    async updateAllHistory() {
      if (!this.dateRange || this.dateRange.length !== 2) {
        this.$message.warning('请先选择日期范围')
        return
      }
      
      this.historyLoading = true
      try {
        const response = await request7002.post(updateAllHistoryApi.replace('http://localhost:7002', ''), {
          date_start: this.dateRange[0],
          date_end: this.dateRange[1]
        })
        
        if (response.code === 0) {
          this.$message.success('历史数据更新已启动，请稍后刷新查看结果')
          // 等待一段时间后自动刷新日志
          setTimeout(() => {
            this.loadHistoryLogs()
          }, 3000)
        } else {
          this.$message.error(`启动失败: ${response.message}`)
        }
      } catch (error) {
        console.error('启动历史数据更新失败:', error)
        this.$message.error(`启动失败: ${error.message}`)
      } finally {
        this.historyLoading = false
      }
    },
    
    // 重试单个合约
    async retrySingle(log) {
      if (!this.dateRange || this.dateRange.length !== 2) {
        this.$message.warning('请先选择日期范围')
        return
      }
      
      log.retrying = true
      try {
        const response = await request7002.post(retrySingleHistoryApi.replace('http://localhost:7002', ''), {
          symbol: log.contract_symbol,
          date_start: this.dateRange[0],
          date_end: this.dateRange[1]
        })
        
        if (response.code === 0) {
          this.$message.success(`${log.contract_symbol} 重试已启动`)
          // 等待一段时间后自动刷新日志
          setTimeout(() => {
            this.loadHistoryLogs()
          }, 2000)
        } else {
          this.$message.error(`重试失败: ${response.message}`)
        }
      } catch (error) {
        console.error('重试失败:', error)
        this.$message.error(`重试失败: ${error.message}`)
      } finally {
        log.retrying = false
      }
    },
    
    // 启动刷新定时器
    startRefreshTimer() {
      if (this.refreshTimer) {
        clearInterval(this.refreshTimer)
      }
      this.refreshTimer = setInterval(() => {
        // 定期刷新历史日志
        this.loadHistoryLogs()
      }, this.refreshInterval)
    },
    
    // 停止刷新定时器
    stopRefreshTimer() {
      if (this.refreshTimer) {
        clearInterval(this.refreshTimer)
        this.refreshTimer = null
      }
    },
    
    // 切换自动刷新
    toggleAutoRefresh(enabled) {
      if (enabled) {
        this.startRefreshTimer()
        this.$message.success('已启用日志自动刷新')
      } else {
        this.stopRefreshTimer()
        this.$message.info('已关闭日志自动刷新')
      }
    },
    
    // 更新刷新间隔
    updateRefreshInterval() {
      if (this.autoRefreshEnabled) {
        this.startRefreshTimer() // 重新启动定时器以应用新的间隔
        this.$message.success(`刷新间隔已更新为 ${this.refreshInterval / 1000} 秒`)
      }
    },
    
    // 格式化时间
    formatTime(timeStr) {
      if (!timeStr) return '-'
      return new Date(timeStr).toLocaleString()
    },
    
    // 格式化持续时间
    formatDuration(ms) {
      if (!ms) return '-'
      if (ms < 1000) return `${ms}ms`
      return `${(ms / 1000).toFixed(1)}s`
    },
    
    // 获取状态类型
    getStatusType(status) {
      const typeMap = {
        success: 'success',
        failure: 'danger'
      }
      return typeMap[status] || 'info'
    },
    
    // 获取状态文本
    getStatusText(status) {
      const textMap = {
        success: '成功',
        failure: '失败'
      }
      return textMap[status] || '未知'
    },

    // 序号方法
    indexMethod(index) {
      return index + 1
    }
  }
}
</script>

<style scoped>
.futures-update {
  padding: 20px;
}

.header-card,
.contracts-card,
.history-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.control-row {
  margin-bottom: 0;
}

.setting-card {
  height: 180px;
}

.setting-card .el-card__body {
  padding: 15px;
}

.contracts-status {
  margin-top: 15px;
}

.error-message {
  margin-top: 15px;
}

.summary-item {
  text-align: center;
  padding: 10px;
}

.summary-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 5px;
}

.summary-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.summary-value.success {
  color: #67c23a;
}

.summary-value.danger {
  color: #f56c6c;
}

.error-text {
  color: #f56c6c;
  font-size: 12px;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .control-row .el-col {
    margin-bottom: 20px;
  }
}
</style>