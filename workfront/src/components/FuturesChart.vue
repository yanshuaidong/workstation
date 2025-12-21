<template>
  <div class="futures-chart">
    <!-- 控制面板 -->
    <el-card class="control-card">
      <template #header>
        <div class="card-header">
          <span>期货K线图</span>
        </div>
      </template>

      <el-row :gutter="20" align="middle">
        <!-- 合约选择 -->
        <el-col :span="6">
          <el-form-item label="选择品种">
            <el-select
              v-model="selectedContract"
              placeholder="请选择期货品种"
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
          <el-form-item label="日期范围">
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
          </el-form-item>
        </el-col>

        <!-- 查询按钮 -->
        <el-col :span="4">
          <el-form-item label=" ">
            <el-button
              type="primary"
              @click="queryData"
              :loading="loading"
              icon="Search"
              style="width: 100%"
            >
              查询
            </el-button>
          </el-form-item>
        </el-col>

        <!-- 快捷日期 -->
        <el-col :span="6">
          <el-form-item label="快捷选择">
            <el-button-group>
              <el-button size="small" @click="setDateRange(30)">近30天</el-button>
              <el-button size="small" @click="setDateRange(60)">近60天</el-button>
              <el-button size="small" @click="setDateRange(90)">近90天</el-button>
            </el-button-group>
          </el-form-item>
        </el-col>
      </el-row>
    </el-card>

    <!-- 图表展示区 -->
    <el-card class="chart-card" v-loading="loading">
      <template #header>
        <div class="card-header">
          <span>{{ chartTitle }}</span>
          <span v-if="historyData.length" class="data-count">
            （共 {{ historyData.length }} 条数据）
          </span>
        </div>
      </template>

      <!-- K线图容器 -->
      <div 
        ref="chartContainer" 
        class="chart-container"
        v-show="historyData.length > 0"
      ></div>

      <!-- 空状态 -->
      <el-empty 
        v-show="historyData.length === 0 && !loading"
        description="请选择期货品种并查询数据"
      />
    </el-card>

    <!-- 数据表格 -->
    <el-card class="table-card" v-if="historyData.length > 0">
      <template #header>
        <div class="card-header">
          <span>数据明细</span>
          <el-switch
            v-model="showTable"
            active-text="显示表格"
            inactive-text="隐藏表格"
          />
        </div>
      </template>

      <el-collapse-transition>
        <div v-show="showTable">
          <el-table
            :data="historyData"
            stripe
            border
            style="width: 100%"
            max-height="400"
          >
            <el-table-column type="index" label="序号" width="60" :index="(index) => index + 1" />
            <el-table-column prop="raw.trade_date" label="日期" width="110" />
            <el-table-column prop="raw.open_price" label="开盘" width="90" />
            <el-table-column prop="raw.high_price" label="最高" width="90" />
            <el-table-column prop="raw.low_price" label="最低" width="90" />
            <el-table-column prop="raw.close_price" label="收盘" width="90" />
            <el-table-column label="涨跌幅" width="100">
              <template #default="scope">
                <span :class="getChangeClass(scope.row.raw.change_pct)">
                  {{ scope.row.raw.change_pct ? scope.row.raw.change_pct.toFixed(2) + '%' : '-' }}
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="raw.volume" label="成交量" width="120">
              <template #default="scope">
                {{ formatVolume(scope.row.raw.volume) }}
              </template>
            </el-table-column>
            <el-table-column prop="raw.open_interest" label="持仓量" width="120">
              <template #default="scope">
                {{ formatVolume(scope.row.raw.open_interest) }}
              </template>
            </el-table-column>
            <el-table-column label="成交额(万)" width="120">
              <template #default="scope">
                {{ (scope.row.raw.turnover / 10000).toFixed(2) }}
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-collapse-transition>
    </el-card>
  </div>
</template>

<script>
import { markRaw } from 'vue'
import * as echarts from 'echarts'
import request from '@/utils/request'
import { getContractsListApi, getHistoryDataApi } from '@/api'

export default {
  name: 'FuturesChart',
  data() {
    return {
      contractsList: [],
      selectedContract: '',
      selectedContractName: '',
      dateRange: [],
      historyData: [],
      loading: false,
      showTable: false,
      chart: null
    }
  },

  computed: {
    chartTitle() {
      if (this.selectedContractName) {
        return `${this.selectedContractName} K线走势图`
      }
      return '期货K线走势图'
    }
  },

  async mounted() {
    await this.loadContractsList()
    this.initDateRange()
    
    // 监听窗口大小变化
    window.addEventListener('resize', this.handleResize)
  },

  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize)
    if (this.chart) {
      this.chart.dispose()
    }
  },

  methods: {
    // 初始化日期范围（默认近60天）
    initDateRange() {
      this.setDateRange(60)
    },

    // 设置日期范围
    setDateRange(days) {
      const end = new Date()
      const start = new Date()
      start.setDate(start.getDate() - days)
      
      this.dateRange = [
        start.toISOString().split('T')[0],
        end.toISOString().split('T')[0]
      ]
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
      this.historyData = []
      // 销毁图表实例，避免状态残留
      if (this.chart) {
        this.chart.dispose()
        this.chart = null
      }
    },

    // 查询数据
    async queryData() {
      if (!this.selectedContract) {
        this.$message.warning('请先选择期货品种')
        return
      }

      if (!this.dateRange || this.dateRange.length !== 2) {
        this.$message.warning('请选择日期范围')
        return
      }

      this.loading = true
      try {
        const params = new URLSearchParams({
          symbol: this.selectedContract,
          start_date: this.dateRange[0],
          end_date: this.dateRange[1]
        })

        const response = await request.get(`${getHistoryDataApi}?${params}`)
        
        if (response.code === 0) {
          // 按日期正序排列（从旧到新）
          this.historyData = (response.data.data || []).reverse()
          this.$message.success(`查询成功，获取到 ${this.historyData.length} 条数据`)
          
          // 渲染图表
          this.$nextTick(() => {
            this.renderChart()
          })
        } else {
          this.$message.error(`查询失败: ${response.message}`)
        }
      } catch (error) {
        console.error('查询数据失败:', error)
        this.$message.error(`查询失败: ${error.message}`)
      } finally {
        this.loading = false
      }
    },

    // 渲染图表
    renderChart() {
      if (!this.historyData.length) return

      const container = this.$refs.chartContainer
      if (!container) return

      // 销毁旧的图表实例并重新创建，避免多grid时的dataZoom交互bug
      if (this.chart) {
        this.chart.dispose()
        this.chart = null
      }
      // 使用 markRaw 将 ECharts 实例标记为非响应式，避免 Vue Proxy 干扰导致 dataZoom 报错
      this.chart = markRaw(echarts.init(container))

      // 准备数据
      const dates = this.historyData.map(item => item.raw.trade_date)
      const ohlc = this.historyData.map(item => [
        item.raw.open_price,
        item.raw.close_price,
        item.raw.low_price,
        item.raw.high_price
      ])
      const volumes = this.historyData.map(item => item.raw.volume)
      const openInterests = this.historyData.map(item => item.raw.open_interest)

      // 计算涨跌颜色
      const volumeColors = this.historyData.map((item, index) => {
        if (index === 0) return item.raw.close_price >= item.raw.open_price ? 1 : -1
        return item.raw.close_price >= this.historyData[index - 1].raw.close_price ? 1 : -1
      })

      const option = {
        animation: true,
        legend: {
          data: ['K线', '成交量', '持仓量'],
          top: 10,
          left: 'center',
          textStyle: {
            fontSize: 12
          }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          },
          backgroundColor: 'rgba(245, 245, 245, 0.9)',
          borderWidth: 1,
          borderColor: '#ccc',
          padding: 10,
          textStyle: {
            color: '#333'
          },
          formatter: (params) => {
            const dataIndex = params[0]?.dataIndex
            if (dataIndex === undefined) return ''
            
            const item = this.historyData[dataIndex]
            const raw = item.raw
            const changeColor = raw.change_pct >= 0 ? '#ff3d3b' : '#43bc7c'
            
            return `
              <div style="font-weight: bold; margin-bottom: 8px;">${raw.trade_date}</div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span>开盘：</span><span style="font-weight: bold;">${raw.open_price}</span>
              </div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span>收盘：</span><span style="font-weight: bold;">${raw.close_price}</span>
              </div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span>最高：</span><span style="font-weight: bold;">${raw.high_price}</span>
              </div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span>最低：</span><span style="font-weight: bold;">${raw.low_price}</span>
              </div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span>涨跌幅：</span><span style="font-weight: bold; color: ${changeColor};">${raw.change_pct ? raw.change_pct.toFixed(2) + '%' : '-'}</span>
              </div>
              <div style="display: flex; justify-content: space-between; margin-bottom: 4px;">
                <span>成交量：</span><span style="font-weight: bold;">${this.formatVolume(raw.volume)}</span>
              </div>
              <div style="display: flex; justify-content: space-between;">
                <span>持仓量：</span><span style="font-weight: bold;">${this.formatVolume(raw.open_interest)}</span>
              </div>
            `
          }
        },
        axisPointer: {
          link: [{ xAxisIndex: 'all' }],
          label: {
            backgroundColor: '#777'
          }
        },
        toolbox: {
          feature: {
            dataZoom: {
              xAxisIndex: [0, 1, 2],
              yAxisIndex: 'none'
            },
            restore: {},
            saveAsImage: {}
          },
          right: 20,
          top: 5
        },
        grid: [
          {
            left: '8%',
            right: '8%',
            top: '10%',
            height: '45%'
          },
          {
            left: '8%',
            right: '8%',
            top: '60%',
            height: '13%'
          },
          {
            left: '8%',
            right: '8%',
            top: '76%',
            height: '13%'
          }
        ],
        xAxis: [
          {
            type: 'category',
            gridIndex: 0,
            data: dates,
            boundaryGap: true,
            axisLine: { onZero: false },
            splitLine: { show: false },
            axisLabel: {
              rotate: 45,
              fontSize: 10
            },
            min: 'dataMin',
            max: 'dataMax',
            axisPointer: {
              z: 100
            }
          },
          {
            type: 'category',
            gridIndex: 1,
            data: dates,
            boundaryGap: true,
            axisLine: { onZero: false },
            axisTick: { show: false },
            splitLine: { show: false },
            axisLabel: { show: false },
            min: 'dataMin',
            max: 'dataMax'
          },
          {
            type: 'category',
            gridIndex: 2,
            data: dates,
            boundaryGap: true,
            axisLine: { onZero: false },
            axisTick: { show: false },
            splitLine: { show: false },
            axisLabel: { show: false },
            min: 'dataMin',
            max: 'dataMax'
          }
        ],
        yAxis: [
          {
            scale: true,
            gridIndex: 0,
            splitArea: {
              show: true
            },
            axisLabel: {
              fontSize: 10
            }
          },
          {
            scale: true,
            gridIndex: 1,
            splitNumber: 2,
            axisLabel: {
              show: true,
              fontSize: 9,
              formatter: (value) => this.formatAxisVolume(value)
            },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { show: false }
          },
          {
            scale: true,
            gridIndex: 2,
            splitNumber: 2,
            axisLabel: {
              show: true,
              fontSize: 9,
              formatter: (value) => this.formatAxisVolume(value)
            },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { show: false }
          }
        ],
        dataZoom: [
          {
            type: 'inside',
            xAxisIndex: [0, 1, 2],
            start: 0,
            end: 100
          },
          {
            show: true,
            xAxisIndex: [0, 1, 2],
            type: 'slider',
            top: '93%',
            start: 0,
            end: 100,
            height: 20
          }
        ],
        series: [
          {
            name: 'K线',
            type: 'candlestick',
            xAxisIndex: 0,
            yAxisIndex: 0,
            data: ohlc,
            itemStyle: {
              color: '#ff3d3b',
              color0: '#43bc7c',
              borderColor: '#ff3d3b',
              borderColor0: '#43bc7c'
            }
          },
          {
            name: '成交量',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: volumes.map((v, i) => ({
              value: v,
              itemStyle: {
                color: volumeColors[i] > 0 ? 'rgba(255, 61, 59, 0.7)' : 'rgba(67, 188, 124, 0.7)'
              }
            }))
          },
          {
            name: '持仓量',
            type: 'bar',
            xAxisIndex: 2,
            yAxisIndex: 2,
            data: openInterests,
            itemStyle: {
              color: 'rgba(65, 105, 225, 0.7)'
            }
          }
        ]
      }

      // 使用 notMerge: true 确保完整替换配置，避免多grid交互问题
      this.chart.setOption(option, { notMerge: true })
    },

    // 处理窗口大小变化
    handleResize() {
      if (this.chart) {
        this.chart.resize()
      }
    },

    // 格式化成交量
    formatVolume(volume) {
      if (!volume) return '0'
      if (volume >= 100000000) {
        return (volume / 100000000).toFixed(2) + '亿'
      } else if (volume >= 10000) {
        return (volume / 10000).toFixed(2) + '万'
      }
      return volume.toString()
    },

    // 格式化Y轴成交量
    formatAxisVolume(value) {
      if (value >= 100000000) {
        return (value / 100000000).toFixed(1) + '亿'
      } else if (value >= 10000) {
        return (value / 10000).toFixed(0) + '万'
      }
      return value
    },

    // 获取涨跌幅样式类
    getChangeClass(changePct) {
      if (!changePct) return ''
      return changePct >= 0 ? 'price-up' : 'price-down'
    }
  }
}
</script>

<style scoped>
.futures-chart {
  padding: 0;
}

.control-card,
.chart-card,
.table-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.data-count {
  font-size: 14px;
  font-weight: normal;
  color: #909399;
}

.chart-container {
  width: 100%;
  height: 600px;
}

.price-up {
  color: #ff3d3b;
  font-weight: bold;
}

.price-down {
  color: #43bc7c;
  font-weight: bold;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .chart-container {
    height: 500px;
  }
}

@media (max-width: 768px) {
  .chart-container {
    height: 400px;
  }
  
  .control-card .el-col {
    margin-bottom: 15px;
  }
}
</style>

