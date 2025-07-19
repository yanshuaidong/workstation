<template>
  <div class="api-section">
    <h2>第三方API数据获取</h2>
    
    <!-- 下拉选择区域 -->
    <div class="selector-section">
      <el-card class="selector-card">
        <h4>品种和合约选择</h4>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="选择品种:">
              <el-select 
                v-model="selectedVariety" 
                placeholder="请选择品种"
                @change="onVarietyChange"
                :loading="loadingVarieties"
                size="large"
                style="width: 100%"
              >
                <el-option
                  v-for="variety in varieties"
                  :key="variety.symbol"
                  :label="`${variety.name} (${variety.symbol})`"
                  :value="variety.symbol"
                >
                  <span style="float: left">{{ variety.name }}</span>
                  <span style="float: right; color: #8492a6; font-size: 13px">{{ variety.market }}</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="选择合约:">
              <el-select 
                v-model="selectedContract" 
                placeholder="请先选择品种"
                :disabled="!selectedVariety || loadingContracts"
                :loading="loadingContracts"
                size="large"
                style="width: 100%"
              >
                <el-option
                  v-for="contract in contracts"
                  :key="contract.code"
                  :label="contract.code"
                  :value="contract.code"
                >
                  <span style="float: left">{{ contract.code }}</span>
                  <span style="float: right; color: #8492a6; font-size: 13px">{{ formatValue(contract.value) }}</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <!-- 获取品种结构按钮 -->
        <div class="button-group">
          <el-button 
            @click="fetchVarietyStructure" 
            :loading="loadingStructure"
            type="warning"
            size="large"
            :icon="Refresh"
            :disabled="!selectedVariety"
          >
            {{ loadingStructure ? '获取中...' : '获取品种结构' }}
          </el-button>
          <el-button 
            @click="fetchVarietyDates" 
            :loading="loadingDates"
            type="success"
            size="large"
            :icon="Calendar"
            :disabled="!selectedVariety"
          >
            {{ loadingDates ? '获取中...' : '获取品种日期' }}
          </el-button>
          <el-button 
            @click="fetchVarietyProfitLoss" 
            :loading="loadingProfitLoss"
            type="primary"
            size="large"
            :icon="Refresh"
            :disabled="!selectedVariety"
          >
            {{ loadingProfitLoss ? '获取中...' : '获取品种盈亏' }}
          </el-button>
        </div>
      </el-card>
    </div>

    <!-- 数据展示区域 -->
    <div v-if="selectedVarietyData" class="data-display">
      <h3>当前选择的品种信息：</h3>
      <el-card class="info-card">
        <el-descriptions :column="3" border>
          <el-descriptions-item label="品种名称">{{ selectedVarietyData.name }}</el-descriptions-item>
          <el-descriptions-item label="品种代码">{{ selectedVarietyData.symbol }}</el-descriptions-item>
          <el-descriptions-item label="所属市场">{{ selectedVarietyData.market }}</el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>

    <div v-if="selectedContractData" class="data-display">
      <h3>当前选择的合约信息：</h3>
      <el-card class="info-card">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="合约代码">{{ selectedContractData.code }}</el-descriptions-item>
          <el-descriptions-item label="合约价值">{{ formatValue(selectedContractData.value) }}</el-descriptions-item>
        </el-descriptions>
      </el-card>
    </div>
    
    <div v-if="structureData" class="data-display">
      <h3>品种结构数据：</h3>
      <el-card class="json-card">
        <pre class="json-display">{{ JSON.stringify(structureData, null, 2) }}</pre>
      </el-card>
    </div>

    <div v-if="datesData" class="data-display">
      <h3>品种日期数据：</h3>
      <el-card class="json-card">
        <pre class="json-display">{{ JSON.stringify(datesData, null, 2) }}</pre>
      </el-card>
    </div>

    <div v-if="profitLossData" class="data-display">
      <h3>品种盈亏数据：</h3>
      <el-card class="json-card">
        <pre class="json-display">{{ JSON.stringify(profitLossData, null, 2) }}</pre>
      </el-card>
    </div>

    <!-- 盈利最多的机构展示 -->
    <div v-if="topProfitableBrokers.length > 0" class="data-display">
      <h3>盈利最多的机构 (前{{ topProfitableBrokers.length }}名)：</h3>
      <el-card class="brokers-card">
        <div class="brokers-list">
          <el-tag
            v-for="(broker, index) in topProfitableBrokers"
            :key="index"
            :type="getBrokerTagType(index)"
            size="large"
            effect="dark"
            class="broker-tag"
          >
            <el-icon><Trophy /></el-icon>
            第{{ index + 1 }}名: {{ broker }}
          </el-tag>
        </div>
      </el-card>
    </div>

    <!-- 盈利机构持仓结构表格 -->
    <div v-if="brokersStructureTable" class="data-display">
      <h3>盈利机构持仓结构 (最近20天)：</h3>
      <el-card class="structure-table-card">
        <div class="markdown-table" v-html="renderMarkdownTable(brokersStructureTable)"></div>
      </el-card>
    </div>
    
    <!-- 错误信息展示 -->
    <div v-if="error" class="error-display">
      <el-alert
        :title="error"
        type="error"
        description="API调用过程中发生错误"
        show-icon
        :closable="false"
      />
    </div>
  </div>
</template>

<script>
import axios from '@/utils/request'
import { getVarietiesApi, getRecentContractsApi, getVarietyStructureApi, getVarietyDatesApi, getVarietyProfitLossApi } from '@/api'
import { Refresh, Calendar, Trophy } from '@element-plus/icons-vue'
import { markRaw } from 'vue'

export default {
  name: 'ApiDataFetcher',
  data() {
    return {
      loadingVarieties: false,    // 品种数据加载状态
      loadingContracts: false,    // 合约数据加载状态
      loadingStructure: false,    // 品种结构数据加载状态
      loadingDates: false,        // 品种日期数据加载状态
      loadingProfitLoss: false,   // 品种盈亏数据加载状态
      varieties: [],              // 品种列表数据
      contracts: [],              // 合约列表数据
      selectedVariety: '',        // 选中的品种代码
      selectedContract: '',       // 选中的合约代码
      structureData: null,        // 品种结构数据
      datesData: null,            // 品种日期数据
      profitLossData: null,       // 品种盈亏数据
      topProfitableBrokers: [],   // 盈利最多的前5个机构
      brokersStructureTable: '',  // 盈利机构的结构表格（markdown格式）
      error: null,                // 错误信息
      Refresh: markRaw(Refresh),  // Element Plus 刷新图标
      Calendar: markRaw(Calendar), // Element Plus 日历图标
      Trophy: markRaw(Trophy)    // Element Plus 奖杯图标
    }
  },
  computed: {
    /**
     * 获取当前选中的品种完整数据
     * @returns {Object|undefined} 品种数据对象
     */
    selectedVarietyData() {
      return this.varieties.find(v => v.symbol === this.selectedVariety)
    },
    
    /**
     * 获取当前选中的合约完整数据
     * @returns {Object|undefined} 合约数据对象
     */
    selectedContractData() {
      return this.contracts.find(c => c.code === this.selectedContract)
    }
  },
  
  /**
   * 组件挂载完成后执行初始化
   */
  async mounted() {
    // 执行完整的初始化流程
    await this.initializeData()
  },
  
  methods: {
    /**
     * 初始化数据流程
     * 1. 获取所有品种
     * 2. 自动选择第一个品种
     * 3. 获取该品种的合约列表
     * 4. 自动选择第一个合约
     * 5. 获取品种可用日期
     * 6. 根据日期范围自动请求盈亏数据
     * 7. 显示盈利最多的前5个机构
     */
    async initializeData() {
      try {
        // 第一步：获取所有品种数据
        await this.fetchVarieties()
        
        // 第二步：如果有品种数据，自动选择第一个
        if (this.varieties && this.varieties.length > 0) {
          this.selectedVariety = this.varieties[0].symbol
          console.log('自动选择第一个品种:', this.varieties[0])
          
          // 第三步：获取第一个品种的合约列表
          await this.fetchContracts(this.selectedVariety)
          
          // 第四步：如果有合约数据，自动选择第一个
          if (this.contracts && this.contracts.length > 0) {
            this.selectedContract = this.contracts[0].code
            console.log('自动选择第一个合约:', this.contracts[0])
          }
          
          // 第五步：获取品种可用日期
          await this.fetchVarietyDates()
          
          // 第六步：根据日期范围自动请求盈亏数据
          if (this.datesData) {
            await this.autoFetchProfitLossData()
          }
        }
      } catch (error) {
        console.error('初始化数据失败:', error)
        this.error = '初始化数据失败'
      }
    },

    /**
     * 获取所有品种数据
     * 调用后端API获取品种列表
     */
    async fetchVarieties() {
      this.loadingVarieties = true
      this.error = null
      
      try {
        // 调用获取品种列表的API
        const response = await axios.post(getVarietiesApi, {})
        console.log('品种API响应:', response)

        // 检查响应状态码
        if (response.code === 0) {
          this.varieties = response.data || []
          console.log('成功获取品种列表:', this.varieties)
        } else {
          this.error = response.msg || '获取品种数据失败'
          console.error('获取品种失败:', response.msg)
        }
      } catch (err) {
        this.error = err.message
        console.error('获取品种API调用错误:', err)
      } finally {
        this.loadingVarieties = false
      }
    },

    /**
     * 品种选择变化时的处理函数
     * @param {string} varietySymbol 选中的品种代码
     */
    async onVarietyChange(varietySymbol) {
      // 如果没有选择品种，清空合约相关数据
      if (!varietySymbol) {
        this.contracts = []
        this.selectedContract = ''
        this.brokersStructureTable = ''
        return
      }
      
      // 获取该品种的合约列表
      await this.fetchContracts(varietySymbol)
      
      // 自动选择第一个合约（如果有的话）
      if (this.contracts && this.contracts.length > 0) {
        this.selectedContract = this.contracts[0].code
        console.log('品种变化后自动选择第一个合约:', this.contracts[0])
      }
    },

    /**
     * 获取指定品种的合约列表
     * @param {string} varietySymbol 品种代码
     */
    async fetchContracts(varietySymbol) {
      this.loadingContracts = true
      this.error = null
      this.contracts = []
      this.selectedContract = ''
      
      try {
        // 根据品种代码查找品种数据
        const varietyData = this.varieties.find(v => v.symbol === varietySymbol)
        
        // 调用获取合约列表的API
        const response = await axios.post(getRecentContractsApi, {
          variety: varietyData ? varietyData.name : varietySymbol,
          date: ''
        })
        
        console.log('合约API响应:', response)
        
        // 检查响应状态码
        if (response.code === 0) {
          this.contracts = response.data || []
          console.log('成功获取合约列表:', this.contracts)
        } else {
          this.error = response.msg || '获取合约数据失败'
          console.error('获取合约失败:', response.msg)
        }
      } catch (err) {
        this.error = err.message
        console.error('获取合约API调用错误:', err)
      } finally {
        this.loadingContracts = false
      }
    },

    /**
     * 获取品种结构数据
     * 根据当前选中的品种和合约获取详细的结构信息
     */
    async fetchVarietyStructure() {
      // 检查是否已选择品种
      if (!this.selectedVariety) {
        this.error = '请先选择品种'
        return
      }

      this.loadingStructure = true
      this.error = null
      this.structureData = null
      
      try {
        // 获取当前选中的品种数据
        const varietyData = this.selectedVarietyData
        
        // 调用获取品种结构的API
        const response = await axios.post(getVarietyStructureApi, {
          variety: varietyData.name,
          code: this.selectedContract || '',
          broker_type: 'all'
        })
        
        console.log('品种结构API响应:', response)
        
        // 检查响应状态码
        if (response.code === 0) {
          this.structureData = response.data
          console.log('成功获取品种结构数据:', this.structureData)
        } else {
          this.error = response.msg || '获取品种结构数据失败'
          console.error('获取品种结构失败:', response.msg)
        }
      } catch (err) {
        this.error = err.message
        console.error('品种结构API调用错误:', err)
      } finally {
        this.loadingStructure = false
      }
    },

    /**
     * 获取品种日期数据
     * 根据当前选中的品种获取其可交易日期列表
     */
    async fetchVarietyDates() {
      // 检查是否已选择品种
      if (!this.selectedVariety) {
        this.error = '请先选择品种'
        return
      }

      this.loadingDates = true
      this.error = null
      this.datesData = null
      
      try {
        // 获取当前选中的品种数据
        const varietyData = this.selectedVarietyData
        
        // 调用获取品种日期的API
        const response = await axios.post(getVarietyDatesApi, {
          variety: varietyData.name
        })
        
        console.log('品种日期API响应:', response)
        
        // 检查响应状态码
        if (response.code === 0) {
          const rawData = response.data
          console.log('成功获取品种日期数据:', rawData)
          
          // 解析日期数据
          const firstDate = new Date(rawData.first_date)
          const lastDate = new Date(rawData.last_date)
          
          // 计算可用的时间范围（年数）
          const totalYears = (lastDate - firstDate) / (1000 * 60 * 60 * 24 * 365)
          console.log(`数据可用时间范围: ${totalYears.toFixed(1)} 年`)
          
          // 确定请求的开始日期
          let startDate
          if (totalYears >= 3) {
            // 如果有3年或以上数据，请求过去3年的数据
            startDate = new Date()
            startDate.setFullYear(startDate.getFullYear() - 3)
            console.log('数据充足，请求过去3年的数据')
          } else {
            // 如果不足3年，使用第一个可用日期
            startDate = firstDate
            console.log(`数据不足3年，请求全部可用数据 (${totalYears.toFixed(1)} 年)`)
          }
          
          // 格式化日期为YYYY-MM-DD格式
          const formatDate = (date) => {
            return date.toISOString().split('T')[0]
          }
          
          // 保存处理后的日期数据
          this.datesData = {
            ...rawData,
            start_date: formatDate(startDate),
            end_date: '', // 空字符串表示到当前日期
            available_years: totalYears,
            request_years: totalYears >= 3 ? 3 : totalYears
          }
          
          console.log('处理后的日期数据:', this.datesData)
        } else {
          this.error = response.msg || '获取品种日期数据失败'
          console.error('获取品种日期失败:', response.msg)
        }
      } catch (err) {
        this.error = err.message
        console.error('品种日期API调用错误:', err)
      } finally {
        this.loadingDates = false
      }
    },

    /**
     * 获取品种盈亏数据
     * 根据当前选中的品种获取其盈亏情况
     */
    async fetchVarietyProfitLoss() {
      // 检查是否已选择品种
      if (!this.selectedVariety) {
        this.error = '请先选择品种'
        return
      }

      this.loadingProfitLoss = true
      this.error = null
      this.profitLossData = null
      
      try {
        // 获取当前选中的品种数据
        const varietyData = this.selectedVarietyData
        
        // 调用获取品种盈亏的API（使用写死的参数）
        const response = await axios.post(getVarietyProfitLossApi, {
          variety: varietyData.name,
          date1: '2024-07-01',  // 写死的开始日期
          date2: ''             // 写死的结束日期（空表示到当前）
        })
        
        console.log('品种盈亏API响应:', response)
        
        // 检查响应状态码
        if (response.code === 0) {
          this.profitLossData = response.data
          console.log('成功获取品种盈亏数据:', this.profitLossData)
        } else {
          this.error = response.msg || '获取品种盈亏数据失败'
          console.error('获取品种盈亏失败:', response.msg)
        }
      } catch (err) {
        this.error = err.message
        console.error('品种盈亏API调用错误:', err)
      } finally {
        this.loadingProfitLoss = false
      }
    },

    /**
     * 自动请求盈亏数据
     * 根据当前选中的品种和合约，以及日期范围，自动请求并更新盈亏数据
     */
    async autoFetchProfitLossData() {
      // 检查是否已选择品种
      if (!this.selectedVariety) {
        this.error = '请先选择品种'
        return
      }

      this.loadingProfitLoss = true
      this.error = null
      this.profitLossData = null
      this.topProfitableBrokers = []

      try {
        // 获取当前选中的品种数据
        const varietyData = this.selectedVarietyData
        
        // 调用获取品种盈亏的API
        const response = await axios.post(getVarietyProfitLossApi, {
          variety: varietyData.name,
          date1: this.datesData.start_date, // 使用计算出的开始日期
          date2: this.datesData.end_date    // 空字符串表示到当前日期
        })
        
        console.log('自动请求盈亏API响应:', response)
        
        // 检查响应状态码
        if (response.code === 0) {
          this.profitLossData = response.data
          console.log('成功获取品种盈亏数据:', this.profitLossData)

          // 从返回的数据中提取brokers数组
          if (this.profitLossData && this.profitLossData.brokers && Array.isArray(this.profitLossData.brokers)) {
            const brokers = this.profitLossData.brokers
            console.log('所有机构列表:', brokers)
            
            // 获取倒数5个机构（盈利最多的机构）
            const topCount = Math.min(5, brokers.length)
            this.topProfitableBrokers = brokers.slice(-topCount).reverse()
            
            console.log(`成功获取盈利最多的前${topCount}个机构:`, this.topProfitableBrokers)
            
            // 自动获取这些机构的品种结构数据并生成表格
            await this.fetchAndGenerateBrokersTable()
          } else {
            console.warn('API响应中没有找到brokers数组或数组为空')
            this.topProfitableBrokers = []
            this.brokersStructureTable = ''
          }
        } else {
          this.error = response.msg || '获取品种盈亏数据失败'
          console.error('获取品种盈亏失败:', response.msg)
        }
      } catch (err) {
        this.error = err.message
        console.error('自动请求盈亏API调用错误:', err)
      } finally {
        this.loadingProfitLoss = false
      }
    },

    /**
     * 格式化数值显示
     * 将大数值转换为更易读的格式（K、M、B、T等单位）
     * @param {number} value 要格式化的数值
     * @returns {string} 格式化后的字符串
     */
    formatValue(value) {
      if (!value) return '-'
      
      // 根据数值大小添加相应的单位后缀
      if (value >= 1000000000000) {
        return (value / 1000000000000).toFixed(2) + 'T'  // 万亿
      } else if (value >= 1000000000) {
        return (value / 1000000000).toFixed(2) + 'B'     // 十亿
      } else if (value >= 1000000) {
        return (value / 1000000).toFixed(2) + 'M'        // 百万
      } else if (value >= 1000) {
        return (value / 1000).toFixed(2) + 'K'           // 千
      }
      return value.toString()
    },

    /**
     * 根据机构排名设置标签类型
     * @param {number} index 机构在列表中的索引
     * @returns {string} 标签类型，如 'success', 'info', 'warning', 'danger'
     */
    getBrokerTagType(index) {
      if (index === 0) {
        return 'success' // 第一名
      } else if (index === 1) {
        return 'info'    // 第二名
      } else if (index === 2) {
        return 'warning' // 第三名
      } else {
        return 'primary' // 其他名次
      }
    },

    /**
     * 获取盈利机构的品种结构数据并生成表格
     * 在获取到盈利最多的机构后，自动调用品种结构接口并生成markdown表格
     */
    async fetchAndGenerateBrokersTable() {
      if (!this.selectedVariety || this.topProfitableBrokers.length === 0) {
        console.log('无法生成表格：缺少品种或机构数据')
        return
      }

      try {
        console.log('开始获取盈利机构的品种结构数据...')
        
        // 获取当前选中的品种数据
        const varietyData = this.selectedVarietyData
        
        // 调用获取品种结构的API
        const response = await axios.post(getVarietyStructureApi, {
          variety: varietyData.name,
          code: this.selectedContract || '',
          broker_type: 'all'
        })
        
        console.log('品种结构API响应:', response)
        
        if (response.code === 0 && response.data && response.data.data) {
          const structureData = response.data.data
          console.log('成功获取品种结构数据:', structureData)
          
          // 生成markdown表格
          this.brokersStructureTable = this.generateBrokersTable(structureData)
          console.log('生成的表格:', this.brokersStructureTable)
        } else {
          console.error('获取品种结构失败:', response.msg)
          this.brokersStructureTable = '获取品种结构数据失败'
        }
      } catch (err) {
        console.error('获取品种结构API调用错误:', err)
        this.brokersStructureTable = '获取品种结构数据时发生错误'
      }
    },

    /**
     * 根据品种结构数据生成markdown表格
     * @param {Object} structureData 品种结构数据
     * @returns {string} markdown格式的表格字符串
     */
    generateBrokersTable(structureData) {
      try {
        console.log('开始处理品种结构数据:', structureData)
        console.log('type:', typeof structureData.data)
        if (!structureData || !Array.isArray(structureData)) {
          return '品种结构数据格式错误'
        }

        const data = structureData;
        console.log('开始处理品种结构数据:', data)
        
        // 找到日期行（第一行）
        const dateRow = data.find(row => Array.isArray(row) && row[0] === 'dates')
        if (!dateRow) {
          return '未找到日期数据'
        }

        // 提取日期（跳过第一个元素'dates'，获取最近20天的日期）
        const allDates = dateRow.slice(1)
        const recentDates = allDates.slice(-20).reverse() // 取最近20天并倒序排列
        console.log('最近20天日期（倒序）:', recentDates)

        // 查找匹配的机构数据
        const matchedBrokers = []
        
        for (let i = 0; i < this.topProfitableBrokers.length; i++) {
          const brokerName = this.topProfitableBrokers[i]
          console.log(`查找机构: ${brokerName}`)
          
          // 在品种结构数据中查找匹配的机构
          const brokerRow = data.find(row => 
            Array.isArray(row) && 
            row.length > 1 && 
            row[0] === brokerName
          )
          
          if (brokerRow) {
            // 获取该机构对应日期的数据（跳过第一个元素机构名称）
            const brokerData = brokerRow.slice(1)
            const recentBrokerData = brokerData.slice(-20).reverse() // 对应最近20天并倒序
            
            matchedBrokers.push({
              name: brokerName,
              rank: i + 1,
              data: recentBrokerData
            })
            console.log(`找到机构 ${brokerName} 的数据:`, recentBrokerData)
          } else {
            console.log(`未找到机构 ${brokerName} 的数据`)
            // 即使没找到数据，也要添加占位符
            matchedBrokers.push({
              name: brokerName,
              rank: i + 1,
              data: new Array(recentDates.length).fill(0)
            })
          }
        }

        // 生成表格标题行
        const headers = ['日期']
        matchedBrokers.forEach(broker => {
          headers.push(`${broker.name}（近三年盈利第${broker.rank}席位）`)
        })

        // 生成markdown表格
        let table = `| ${headers.join(' | ')} |\n`
        table += `| ${headers.map(() => '----------').join(' | ')} |\n`

        // 生成数据行
        for (let dateIndex = 0; dateIndex < recentDates.length; dateIndex++) {
          const row = [recentDates[dateIndex]]
          
          matchedBrokers.forEach(broker => {
            const value = broker.data[dateIndex] || 0
            const formattedValue = this.formatPositionValue(value)
            row.push(formattedValue)
          })
          
          table += `| ${row.join(' | ')} |\n`
        }

        return table
      } catch (error) {
        console.error('生成表格时发生错误:', error)
        return '生成表格时发生错误'
      }
    },

    /**
     * 格式化持仓数值
     * 将数值转换为"净多 X.X 亿"或"净空 X.X 亿"的格式
     * @param {number} value 持仓数值
     * @returns {string} 格式化后的字符串
     */
    formatPositionValue(value) {
      if (!value || value === 0) {
        return '持平'
      }

      // 转换为亿为单位
      const absValue = Math.abs(value)
      const valueInYi = absValue / 100000000 // 1亿 = 100000000

      // 格式化为1位小数
      const formattedValue = valueInYi.toFixed(1)

      // 判断正负
      if (value > 0) {
        return `净多 ${formattedValue} 亿`
             } else {
         return `净空 ${formattedValue} 亿`
       }
     },

     /**
      * 渲染markdown表格为HTML
      * @param {string} markdownTable markdown格式的表格字符串
      * @returns {string} HTML格式的表格
      */
     renderMarkdownTable(markdownTable) {
       if (!markdownTable) return ''
       
       try {
         // 将markdown表格转换为HTML表格
         const lines = markdownTable.trim().split('\n')
         if (lines.length < 3) return markdownTable // 至少需要标题行、分隔行、数据行
         
         let html = '<table class="custom-table">'
         
         // 处理标题行
         const headerLine = lines[0]
         const headers = headerLine.split('|').slice(1, -1).map(h => h.trim())
         html += '<thead><tr>'
         headers.forEach(header => {
           html += `<th>${header}</th>`
         })
         html += '</tr></thead>'
         
         // 处理数据行（跳过分隔行）
         html += '<tbody>'
         for (let i = 2; i < lines.length; i++) {
           const dataLine = lines[i]
           const cells = dataLine.split('|').slice(1, -1).map(c => c.trim())
           html += '<tr>'
           cells.forEach((cell) => {
             let cellClass = ''
             if (cell.includes('净多')) {
               cellClass = 'class="net-long"'
             } else if (cell.includes('净空')) {
               cellClass = 'class="net-short"'
             }
             html += `<td ${cellClass}>${cell}</td>`
           })
           html += '</tr>'
         }
         html += '</tbody></table>'
         
         return html
       } catch (error) {
         console.error('渲染表格时发生错误:', error)
         return `<pre>${markdownTable}</pre>` // 回退到显示原始markdown
       }
     }
  }
}
</script>

<style scoped>
.api-section {
  margin-top: 40px;
  padding: 20px;
  border: 1px solid #ddd;
  border-radius: 8px;
  max-width: 1200px;
  margin: 40px auto;
}

.selector-section {
  margin-bottom: 20px;
}

.selector-card {
  margin-bottom: 20px;
}

.selector-card h4 {
  margin-bottom: 15px;
  color: #303133;
}

.button-group {
  display: flex;
  gap: 15px;
  justify-content: center;
  flex-wrap: wrap;
  margin-top: 20px;
}

.data-display {
  margin-top: 20px;
  text-align: left;
}

.info-card {
  margin-top: 10px;
}

.json-card {
  margin-top: 10px;
}

.json-display {
  background-color: #f5f5f5;
  border: none;
  border-radius: 4px;
  padding: 15px;
  max-height: 400px;
  overflow-y: auto;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  white-space: pre-wrap;
  word-wrap: break-word;
  margin: 0;
}

.error-display {
  margin-top: 20px;
}

.el-form-item {
  margin-bottom: 15px;
}

.el-form-item__label {
  font-weight: 500;
  color: #606266;
}

.el-select {
  width: 100%;
}

/* 盈利机构展示样式 */
.brokers-card {
  margin-top: 10px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.brokers-list {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
  justify-content: center;
  padding: 10px 0;
}

.broker-tag {
  padding: 12px 20px;
  font-size: 16px;
  font-weight: 600;
  border-radius: 25px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s ease-in-out;
}

.broker-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.3);
}

.broker-tag .el-icon {
  margin-right: 8px;
}

/* 持仓结构表格样式 */
.structure-table-card {
  margin-top: 10px;
  overflow-x: auto;
}

.markdown-table {
  width: 100%;
  overflow-x: auto;
}

.custom-table {
  width: 100%;
  border-collapse: collapse;
  margin: 0;
  font-size: 14px;
  background-color: white;
}

.custom-table th,
.custom-table td {
  border: 1px solid #e4e7ed;
  padding: 12px 8px;
  text-align: center;
  vertical-align: middle;
}

.custom-table th {
  background-color: #f5f7fa;
  font-weight: 600;
  color: #303133;
  white-space: nowrap;
}

.custom-table td {
  color: #606266;
  white-space: nowrap;
}

.custom-table tbody tr:nth-child(even) {
  background-color: #fafafa;
}

.custom-table tbody tr:hover {
  background-color: #f0f9ff;
}

/* 净多净空的颜色区分 */
.custom-table td.net-long {
  color: #67c23a;
  font-weight: 500;
}

.custom-table td.net-short {
  color: #f56c6c;
  font-weight: 500;
}
</style> 