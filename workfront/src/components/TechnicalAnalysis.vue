<template>
  <div class="technical-analysis">
    <!-- 页面标题 -->
    <el-card class="header-card" shadow="never">
      <template #header>
        <div class="card-header">
          <span class="title">期货技术分析</span>
          <el-tag type="info" size="large">实时数据分析</el-tag>
        </div>
      </template>
    </el-card>
    
    <!-- 列显示控制 -->
    <el-card class="column-controls-card" shadow="hover">
      <template #header>
        <div class="controls-header">
          <span>列显示设置</span>
          <div class="control-buttons">
            <el-button @click="showAllColumns" size="small" type="primary" plain>
              <el-icon><Select /></el-icon>
              全选
            </el-button>
            <el-button @click="hideAllColumns" size="small" type="warning" plain>
              <el-icon><Remove /></el-icon>
              全不选
            </el-button>
            <el-button @click="resetToDefault" size="small" type="info" plain>
              <el-icon><Refresh /></el-icon>
              恢复默认
            </el-button>
          </div>
        </div>
      </template>
      
      <div class="column-checkboxes">
        <el-checkbox-group v-model="selectedColumns">
          <el-checkbox 
            v-for="column in availableColumns" 
            :key="column.key"
            :label="column.key"
            :value="column.key"
          >
            {{ column.label }}
          </el-checkbox>
        </el-checkbox-group>
      </div>
    </el-card>
    
    <!-- 查询表单 -->
    <el-card class="query-form-card" shadow="hover">
      <template #header>
        <span>查询条件</span>
      </template>
      
      <el-form :model="queryParams" label-width="80px" :inline="true">
        <el-row :gutter="20">
          <el-col :xs="24" :sm="12" :md="8" :lg="6">
            <el-form-item label="选择合约">
              <div class="contract-selector">
                <el-input 
                  v-model="contractSearch" 
                  placeholder="搜索合约名称、代码或交易所..."
                  clearable
                  @input="filterContracts"
                  class="contract-search"
                >
                  <template #prefix>
                    <el-icon><Search /></el-icon>
                  </template>
                </el-input>
                <el-select 
                  v-model="queryParams.symbol" 
                  placeholder="请选择合约"
                  filterable
                  clearable
                  style="width: 100%; margin-top: 8px;"
                >
                  <el-option 
                    v-for="contract in filteredContracts" 
                    :key="contract.symbol" 
                    :label="`${contract.exchange} - ${contract.name} (${contract.symbol})`"
                    :value="contract.name"
                  />
                </el-select>
              </div>
            </el-form-item>
          </el-col>
          
          <el-col :xs="12" :sm="12" :md="2" :lg="6">
            <el-form-item label="周期">
              <el-select v-model="queryParams.period" placeholder="选择周期" style="width: 100%; min-width: 120px;">
                <el-option 
                  v-for="period in periods"
                  :key="period.value" 
                  :label="period.label"
                  :value="period.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="8" :lg="6">
            <el-form-item label="开始日期">
              <el-date-picker
                v-model="queryParams.startDate"
                type="date"
                placeholder="选择日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
          
          <el-col :xs="24" :sm="12" :md="8" :lg="6">
            <el-form-item label="结束日期">
              <el-date-picker
                v-model="queryParams.endDate"
                type="date"
                placeholder="选择日期"
                format="YYYY-MM-DD"
                value-format="YYYY-MM-DD"
                style="width: 100%;"
              />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row>
          <el-col :span="24">
            <el-form-item>
              <el-button 
                @click="queryData" 
                :loading="loading"
                :disabled="!queryParams.symbol"
                type="primary"
                size="default"
              >
                <el-icon v-if="!loading"><Search /></el-icon>
                {{ loading ? '查询中...' : '查询数据' }}
              </el-button>
              
              <el-button 
                @click="refreshContracts" 
                :loading="contractsLoading"
                type="success"
                size="default"
              >
                <el-icon v-if="!contractsLoading"><Refresh /></el-icon>
                {{ contractsLoading ? '刷新中...' : '刷新合约' }}
              </el-button>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>
    
    <!-- 数据表格 -->
    <el-card v-if="tableData.length > 0" class="data-table-card" shadow="hover">
      <template #header>
        <div class="table-header">
          <span class="table-title">{{ currentSymbol }} - {{ getCurrentPeriodLabel() }} 数据</span>
          <el-tag type="success" size="large">{{ tableData.length }}条记录</el-tag>
        </div>
      </template>
      
      <el-table 
        :data="tableData" 
        stripe 
        border
        height="600"
        style="width: 100%"
        :header-cell-style="{ background: '#f5f7fa', color: '#606266' }"
      >
        <el-table-column 
          v-if="isColumnVisible('time')"
          prop="时间" 
          label="时间" 
          width="120"
          align="center"
          fixed="left"
        />
        
        <el-table-column 
          v-if="isColumnVisible('close')"
          prop="收盘" 
          label="收盘价" 
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <span :class="getPriceClass(row.涨跌)">{{ row.收盘 }}</span>
          </template>
        </el-table-column>
        
        <el-table-column 
          v-if="isColumnVisible('changePercent')"
          prop="涨跌幅" 
          label="涨跌幅(%)" 
          width="120"
          align="center"
        >
          <template #default="{ row }">
            <el-tag 
              :type="getChangeTagType(row.涨跌)" 
              size="small"
              effect="dark"
            >
              {{ row.涨跌幅 }}%
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column 
          v-if="isColumnVisible('volume')"
          prop="成交量" 
          label="成交量" 
          width="120"
          align="center"
        />
        
        <el-table-column 
          v-if="isColumnVisible('openInterest')"
          prop="持仓量" 
          label="持仓量" 
          width="120"
          align="center"
        />
        
        <el-table-column 
          v-if="isColumnVisible('dailyChange')"
          prop="日增仓" 
          label="日增仓" 
          width="120"
          align="center"
        >
          <template #default="{ row }">
            <el-tag 
              :type="getPositionChangeTagType(row.日增仓)" 
              size="small"
              effect="plain"
            >
              {{ row.日增仓 }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column 
          v-if="isColumnVisible('open')"
          prop="开盘" 
          label="开盘" 
          width="100"
          align="center"
        />
        
        <el-table-column 
          v-if="isColumnVisible('high')"
          prop="最高" 
          label="最高" 
          width="100"
          align="center"
        />
        
        <el-table-column 
          v-if="isColumnVisible('low')"
          prop="最低" 
          label="最低" 
          width="100"
          align="center"
        />
        
        <el-table-column 
          v-if="isColumnVisible('change')"
          prop="涨跌" 
          label="涨跌" 
          width="100"
          align="center"
        >
          <template #default="{ row }">
            <span :class="getPriceClass(row.涨跌)">{{ row.涨跌 }}</span>
          </template>
        </el-table-column>
        
        <el-table-column 
          v-if="isColumnVisible('turnover')"
          prop="成交额" 
          label="成交额" 
          width="120"
          align="center"
        />
      </el-table>
    </el-card>
    
    <!-- 空数据提示 -->
    <el-card v-else-if="!loading && hasQueried" class="no-data-card" shadow="hover">
      <el-empty description="暂无数据">
        <el-button type="primary" @click="queryData">重新查询</el-button>
      </el-empty>
    </el-card>
    
    <!-- 错误信息 -->
    <el-alert
      v-if="error"
      :title="error"
      type="error"
      show-icon
      :closable="true"
      @close="error = ''"
      style="margin-top: 20px;"
    />
  </div>
</template>

<script>
import { request7001 } from '../utils/request'
import { 
  Search, 
  Refresh, 
  Select, 
  Remove 
} from '@element-plus/icons-vue'

export default {
  name: 'TechnicalAnalysis',
  components: {
    Search,
    Refresh,
    Select,
    Remove
  },
  data() {
    const today = new Date()
    const oneMonthAgo = new Date(today.getTime() - 30 * 24 * 60 * 60 * 1000)
    
    return {
      // 查询参数
      queryParams: {
        symbol: '',
        period: 'daily',
        startDate: this.formatDate(oneMonthAgo),
        endDate: this.formatDate(today)
      },
      // 可用列配置
      availableColumns: [
        { key: 'time', label: '时间' },
        { key: 'close', label: '收盘价' },
        { key: 'changePercent', label: '涨跌幅(%)' },
        { key: 'volume', label: '成交量' },
        { key: 'openInterest', label: '持仓量' },
        { key: 'dailyChange', label: '日增仓' },
        { key: 'open', label: '开盘' },
        { key: 'high', label: '最高' },
        { key: 'low', label: '最低' },
        { key: 'change', label: '涨跌' },
        { key: 'turnover', label: '成交额' }
      ],
      // 选中的列
      selectedColumns: ['time', 'close', 'changePercent', 'volume', 'openInterest', 'dailyChange', 'high', 'low'],
      // 数据
      contracts: [],
      filteredContracts: [],
      contractSearch: '',
      periods: [],
      tableData: [],
      currentSymbol: '',
      // 状态
      loading: false,
      contractsLoading: false,
      hasQueried: false,
      error: ''
    }
  },
  
  mounted() {
    this.loadInitialData()
    this.loadColumnSettings()
  },
  
  watch: {
    selectedColumns: {
      handler() {
        this.saveColumnSettings()
      },
      deep: true
    }
  },
  
  methods: {
    // 加载初始数据
    async loadInitialData() {
      await Promise.all([
        this.loadContracts(),
        this.loadPeriods()
      ])
    },
    
    // 加载合约列表
    async loadContracts() {
      try {
        this.contractsLoading = true
        this.error = ''
        const response = await request7001.get('/api/futures/contracts')
        this.contracts = response || []
        this.filteredContracts = this.contracts
      } catch (error) {
        this.error = `加载合约列表失败: ${error.message}`
        console.error('加载合约列表失败:', error)
      } finally {
        this.contractsLoading = false
      }
    },
    
    // 加载周期选项
    async loadPeriods() {
      try {
        const response = await request7001.get('/api/futures/periods')
        this.periods = response || []
      } catch (error) {
        console.error('加载周期选项失败:', error)
        // 使用默认周期选项
        this.periods = [
          { value: 'daily', label: '日线' },
          { value: 'weekly', label: '周线' },
          { value: 'monthly', label: '月线' }
        ]
      }
    },
    
    // 刷新合约数据
    async refreshContracts() {
      try {
        this.contractsLoading = true
        this.error = ''
        await request7001.post('/api/futures/refresh-contracts')
        await this.loadContracts()
        this.$message.success('合约数据刷新成功')
      } catch (error) {
        this.error = `刷新合约数据失败: ${error.message}`
        console.error('刷新合约数据失败:', error)
      }
    },

    // 筛选合约
    filterContracts() {
      const searchTerm = this.contractSearch.toLowerCase().trim()
      
      if (!searchTerm) {
        this.filteredContracts = this.contracts
        return
      }
      
      this.filteredContracts = this.contracts.filter(contract => {
        const exchangeMatch = contract.exchange && contract.exchange.toLowerCase().includes(searchTerm)
        const nameMatch = contract.name && contract.name.toLowerCase().includes(searchTerm)
        const symbolMatch = contract.symbol && contract.symbol.toLowerCase().includes(searchTerm)
        
        return exchangeMatch || nameMatch || symbolMatch
      })
    },
    
    // 查询数据
    async queryData() {
      if (!this.queryParams.symbol) {
        this.$message.warning('请选择合约')
        return
      }
      
      try {
        this.loading = true
        this.error = ''
        this.hasQueried = false
        
        const params = {
          symbol: this.queryParams.symbol,
          period: this.queryParams.period,
          start_date: this.queryParams.startDate.replace(/-/g, ''),
          end_date: this.queryParams.endDate.replace(/-/g, '')
        }
        
        const response = await request7001.get('/api/futures/history', { params })
        
        // 对数据进行排序，最新的数据在前面
        const sortedData = (response.data || []).sort((a, b) => {
          // 将时间字符串转换为日期对象进行比较
          const dateA = new Date(a.时间.replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3'))
          const dateB = new Date(b.时间.replace(/(\d{4})(\d{2})(\d{2})/, '$1-$2-$3'))
          // 降序排列，最新的日期在前面
          return dateB - dateA
        })
        
        this.tableData = sortedData
        this.currentSymbol = response.symbol || this.queryParams.symbol
        this.hasQueried = true
        
        if (sortedData.length > 0) {
          this.$message.success(`查询成功，共获取 ${sortedData.length} 条数据`)
        }
        
      } catch (error) {
        this.error = `查询数据失败: ${error.message}`
        console.error('查询数据失败:', error)
        this.tableData = []
        this.$message.error('查询数据失败')
      } finally {
        this.loading = false
      }
    },
    
    // 列显示控制方法
    showAllColumns() {
      this.selectedColumns = this.availableColumns.map(col => col.key)
    },
    
    hideAllColumns() {
      this.selectedColumns = []
    },
    
    resetToDefault() {
      this.selectedColumns = ['time', 'close', 'changePercent', 'volume', 'openInterest', 'dailyChange', 'high', 'low']
    },
    
    // 检查列是否可见
    isColumnVisible(columnKey) {
      return this.selectedColumns.includes(columnKey)
    },
    
    // 保存列设置到本地存储
    saveColumnSettings() {
      try {
        localStorage.setItem('futuresTableColumnSettings', JSON.stringify(this.selectedColumns))
      } catch (error) {
        console.warn('保存列设置失败:', error)
      }
    },
    
    // 从本地存储加载列设置
    loadColumnSettings() {
      try {
        const saved = localStorage.getItem('futuresTableColumnSettings')
        if (saved) {
          this.selectedColumns = JSON.parse(saved)
        }
      } catch (error) {
        console.warn('加载列设置失败:', error)
      }
    },
    
    // 格式化日期
    formatDate(date) {
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}-${month}-${day}`
    },
    
    // 获取当前周期标签
    getCurrentPeriodLabel() {
      const period = this.periods.find(p => p.value === this.queryParams.period)
      return period ? period.label : '日线'
    },
    
    // 获取价格变化样式类
    getPriceClass(change) {
      if (change > 0) return 'price-up'
      if (change < 0) return 'price-down'
      return 'price-neutral'
    },
    
    // 获取涨跌标签类型
    getChangeTagType(change) {
      if (change > 0) return 'danger'
      if (change < 0) return 'success'
      return 'info'
    },
    
    // 获取持仓变化标签类型
    getPositionChangeTagType(change) {
      if (change.includes('增仓')) return 'danger'
      if (change.includes('减仓')) return 'success'
      return 'info'
    }
  }
}
</script>

<style scoped>
.technical-analysis {
  padding: 20px;
  background: #f0f2f5;
  min-height: 100vh;
}

.header-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
}

.column-controls-card,
.query-form-card,
.data-table-card,
.no-data-card {
  margin-bottom: 20px;
}

.controls-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.control-buttons {
  display: flex;
  gap: 8px;
}

.column-checkboxes {
  margin-top: 15px;
}

.column-checkboxes :deep(.el-checkbox-group) {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
}

.contract-selector {
  width: 100%;
}

.contract-search {
  margin-bottom: 8px;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.table-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.price-up {
  color: #f56c6c;
  font-weight: bold;
}

.price-down {
  color: #67c23a;
  font-weight: bold;
}

.price-neutral {
  color: #909399;
  font-weight: bold;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .technical-analysis {
    padding: 10px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }
  
  .controls-header {
    flex-direction: column;
    gap: 10px;
  }
  
  .table-header {
    flex-direction: column;
    gap: 10px;
    text-align: center;
  }
  
  .column-checkboxes :deep(.el-checkbox-group) {
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  }
}

/* Element Plus 样式覆盖 */
:deep(.el-card__header) {
  background: #f7f8fa;
  color: #333;
  border-radius: 8px 8px 0 0;
  box-shadow: none;
  border-bottom: 1px solid #ebeef5;
}

:deep(.el-card__header .card-header span) {
  color: #333;
  text-shadow: none;
}

:deep(.el-table .cell) {
  font-size: 13px;
}

:deep(.el-table th.el-table__cell) {
  background: #fafafa !important;
  font-weight: 600;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td.el-table__cell) {
  background: #fafafa;
}

:deep(.el-table__body tr:hover > td.el-table__cell) {
  background-color: #e6f7ff !important;
}
</style>
