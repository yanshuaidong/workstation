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

    <!-- 历史数据展示区块 -->
    <el-card class="data-display-card">
      <template #header>
        <div class="card-header">
          <span>历史数据展示</span>
        </div>
      </template>

      <!-- 控制面板 -->
      <div class="control-panel">
        <el-row :gutter="20">
          <!-- 合约选择 -->
          <el-col :span="6">
            <el-form-item label="选择合约">
              <el-select
                v-model="selectedContract"
                placeholder="请选择合约"
                style="width: 100%"
                @change="onContractChange"
                filterable
                clearable
              >
                <el-option
                  v-for="contract in contractsList"
                  :key="contract.symbol"
                  :label="`${contract.name} (${contract.symbol})`"
                  :value="contract.symbol"
                />
              </el-select>
            </el-form-item>
          </el-col>

          <!-- 日期范围选择 -->
          <el-col :span="8">
            <el-form-item label="查询日期范围">
              <el-date-picker
                v-model="dataDateRange"
                type="daterange"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>

          <!-- 查询按钮 -->
          <el-col :span="4">
            <el-form-item label=" ">
              <el-button
                type="primary"
                @click="queryHistoryData"
                :loading="dataLoading"
                icon="Search"
                style="width: 100%"
              >
                查询
              </el-button>
            </el-form-item>
          </el-col>

          <!-- 复制操作 -->
          <el-col :span="6">
            <el-form-item label="复制操作">
              <div class="copy-controls">
                <el-button
                  size="small"
                  @click="showColumnSelector"
                  :disabled="!historyData.length"
                >
                  选择列
                </el-button>
                <el-button
                  size="small"
                  type="success"
                  @click="copyAsJson"
                  :disabled="!historyData.length"
                >
                  复制JSON
                </el-button>
                <el-button
                  size="small"
                  type="warning"
                  @click="copyAsTable"
                  :disabled="!historyData.length"
                >
                  复制表格
                </el-button>
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- 数据表格 -->
      <div class="data-table-container">
        <!-- 表格标题 -->
        <div v-if="selectedContractName" class="table-title">
          {{ selectedContractName }}的历史数据
          <span v-if="historyData.length" class="data-count">
            （共{{ historyData.length }}条记录）
          </span>
        </div>

        <!-- 数据表格 -->
        <el-table
          :data="historyData"
          v-loading="dataLoading"
          stripe
          border
          style="width: 100%"
          max-height="600"
          empty-text="请选择合约并查询数据"
        >
          <el-table-column type="index" label="序号" width="60" :index="(index) => index + 1" />
          <el-table-column prop="raw.trade_date" label="交易日期" width="120" />
          <el-table-column prop="raw.open_price" label="开盘价" width="100" />
          <el-table-column prop="raw.high_price" label="最高价" width="100" />
          <el-table-column prop="raw.low_price" label="最低价" width="100" />
          <el-table-column prop="raw.close_price" label="收盘价" width="100" />
          <el-table-column prop="raw.volume" label="成交量" width="120" />
          <el-table-column prop="raw.open_interest" label="持仓量" width="120" />
          <el-table-column label="成交额(万)" width="120">
            <template #default="scope">
              {{ (scope.row.raw.turnover / 10000).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="raw.price_change" label="涨跌" width="80" />
          <el-table-column label="涨跌幅(%)" width="100">
            <template #default="scope">
              {{ scope.row.raw.change_pct ? scope.row.raw.change_pct.toFixed(2) : '-' }}
            </template>
          </el-table-column>
          <el-table-column prop="raw.macd_dif" label="MACD快线" width="100" />
          <el-table-column prop="raw.macd_dea" label="MACD慢线" width="100" />
          <el-table-column prop="raw.macd_histogram" label="MACD柱状图" width="110" />
          <el-table-column prop="raw.rsi_14" label="RSI(14)" width="80" />
          <el-table-column prop="raw.kdj_k" label="KDJ-K" width="80" />
          <el-table-column prop="raw.kdj_d" label="KDJ-D" width="80" />
          <el-table-column prop="raw.kdj_j" label="KDJ-J" width="80" />
          <el-table-column prop="raw.bb_upper" label="布林带上轨" width="100" />
          <el-table-column prop="raw.bb_middle" label="布林带中轨" width="100" />
          <el-table-column prop="raw.bb_lower" label="布林带下轨" width="100" />
          <el-table-column prop="raw.bb_width" label="布林带宽度" width="100" />
        </el-table>
      </div>
    </el-card>

    <!-- 列选择对话框 -->
    <el-dialog
      v-model="columnSelectorVisible"
      title="选择要复制的列"
      width="600px"
    >
      <div class="column-selector">
        <el-checkbox
          v-model="selectAllColumns"
          @change="toggleSelectAll"
          style="margin-bottom: 15px; font-weight: bold;"
        >
          全选/全不选
        </el-checkbox>
        
        <el-row :gutter="10">
          <el-col :span="8" v-for="column in columnOptions" :key="column.key">
            <el-checkbox v-model="selectedColumns[column.key]">
              {{ column.label }}
            </el-checkbox>
          </el-col>
        </el-row>
      </div>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="columnSelectorVisible = false">取消</el-button>
          <el-button type="primary" @click="columnSelectorVisible = false">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import request from '@/utils/request'
import {
  getSettingsApi,
  updateSettingsApi,
  updateContractsListApi,
  getContractsListApi,
  getListUpdateLogApi,
  updateAllHistoryApi,
  retrySingleHistoryApi,
  getHistoryLogsApi,
  getHistoryDataApi
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
      refreshTimer: null,
      
      // 历史数据展示相关
      contractsList: [], // 合约列表
      selectedContract: '', // 选中的合约
      selectedContractName: '', // 选中合约的名称
      dataDateRange: [], // 数据查询日期范围
      historyData: [], // 历史数据
      dataLoading: false, // 数据加载状态
      
      // 列选择相关
      columnSelectorVisible: false,
      selectAllColumns: true,
      selectedColumns: {},
      columnOptions: [
        { key: 'trade_date', label: '交易日期' },
        { key: 'open_price', label: '开盘价' },
        { key: 'high_price', label: '最高价' },
        { key: 'low_price', label: '最低价' },
        { key: 'close_price', label: '收盘价' },
        { key: 'volume', label: '成交量' },
        { key: 'open_interest', label: '持仓量' },
        { key: 'turnover', label: '成交额(万)' },
        { key: 'price_change', label: '涨跌' },
        { key: 'change_pct', label: '涨跌幅(%)' },
        { key: 'macd_dif', label: 'MACD快线' },
        { key: 'macd_dea', label: 'MACD慢线' },
        { key: 'macd_histogram', label: 'MACD柱状图' },
        { key: 'rsi_14', label: 'RSI(14)' },
        { key: 'kdj_k', label: 'KDJ-K' },
        { key: 'kdj_d', label: 'KDJ-D' },
        { key: 'kdj_j', label: 'KDJ-J' },
        { key: 'bb_upper', label: '布林带上轨' },
        { key: 'bb_middle', label: '布林带中轨' },
        { key: 'bb_lower', label: '布林带下轨' },
        { key: 'bb_width', label: '布林带宽度' }
      ]
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

  watch: {
    // 监听selectedColumns变化，更新selectAllColumns状态
    selectedColumns: {
      handler(newVal) {
        const allSelected = this.columnOptions.every(column => newVal[column.key])
        const noneSelected = this.columnOptions.every(column => !newVal[column.key])
        
        if (allSelected) {
          this.selectAllColumns = true
        } else if (noneSelected) {
          this.selectAllColumns = false
        } else {
          this.selectAllColumns = false // 部分选中状态
        }
      },
      deep: true
    }
  },
  
  async mounted() {
    await this.loadSettings()
    this.initDateRange()
    this.initDataDateRange()
    this.parseTimeString()
    this.initSelectedColumns()
    await this.loadContractsUpdateLog()
    await this.loadHistoryLogs()
    await this.loadContractsList()
    // 默认不启动定时器，由用户手动开启
  },
  
  beforeUnmount() {
    if (this.refreshTimer) {
      clearInterval(this.refreshTimer)
    }
  },
  
  methods: {
    // 初始化日期范围（默认近三个月）
    initDateRange() {
      const end = new Date()
      const start = new Date()
      start.setDate(start.getDate() - 90)
      
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
        const response = await request.get(getSettingsApi)
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
        const response = await request.post(updateSettingsApi, this.settings)
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
        const response = await request.get(getListUpdateLogApi)
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
        const response = await request.post(updateContractsListApi)
        
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
        const response = await request.get(getHistoryLogsApi)
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
        const response = await request.post(updateAllHistoryApi, {
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
        const response = await request.post(retrySingleHistoryApi, {
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
    },

    // 初始化数据查询日期范围（默认最近一个月）
    initDataDateRange() {
      const end = new Date()
      const start = new Date()
      start.setDate(start.getDate() - 30)
      
      this.dataDateRange = [
        start.toISOString().split('T')[0],
        end.toISOString().split('T')[0]
      ]
    },

    // 初始化选中的列（默认全选）
    initSelectedColumns() {
      this.selectedColumns = {}
      this.columnOptions.forEach(column => {
        this.selectedColumns[column.key] = true
      })
    },

    // 加载合约列表
    async loadContractsList() {
      try {
        const response = await request.get(getContractsListApi)
        if (response.code === 0) {
          this.contractsList = response.data.contracts || []
        }
      } catch (error) {
        console.error('加载合约列表失败:', error)
        this.$message.error('加载合约列表失败')
      }
    },

    // 合约变化处理
    onContractChange(symbol) {
      const contract = this.contractsList.find(c => c.symbol === symbol)
      this.selectedContractName = contract ? contract.name : ''
      // 清空之前的数据
      this.historyData = []
    },

    // 查询历史数据
    async queryHistoryData() {
      if (!this.selectedContract) {
        this.$message.warning('请先选择合约')
        return
      }

      if (!this.dataDateRange || this.dataDateRange.length !== 2) {
        this.$message.warning('请选择查询日期范围')
        return
      }

      this.dataLoading = true
      try {
        const params = new URLSearchParams({
          symbol: this.selectedContract,
          start_date: this.dataDateRange[0],
          end_date: this.dataDateRange[1]
        })

        const response = await request.get(`${getHistoryDataApi}?${params}`)
        
        if (response.code === 0) {
          this.historyData = response.data.data || []
          this.$message.success(`查询成功，获取到 ${this.historyData.length} 条数据`)
        } else {
          this.$message.error(`查询失败: ${response.message}`)
        }
      } catch (error) {
        console.error('查询历史数据失败:', error)
        this.$message.error(`查询失败: ${error.message}`)
      } finally {
        this.dataLoading = false
      }
    },

    // 显示列选择器
    showColumnSelector() {
      this.columnSelectorVisible = true
    },

    // 切换全选/全不选
    toggleSelectAll(value) {
      this.columnOptions.forEach(column => {
        this.selectedColumns[column.key] = value
      })
    },

    // 通用复制方法（兼容HTTP和HTTPS）
    async copyToClipboard(text) {
      try {
        // 优先使用现代 Clipboard API（仅在 HTTPS 或 localhost 下可用）
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(text)
          return true
        } else {
          // 降级方案：使用传统的 execCommand 方法
          return this.fallbackCopyTextToClipboard(text)
        }
      } catch (error) {
        console.error('复制失败:', error)
        // 如果现代API失败，尝试降级方案
        return this.fallbackCopyTextToClipboard(text)
      }
    },

    // 降级复制方案
    fallbackCopyTextToClipboard(text) {
      try {
        // 创建一个临时的 textarea 元素
        const textArea = document.createElement('textarea')
        textArea.value = text
        
        // 设置样式使其不可见
        textArea.style.position = 'fixed'
        textArea.style.top = '0'
        textArea.style.left = '0'
        textArea.style.width = '2em'
        textArea.style.height = '2em'
        textArea.style.padding = '0'
        textArea.style.border = 'none'
        textArea.style.outline = 'none'
        textArea.style.boxShadow = 'none'
        textArea.style.background = 'transparent'
        textArea.style.opacity = '0'
        
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()
        
        // 尝试复制
        const successful = document.execCommand('copy')
        document.body.removeChild(textArea)
        
        return successful
      } catch (error) {
        console.error('降级复制方案也失败了:', error)
        return false
      }
    },

    // 复制为JSON格式
    async copyAsJson() {
      if (!this.historyData.length) {
        this.$message.warning('没有数据可复制')
        return
      }

      try {
        const filteredData = this.historyData.map(item => {
          const result = {
            date: item.date,
            price: {},
            volume: {},
            indicators: {
              macd: {},
              kdj: {},
              bollinger: {}
            }
          }

          // 根据选中的列过滤数据
          if (this.selectedColumns.open_price) result.price.open = item.price.open
          if (this.selectedColumns.high_price) result.price.high = item.price.high
          if (this.selectedColumns.low_price) result.price.low = item.price.low
          if (this.selectedColumns.close_price) result.price.close = item.price.close
          
          if (this.selectedColumns.volume) result.volume.shares = item.volume.shares
          if (this.selectedColumns.open_interest) result.volume.open_interest = item.volume.open_interest
          if (this.selectedColumns.turnover) result.volume.turnover = item.volume.turnover

          if (this.selectedColumns.macd_dif) result.indicators.macd.dif = item.indicators.macd.dif
          if (this.selectedColumns.macd_dea) result.indicators.macd.dea = item.indicators.macd.dea
          if (this.selectedColumns.macd_histogram) result.indicators.macd.histogram = item.indicators.macd.histogram
          
          if (this.selectedColumns.rsi_14) result.indicators.rsi = item.indicators.rsi
          
          if (this.selectedColumns.kdj_k) result.indicators.kdj.k = item.indicators.kdj.k
          if (this.selectedColumns.kdj_d) result.indicators.kdj.d = item.indicators.kdj.d
          if (this.selectedColumns.kdj_j) result.indicators.kdj.j = item.indicators.kdj.j
          
          if (this.selectedColumns.bb_upper) result.indicators.bollinger.upper = item.indicators.bollinger.upper
          if (this.selectedColumns.bb_middle) result.indicators.bollinger.middle = item.indicators.bollinger.middle
          if (this.selectedColumns.bb_lower) result.indicators.bollinger.lower = item.indicators.bollinger.lower

          // 删除空的对象
          if (Object.keys(result.price).length === 0) delete result.price
          if (Object.keys(result.volume).length === 0) delete result.volume
          if (Object.keys(result.indicators.macd).length === 0) delete result.indicators.macd
          if (Object.keys(result.indicators.kdj).length === 0) delete result.indicators.kdj
          if (Object.keys(result.indicators.bollinger).length === 0) delete result.indicators.bollinger
          if (Object.keys(result.indicators).length === 0) delete result.indicators

          return result
        })

        const jsonData = JSON.stringify({ data: filteredData }, null, 2)
        const success = await this.copyToClipboard(jsonData)
        
        if (success) {
          this.$message.success('JSON数据已复制到剪贴板')
        } else {
          this.$message.error('复制失败，请手动复制数据')
          console.log('复制的JSON数据:', jsonData)
        }
      } catch (error) {
        console.error('复制失败:', error)
        this.$message.error('复制失败')
      }
    },

    // 复制为Markdown表格格式
    async copyAsTable() {
      if (!this.historyData.length) {
        this.$message.warning('没有数据可复制')
        return
      }

      try {
        // 构建表头
        const headers = []
        const headerMap = {
          trade_date: '交易日期',
          open_price: '开盘价',
          high_price: '最高价',
          low_price: '最低价',
          close_price: '收盘价',
          volume: '成交量',
          open_interest: '持仓量',
          turnover: '成交额(万)',
          price_change: '涨跌',
          change_pct: '涨跌幅(%)',
          macd_dif: 'MACD快线',
          macd_dea: 'MACD慢线',
          macd_histogram: 'MACD柱状图',
          rsi_14: 'RSI(14)',
          kdj_k: 'KDJ-K',
          kdj_d: 'KDJ-D',
          kdj_j: 'KDJ-J',
          bb_upper: '布林带上轨',
          bb_middle: '布林带中轨',
          bb_lower: '布林带下轨',
          bb_width: '布林带宽度'
        }

        Object.keys(headerMap).forEach(key => {
          if (this.selectedColumns[key]) {
            headers.push(headerMap[key])
          }
        })

        // 构建表格数据
        const rows = this.historyData.map(item => {
          const row = []
          Object.keys(headerMap).forEach(key => {
            if (this.selectedColumns[key]) {
              let value = ''
              switch (key) {
                case 'trade_date':
                  value = item.raw.trade_date
                  break
                case 'turnover':
                  value = (item.raw.turnover / 10000).toFixed(2)
                  break
                case 'change_pct':
                  value = item.raw.change_pct ? item.raw.change_pct.toFixed(2) : '-'
                  break
                default:
                  value = item.raw[key] !== null && item.raw[key] !== undefined ? item.raw[key] : '-'
              }
              row.push(value)
            }
          })
          return row
        })

        // 构建Markdown表格
        let markdown = '| ' + headers.join(' | ') + ' |\n'
        markdown += '| ' + headers.map(() => '---').join(' | ') + ' |\n'
        rows.forEach(row => {
          markdown += '| ' + row.join(' | ') + ' |\n'
        })

        const success = await this.copyToClipboard(markdown)
        
        if (success) {
          this.$message.success('Markdown表格已复制到剪贴板')
        } else {
          this.$message.error('复制失败，请手动复制数据')
          console.log('复制的Markdown表格:', markdown)
        }
      } catch (error) {
        console.error('复制失败:', error)
        this.$message.error('复制失败')
      }
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
.history-card,
.data-display-card {
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

/* 数据展示相关样式 */
.control-panel {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 6px;
}

.copy-controls {
  display: flex;
  gap: 5px;
}

.copy-controls .el-button {
  flex: 1;
  min-width: 60px;
}

.table-title {
  font-size: 16px;
  font-weight: bold;
  margin-bottom: 15px;
  color: #303133;
}

.data-count {
  font-size: 14px;
  font-weight: normal;
  color: #909399;
}

.data-table-container {
  margin-top: 15px;
}

.column-selector {
  padding: 10px 0;
}

.column-selector .el-checkbox {
  margin-bottom: 10px;
  display: block;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .control-row .el-col {
    margin-bottom: 20px;
  }
  
  .copy-controls {
    flex-direction: column;
  }
  
  .copy-controls .el-button {
    width: 100%;
    margin-bottom: 5px;
  }
}
</style>