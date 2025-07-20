<template>
  <div class="technical-analysis">
    <div class="header">
      <h2>期货技术分析</h2>
    </div>
    
    <!-- 列显示控制 -->
    <div class="column-controls">
      <div class="controls-header">
        <h4>列显示设置</h4>
        <div class="control-buttons">
          <button @click="showAllColumns" class="btn btn-sm btn-outline">全选</button>
          <button @click="hideAllColumns" class="btn btn-sm btn-outline">全不选</button>
          <button @click="resetToDefault" class="btn btn-sm btn-outline">恢复默认</button>
        </div>
      </div>
      <div class="column-checkboxes">
        <label 
          v-for="column in availableColumns" 
          :key="column.key"
          class="checkbox-label"
        >
          <input 
            type="checkbox" 
            v-model="visibleColumns[column.key]"
            class="checkbox-input"
          >
          <span class="checkbox-text">{{ column.label }}</span>
        </label>
      </div>
    </div>
    
    <!-- 查询表单 -->
    <div class="query-form">
      <div class="form-row">
        <div class="form-group">
          <label>选择合约:</label>
          <div class="contract-selector">
            <input 
              type="text" 
              v-model="contractSearch" 
              placeholder="搜索合约名称、代码或交易所..."
              class="form-control contract-search"
              @input="filterContracts"
            >
            <select v-model="queryParams.symbol" class="form-control">
              <option value="">请选择合约</option>
              <option 
                v-for="contract in filteredContracts" 
                :key="contract.symbol" 
                :value="contract.name"
              >
                {{ contract.exchange }} - {{ contract.name }} ({{ contract.symbol }})
              </option>
            </select>
          </div>
        </div>
        
        <div class="form-group">
          <label>周期:</label>
          <select v-model="queryParams.period" class="form-control">
            <option 
              v-for="period in periods" 
              :key="period.value" 
              :value="period.value"
            >
              {{ period.label }}
            </option>
          </select>
        </div>
        
        <div class="form-group">
          <label>开始日期:</label>
          <input 
            type="date" 
            v-model="queryParams.startDate" 
            class="form-control"
          >
        </div>
        
        <div class="form-group">
          <label>结束日期:</label>
          <input 
            type="date" 
            v-model="queryParams.endDate" 
            class="form-control"
          >
        </div>
        
        <div class="form-group">
          <button 
            @click="queryData" 
            :disabled="loading || !queryParams.symbol"
            class="btn btn-primary"
          >
            {{ loading ? '查询中...' : '查询' }}
          </button>
          
          <button 
            @click="refreshContracts" 
            :disabled="contractsLoading"
            class="btn btn-secondary"
          >
            {{ contractsLoading ? '刷新中...' : '刷新合约' }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- 数据表格 -->
    <div class="data-table" v-if="tableData.length > 0">
      <h3>{{ currentSymbol }} - {{ getCurrentPeriodLabel() }} 数据 ({{ tableData.length }}条记录)</h3>
      <div class="table-container">
        <table class="table">
          <thead>
            <tr>
              <th v-if="visibleColumns.time">时间</th>
              <th v-if="visibleColumns.close">收盘价</th>
              <th v-if="visibleColumns.changePercent">涨跌幅(%)</th>
              <th v-if="visibleColumns.volume">成交量</th>
              <th v-if="visibleColumns.openInterest">持仓量</th>
              <th v-if="visibleColumns.dailyChange">日增仓</th>
              <th v-if="visibleColumns.open">开盘</th>
              <th v-if="visibleColumns.high">最高</th>
              <th v-if="visibleColumns.low">最低</th>
              <th v-if="visibleColumns.change">涨跌</th>
              <th v-if="visibleColumns.turnover">成交额</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in tableData" :key="index">
              <td v-if="visibleColumns.time">{{ row.时间 }}</td>
              <td v-if="visibleColumns.close" :class="getPriceClass(row.涨跌)">{{ row.收盘 }}</td>
              <td v-if="visibleColumns.changePercent" :class="getPriceClass(row.涨跌)">{{ row.涨跌幅 }}%</td>
              <td v-if="visibleColumns.volume">{{ row.成交量 }}</td>
              <td v-if="visibleColumns.openInterest">{{ row.持仓量 }}</td>
              <td v-if="visibleColumns.dailyChange" :class="getPositionChangeClass(row.日增仓)">{{ row.日增仓 }}</td>
              <td v-if="visibleColumns.open">{{ row.开盘 }}</td>
              <td v-if="visibleColumns.high">{{ row.最高 }}</td>
              <td v-if="visibleColumns.low">{{ row.最低 }}</td>
              <td v-if="visibleColumns.change" :class="getPriceClass(row.涨跌)">{{ row.涨跌 }}</td>
              <td v-if="visibleColumns.turnover">{{ row.成交额 }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
    
    <!-- 空数据提示 -->
    <div v-else-if="!loading && hasQueried" class="no-data">
      <p>暂无数据</p>
    </div>
    
    <!-- 错误信息 -->
    <div v-if="error" class="error-message">
      <p>{{ error }}</p>
    </div>
  </div>
</template>

<script>
import { request5000 } from '../utils/request'

export default {
  name: 'TechnicalAnalysis',
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
      // 列可见性控制
      visibleColumns: {
        time: true,
        close: true,
        changePercent: true,
        volume: true,
        openInterest: true,
        dailyChange: true,
        open: false,
        high: false,
        low: false,
        change: false,
        turnover: false
      },
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
    visibleColumns: {
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
        const response = await request5000.get('/api/futures/contracts')
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
        const response = await request5000.get('/api/futures/periods')
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
        await request5000.post('/api/futures/refresh-contracts')
        await this.loadContracts()
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
        this.error = '请选择合约'
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
        
        const response = await request5000.get('/api/futures/history', { params })
        
        this.tableData = response.data || []
        this.currentSymbol = response.symbol || this.queryParams.symbol
        this.hasQueried = true
        
      } catch (error) {
        this.error = `查询数据失败: ${error.message}`
        console.error('查询数据失败:', error)
        this.tableData = []
      } finally {
        this.loading = false
      }
    },
    
    // 列显示控制方法
    showAllColumns() {
      this.availableColumns.forEach(column => {
        this.visibleColumns[column.key] = true
      })
    },
    
    hideAllColumns() {
      this.availableColumns.forEach(column => {
        this.visibleColumns[column.key] = false
      })
    },
    
    resetToDefault() {
      this.visibleColumns = {
        time: true,
        close: true,
        changePercent: true,
        volume: true,
        openInterest: true,
        dailyChange: true,
        open: false,
        high: false,
        low: false,
        change: false,
        turnover: false
      }
    },
    
    // 保存列设置到本地存储
    saveColumnSettings() {
      try {
        localStorage.setItem('futuresTableColumnSettings', JSON.stringify(this.visibleColumns))
      } catch (error) {
        console.warn('保存列设置失败:', error)
      }
    },
    
    // 从本地存储加载列设置
    loadColumnSettings() {
      try {
        const saved = localStorage.getItem('futuresTableColumnSettings')
        if (saved) {
          const settings = JSON.parse(saved)
          this.visibleColumns = { ...this.visibleColumns, ...settings }
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
      return ''
    },
    
    // 获取持仓变化样式类
    getPositionChangeClass(change) {
      if (change.includes('增仓')) return 'position-up'
      if (change.includes('减仓')) return 'position-down'
      return ''
    }
  }
}
</script>

<style scoped>
.technical-analysis {
  padding: 20px;
  background: #f8f9fa;
  min-height: 100vh;
}

.header h2 {
  color: #333;
  margin-bottom: 20px;
  text-align: center;
}

.column-controls {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

.controls-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.controls-header h4 {
  margin: 0;
  color: #333;
  font-size: 16px;
}

.control-buttons {
  display: flex;
  gap: 8px;
}

.btn-sm {
  padding: 4px 8px;
  font-size: 12px;
}

.btn-outline {
  background-color: transparent;
  color: #007bff;
  border: 1px solid #007bff;
}

.btn-outline:hover:not(:disabled) {
  background-color: #007bff;
  color: white;
}

.column-checkboxes {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 5px 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.checkbox-label:hover {
  background-color: #f8f9fa;
}

.checkbox-input {
  margin-right: 8px;
  cursor: pointer;
}

.checkbox-text {
  font-size: 14px;
  color: #555;
  user-select: none;
}

.query-form {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  margin-bottom: 20px;
}

.form-row {
  display: flex;
  gap: 15px;
  align-items: end;
  flex-wrap: wrap;
}

.form-group {
  display: flex;
  flex-direction: column;
  min-width: 150px;
}

.form-group label {
  font-weight: bold;
  margin-bottom: 5px;
  color: #555;
}

.form-control {
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 14px;
}

.form-control:focus {
  outline: none;
  border-color: #007bff;
  box-shadow: 0 0 0 2px rgba(0,123,255,0.25);
}

.contract-selector {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.contract-search {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  font-size: 13px;
}

.contract-search:focus {
  background-color: white;
}

.btn {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  transition: background-color 0.2s;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background-color: #007bff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background-color: #0056b3;
}

.btn-secondary {
  background-color: #6c757d;
  color: white;
  margin-left: 10px;
}

.btn-secondary:hover:not(:disabled) {
  background-color: #545b62;
}

.data-table {
  background: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.data-table h3 {
  color: #333;
  margin-bottom: 15px;
}

.table-container {
  overflow-x: auto;
}

.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 14px;
}

.table th,
.table td {
  padding: 10px 8px;
  text-align: center;
  border-bottom: 1px solid #dee2e6;
}

.table th {
  background-color: #f8f9fa;
  font-weight: bold;
  color: #495057;
  position: sticky;
  top: 0;
}

.table tbody tr:hover {
  background-color: #f8f9fa;
}

.price-up {
  color: #dc3545;
  font-weight: bold;
}

.price-down {
  color: #28a745;
  font-weight: bold;
}

.position-up {
  color: #dc3545;
  font-weight: bold;
}

.position-down {
  color: #28a745;
  font-weight: bold;
}

.no-data {
  text-align: center;
  padding: 40px;
  color: #6c757d;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.error-message {
  background-color: #f8d7da;
  color: #721c24;
  padding: 15px;
  border-radius: 4px;
  margin-top: 10px;
  border: 1px solid #f5c6cb;
}

@media (max-width: 768px) {
  .controls-header {
    flex-direction: column;
    align-items: stretch;
    gap: 10px;
  }
  
  .column-checkboxes {
    grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
  }
  
  .form-row {
    flex-direction: column;
  }
  
  .form-group {
    min-width: 100%;
  }
  
  .table-container {
    font-size: 12px;
  }
  
  .table th,
  .table td {
    padding: 6px 4px;
  }
}
</style>
