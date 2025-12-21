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
          <div class="header-left">
            <span>{{ chartTitle }}</span>
            <span v-if="historyData.length" class="data-count">
              （共 {{ historyData.length }} 条数据）
            </span>
          </div>
          <div class="header-right" v-if="selectedContract">
            <!-- 事件开关 - 控制K线图上的事件标记显示 -->
            <el-switch
              v-model="showEvents"
              active-text="显示事件标记"
              inactive-text=""
              @change="onShowEventsChange"
              style="margin-right: 16px;"
            />
            <el-button 
              type="primary" 
              size="small" 
              icon="List"
              @click="openEventsDrawer"
            >
              管理事件
            </el-button>
          </div>
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

    <!-- 事件管理抽屉 -->
    <el-drawer
      v-model="eventsDrawerVisible"
      title="事件管理"
      direction="rtl"
      size="550px"
    >
      <div class="events-drawer-content">
        <div class="events-drawer-header">
          <el-button 
            type="primary" 
            icon="Plus"
            @click="openEventDialog()"
          >
            添加事件
          </el-button>
          <el-button 
            icon="Refresh"
            @click="loadEvents"
            :loading="eventsLoading"
          >
            刷新
          </el-button>
        </div>

        <el-table
          :data="eventsData"
          stripe
          style="width: 100%"
          v-loading="eventsLoading"
        >
          <el-table-column prop="event_date" label="日期" width="100" />
          <el-table-column prop="title" label="标题" min-width="120" show-overflow-tooltip />
          <el-table-column label="方向" width="70">
            <template #default="scope">
              <el-tag 
                :type="getOutlookTagType(scope.row.outlook)"
                size="small"
              >
                {{ getOutlookLabel(scope.row.outlook) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="100" fixed="right">
            <template #default="scope">
              <el-button 
                type="primary" 
                size="small" 
                text
                @click="openEventDialog(scope.row)"
              >
                编辑
              </el-button>
              <el-popconfirm
                title="确定要删除这条事件吗？"
                confirm-button-text="确定"
                cancel-button-text="取消"
                @confirm="deleteEvent(scope.row.id)"
              >
                <template #reference>
                  <el-button type="danger" size="small" text>删除</el-button>
                </template>
              </el-popconfirm>
            </template>
          </el-table-column>
        </el-table>

        <el-empty 
          v-if="eventsData.length === 0 && !eventsLoading"
          description="暂无事件记录"
        />
      </div>
    </el-drawer>

    <!-- 事件详情表格 -->
    <el-card class="events-table-card" v-if="showEvents && eventsData.length > 0">
      <template #header>
        <div class="card-header">
          <div class="header-left">
            <span>事件详情</span>
            <span class="data-count">（共 {{ eventsData.length }} 条事件）</span>
          </div>
          <el-button 
            type="primary" 
            size="small" 
            icon="Plus"
            @click="openEventDialog()"
          >
            添加事件
          </el-button>
        </div>
      </template>

      <el-table
        :data="eventsData"
        stripe
        border
        style="width: 100%"
        max-height="500"
        row-key="id"
      >
        <el-table-column prop="event_date" label="日期" width="110" sortable />
        <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
        <el-table-column label="方向" width="90" align="center">
          <template #default="scope">
            <el-tag 
              :type="getOutlookTagType(scope.row.outlook)"
              size="small"
              effect="dark"
            >
              {{ getOutlookLabel(scope.row.outlook) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="强度" width="80" align="center">
          <template #default="scope">
            <span class="strength-value">{{ scope.row.strength || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="内容" min-width="300">
          <template #default="scope">
            <div class="event-content-cell">
              {{ scope.row.content || '-' }}
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right" align="center">
          <template #default="scope">
            <el-button 
              type="primary" 
              size="small" 
              text
              @click="openEventDialog(scope.row)"
            >
              编辑
            </el-button>
            <el-popconfirm
              title="确定要删除这条事件吗？"
              confirm-button-text="确定"
              cancel-button-text="取消"
              @confirm="deleteEvent(scope.row.id)"
            >
              <template #reference>
                <el-button type="danger" size="small" text>删除</el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 事件编辑弹窗 -->
    <el-dialog
      v-model="eventDialogVisible"
      :title="eventForm.id ? '编辑事件' : '添加事件'"
      width="600px"
      destroy-on-close
    >
      <el-form 
        ref="eventFormRef"
        :model="eventForm" 
        :rules="eventFormRules"
        label-width="100px"
      >
        <el-form-item label="品种" prop="symbol">
          <el-input :value="selectedContractName + ' (' + selectedContract + ')'" disabled />
        </el-form-item>

        <el-form-item label="事件日期" prop="event_date">
          <el-date-picker
            v-model="eventForm.event_date"
            type="date"
            placeholder="选择日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
          />
        </el-form-item>

        <el-form-item label="标题" prop="title">
          <el-input 
            v-model="eventForm.title" 
            placeholder="如：美联储降息25个基点"
            maxlength="200"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="内容" prop="content">
          <el-input
            v-model="eventForm.content"
            type="textarea"
            :rows="4"
            placeholder="详细描述事件内容..."
          />
        </el-form-item>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="方向判断" prop="outlook">
              <el-select v-model="eventForm.outlook" placeholder="选择方向" clearable style="width: 100%">
                <el-option label="看多 (Bullish)" value="bullish">
                  <span style="color: #ef5350; display: flex; align-items: center; gap: 8px;">
                    <span style="display: inline-block; width: 8px; height: 8px; background: #ef5350; border-radius: 2px;"></span>
                    看多 (Bullish)
                  </span>
                </el-option>
                <el-option label="看空 (Bearish)" value="bearish">
                  <span style="color: #26a69a; display: flex; align-items: center; gap: 8px;">
                    <span style="display: inline-block; width: 8px; height: 8px; background: #26a69a; border-radius: 2px;"></span>
                    看空 (Bearish)
                  </span>
                </el-option>
                <el-option label="震荡 (Ranging)" value="ranging">
                  <span style="color: #ff9800; display: flex; align-items: center; gap: 8px;">
                    <span style="display: inline-block; width: 8px; height: 8px; background: #ff9800; border-radius: 2px; transform: rotate(45deg);"></span>
                    震荡 (Ranging)
                  </span>
                </el-option>
                <el-option label="不确定 (Uncertain)" value="uncertain">
                  <span style="color: #78909c; display: flex; align-items: center; gap: 8px;">
                    <span style="display: inline-block; width: 8px; height: 8px; background: #78909c; border-radius: 50%;"></span>
                    不确定 (Uncertain)
                  </span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="判断强度" prop="strength">
              <el-slider 
                v-model="eventForm.strength" 
                :min="1" 
                :max="10" 
                :step="1"
                show-stops
                :marks="strengthMarks"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <el-button @click="eventDialogVisible = false">取消</el-button>
        <el-button 
          type="primary" 
          @click="submitEvent"
          :loading="eventSubmitting"
        >
          {{ eventForm.id ? '保存修改' : '确认添加' }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { markRaw } from 'vue'
import * as echarts from 'echarts'
import request from '@/utils/request'
import { 
  getContractsListApi, 
  getHistoryDataApi,
  getEventsListApi,
  createEventApi,
  updateEventApi,
  deleteEventApi
} from '@/api'

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
      chart: null,
      
      // 事件相关
      showEvents: true,
      eventsData: [],
      eventsLoading: false,
      eventsDrawerVisible: false,
      eventDialogVisible: false,
      eventSubmitting: false,
      eventForm: {
        id: null,
        symbol: '',
        event_date: '',
        title: '',
        content: '',
        outlook: '',
        strength: 5
      },
      eventFormRules: {
        event_date: [
          { required: true, message: '请选择事件日期', trigger: 'change' }
        ],
        title: [
          { required: true, message: '请输入事件标题', trigger: 'blur' }
        ]
      },
      strengthMarks: {
        1: '弱',
        5: '中',
        10: '强'
      }
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
      this.eventsData = []
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
          
          // 加载事件数据
          if (this.showEvents) {
            await this.loadEvents()
          }
          
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

    // 加载事件数据
    async loadEvents() {
      if (!this.selectedContract) return
      
      this.eventsLoading = true
      try {
        const params = new URLSearchParams({
          symbol: this.selectedContract
        })
        
        if (this.dateRange && this.dateRange.length === 2) {
          params.append('start_date', this.dateRange[0])
          params.append('end_date', this.dateRange[1])
        }
        
        const response = await request.get(`${getEventsListApi}?${params}`)
        
        if (response.code === 0) {
          this.eventsData = response.data.events || []
        }
      } catch (error) {
        console.error('加载事件失败:', error)
      } finally {
        this.eventsLoading = false
      }
    },

    // 事件显示开关变化 - 控制K线图上的事件标记
    onShowEventsChange(val) {
      if (val && this.selectedContract && this.eventsData.length === 0) {
        this.loadEvents()
      }
      // 重新渲染图表以更新事件标记
      if (this.historyData.length > 0) {
        this.$nextTick(() => {
          this.renderChart()
        })
      }
    },

    // 打开事件管理抽屉
    openEventsDrawer() {
      if (!this.selectedContract) {
        this.$message.warning('请先选择期货品种')
        return
      }
      // 加载事件数据
      if (this.eventsData.length === 0) {
        this.loadEvents()
      }
      this.eventsDrawerVisible = true
    },

    // 打开事件编辑弹窗
    openEventDialog(event = null) {
      if (!this.selectedContract) {
        this.$message.warning('请先选择期货品种')
        return
      }
      
      if (event) {
        // 编辑模式
        this.eventForm = {
          id: event.id,
          symbol: event.symbol,
          event_date: event.event_date,
          title: event.title,
          content: event.content || '',
          outlook: event.outlook || '',
          strength: event.strength || 5
        }
      } else {
        // 新增模式，默认日期为今天
        const today = new Date().toISOString().split('T')[0]
        this.eventForm = {
          id: null,
          symbol: this.selectedContract,
          event_date: today,
          title: '',
          content: '',
          outlook: '',
          strength: 5
        }
      }
      
      this.eventDialogVisible = true
    },

    // 提交事件
    async submitEvent() {
      const formRef = this.$refs.eventFormRef
      if (!formRef) return
      
      const valid = await formRef.validate().catch(() => false)
      if (!valid) return
      
      this.eventSubmitting = true
      try {
        const data = {
          symbol: this.selectedContract,
          event_date: this.eventForm.event_date,
          title: this.eventForm.title,
          content: this.eventForm.content,
          outlook: this.eventForm.outlook || null,
          strength: this.eventForm.strength
        }
        
        let response
        if (this.eventForm.id) {
          // 更新
          response = await request.put(`${updateEventApi}/${this.eventForm.id}`, data)
        } else {
          // 创建
          response = await request.post(createEventApi, data)
        }
        
        if (response.code === 0) {
          this.$message.success(this.eventForm.id ? '更新成功' : '添加成功')
          this.eventDialogVisible = false
          // 刷新事件列表和图表
          await this.loadEvents()
          this.$nextTick(() => {
            this.renderChart()
          })
        } else {
          this.$message.error(response.message)
        }
      } catch (error) {
        console.error('提交事件失败:', error)
        this.$message.error('提交失败: ' + error.message)
      } finally {
        this.eventSubmitting = false
      }
    },

    // 删除事件
    async deleteEvent(eventId) {
      try {
        const response = await request.delete(`${deleteEventApi}/${eventId}`)
        
        if (response.code === 0) {
          this.$message.success('删除成功')
          // 刷新事件列表和图表
          await this.loadEvents()
          this.$nextTick(() => {
            this.renderChart()
          })
        } else {
          this.$message.error(response.message)
        }
      } catch (error) {
        console.error('删除事件失败:', error)
        this.$message.error('删除失败: ' + error.message)
      }
    },

    // 获取方向标签类型 - 亚洲风格：红涨绿跌
    getOutlookTagType(outlook) {
      const types = {
        'bullish': 'danger',    // 看多用红色
        'bearish': 'success',   // 看空用绿色
        'ranging': 'warning',   // 震荡用橙色
        'uncertain': 'info'     // 不确定用灰色
      }
      return types[outlook] || 'info'
    },

    // 获取方向标签文本
    getOutlookLabel(outlook) {
      const labels = {
        'bullish': '看多',
        'bearish': '看空',
        'ranging': '震荡',
        'uncertain': '不确定'
      }
      return labels[outlook] || '-'
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

      // 准备事件标记线 - TradingView风格优化
      const markLines = []
      const markPoints = []
      
      if (this.showEvents && this.eventsData.length > 0) {
        this.eventsData.forEach(event => {
          // 找到事件日期在数据中的位置
          const dateIndex = dates.indexOf(event.event_date)
          if (dateIndex !== -1) {
            const item = this.historyData[dateIndex]
            const color = this.getOutlookColor(event.outlook)
            const colorLight = this.getOutlookColorLight(event.outlook)
            
            // 添加标记线 - 使用细微的渐变虚线
            markLines.push({
              xAxis: event.event_date,
              label: {
                show: false // 标签移到markPoint显示
              },
              lineStyle: {
                color: colorLight,
                type: [4, 4], // 短虚线
                width: 1,
                opacity: 0.6
              }
            })
            
            // 根据方向判断圆点位置和颜色
            // 看空(bearish)：K线上方（头顶向下按）
            // 看多(bullish)、震荡(ranging)、不确定(uncertain)：K线下方（脚下向上推）
            const isBearish = event.outlook === 'bearish'
            const pricePosition = isBearish ? item.raw.high_price : item.raw.low_price
            const symbolOffset = isBearish ? [0, -12] : [0, 12] // 上方向上偏移，下方向下偏移
            const labelPosition = isBearish ? 'top' : 'bottom'
            
            // 圆点大小：基础10 + 强度影响（1-10对应0-5的增量）
            const baseSize = 10
            const strengthBonus = ((event.strength || 5) - 1) * 0.5
            const symbolSize = baseSize + strengthBonus
            
            markPoints.push({
              name: event.title,
              coord: [event.event_date, pricePosition],
              symbol: 'circle',
              symbolSize: symbolSize,
              symbolOffset: symbolOffset,
              itemStyle: {
                color: color,
                shadowColor: colorLight,
                shadowBlur: 6,
                shadowOffsetY: isBearish ? -2 : 2,
                borderColor: 'rgba(255, 255, 255, 0.8)',
                borderWidth: 1.5
              },
              label: {
                show: true,
                position: labelPosition,
                distance: 6,
                formatter: event.title.length > 6 ? event.title.substring(0, 6) + '..' : event.title,
                fontSize: 10,
                fontWeight: 500,
                color: color,
                backgroundColor: 'rgba(255, 255, 255, 0.9)',
                padding: [2, 4],
                borderRadius: 2,
                shadowColor: 'rgba(0, 0, 0, 0.1)',
                shadowBlur: 2
              },
              emphasis: {
                label: {
                  show: true,
                  fontSize: 11,
                  fontWeight: 'bold'
                },
                itemStyle: {
                  shadowBlur: 10,
                  shadowColor: color
                }
              }
            })
          }
        })
      }

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
            type: 'cross',
            crossStyle: {
              color: '#758696'
            },
            lineStyle: {
              color: '#758696',
              type: 'dashed'
            }
          },
          backgroundColor: 'rgba(30, 39, 46, 0.95)',
          borderWidth: 1,
          borderColor: 'rgba(255, 255, 255, 0.1)',
          padding: 12,
          textStyle: {
            color: '#e0e0e0'
          },
          extraCssText: 'box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3); border-radius: 6px;',
          formatter: (params) => {
            const dataIndex = params[0]?.dataIndex
            if (dataIndex === undefined) return ''
            
            const item = this.historyData[dataIndex]
            const raw = item.raw
            // 亚洲风格：红涨绿跌
            const changeColor = raw.change_pct >= 0 ? '#ef5350' : '#26a69a'
            const changeSign = raw.change_pct >= 0 ? '+' : ''
            
            // 查找当天的事件
            const dayEvents = this.eventsData.filter(e => e.event_date === raw.trade_date)
            let eventHtml = ''
            if (dayEvents.length > 0 && this.showEvents) {
              eventHtml = `
                <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);">
                  ${dayEvents.map(e => {
                    const color = this.getOutlookColor(e.outlook)
                    return `
                    <div style="
                      margin-top: 6px; 
                      padding: 6px 10px; 
                      background: linear-gradient(135deg, ${this.getOutlookColorLight(e.outlook)}, transparent);
                      border-left: 3px solid ${color};
                      border-radius: 0 4px 4px 0;
                    ">
                      <div style="display: flex; align-items: center; gap: 6px;">
                        <span style="
                          display: inline-flex;
                          align-items: center;
                          justify-content: center;
                          width: 16px;
                          height: 16px;
                          background: ${color};
                          color: white;
                          border-radius: 50%;
                          font-size: 9px;
                          font-weight: bold;
                        ">${this.getOutlookIcon(e.outlook)}</span>
                        <span style="font-weight: 600; color: #e0e0e0; font-size: 12px;">${e.title}</span>
                      </div>
                    </div>
                  `}).join('')}
                </div>
              `
            }
            
            // TradingView风格的深色tooltip
            return `
              <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
                <div style="
                  font-weight: 600; 
                  font-size: 13px; 
                  color: #fff; 
                  margin-bottom: 10px;
                  padding-bottom: 8px;
                  border-bottom: 1px solid rgba(255,255,255,0.1);
                ">${raw.trade_date}</div>
                
                <div style="display: grid; grid-template-columns: auto 1fr; gap: 4px 16px; font-size: 12px;">
                  <span style="color: #9e9e9e;">开</span>
                  <span style="color: #e0e0e0; text-align: right; font-weight: 500;">${raw.open_price}</span>
                  
                  <span style="color: #9e9e9e;">高</span>
                  <span style="color: #ef5350; text-align: right; font-weight: 500;">${raw.high_price}</span>
                  
                  <span style="color: #9e9e9e;">低</span>
                  <span style="color: #26a69a; text-align: right; font-weight: 500;">${raw.low_price}</span>
                  
                  <span style="color: #9e9e9e;">收</span>
                  <span style="color: #e0e0e0; text-align: right; font-weight: 500;">${raw.close_price}</span>
                  
                  <span style="color: #9e9e9e;">涨跌</span>
                  <span style="color: ${changeColor}; text-align: right; font-weight: 600;">${raw.change_pct ? changeSign + raw.change_pct.toFixed(2) + '%' : '-'}</span>
                  
                  <span style="color: #9e9e9e;">成交量</span>
                  <span style="color: #e0e0e0; text-align: right; font-weight: 500;">${this.formatVolume(raw.volume)}</span>
                  
                  <span style="color: #9e9e9e;">持仓量</span>
                  <span style="color: #e0e0e0; text-align: right; font-weight: 500;">${this.formatVolume(raw.open_interest)}</span>
                </div>
                ${eventHtml}
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
              // 亚洲风格：红涨绿跌
              color: '#ef5350',      // 涨 - 红色填充
              color0: '#26a69a',     // 跌 - 绿色填充
              borderColor: '#ef5350',
              borderColor0: '#26a69a',
              borderWidth: 1
            },
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowColor: 'rgba(0, 0, 0, 0.3)'
              }
            },
            markLine: markLines.length > 0 ? {
              symbol: ['none', 'none'],
              animation: true,
              data: markLines
            } : undefined,
            markPoint: markPoints.length > 0 ? {
              animation: true,
              animationDuration: 300,
              data: markPoints
            } : undefined
          },
          {
            name: '成交量',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: volumes.map((v, i) => ({
              value: v,
              itemStyle: {
                // 亚洲风格成交量颜色：红涨绿跌
                color: volumeColors[i] > 0 ? 'rgba(239, 83, 80, 0.6)' : 'rgba(38, 166, 154, 0.6)'
              }
            })),
            emphasis: {
              disabled: true
            }
          },
          {
            name: '持仓量',
            type: 'bar',
            xAxisIndex: 2,
            yAxisIndex: 2,
            data: openInterests,
            itemStyle: {
              color: 'rgba(66, 165, 245, 0.6)'
            },
            emphasis: {
              disabled: true
            }
          }
        ]
      }

      // 使用 notMerge: true 确保完整替换配置，避免多grid交互问题
      this.chart.setOption(option, { notMerge: true })
    },

    // 获取方向对应的颜色 - 亚洲风格：红涨绿跌
    getOutlookColor(outlook) {
      const colors = {
        'bullish': '#ef5350',   // 红色（看多）
        'bearish': '#26a69a',   // 绿色（看空）
        'ranging': '#ff9800',   // 橙色（震荡）
        'uncertain': '#78909c'  // 灰蓝色（不确定）
      }
      return colors[outlook] || '#2196f3'
    },
    
    // 获取方向对应的浅色（用于阴影和渐变）
    getOutlookColorLight(outlook) {
      const colors = {
        'bullish': 'rgba(239, 83, 80, 0.3)',
        'bearish': 'rgba(38, 166, 154, 0.3)',
        'ranging': 'rgba(255, 152, 0, 0.3)',
        'uncertain': 'rgba(120, 144, 156, 0.3)'
      }
      return colors[outlook] || 'rgba(33, 150, 243, 0.3)'
    },

    // 获取方向对应的图标
    getOutlookIcon(outlook) {
      const icons = {
        'bullish': '▲',
        'bearish': '▼',
        'ranging': '◆',
        'uncertain': '●'
      }
      return icons[outlook] || '◉'
    },

    // 获取旗帜形状的SVG路径 - TradingView风格
    getFlagPath(outlook) {
      // 根据方向返回不同的旗帜形状
      if (outlook === 'bullish') {
        // 向上的旗帜
        return 'path://M0,20 L0,0 L12,4 L0,8 Z'
      } else if (outlook === 'bearish') {
        // 向下的旗帜
        return 'path://M0,0 L0,20 L12,16 L0,12 Z'
      } else if (outlook === 'ranging') {
        // 菱形标记
        return 'path://M8,0 L16,8 L8,16 L0,8 Z'
      } else {
        // 圆形标记
        return 'circle'
      }
    },

    // 获取方向对应的符号（保留兼容）
    getOutlookSymbol(outlook) {
      return this.getFlagPath(outlook)
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

  }
}
</script>

<style scoped>
.futures-chart {
  padding: 0;
}

.control-card,
.chart-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
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

.strength-value {
  font-weight: bold;
  color: #409eff;
}

.text-muted {
  color: #909399;
}

.events-drawer-content {
  padding: 0 10px;
}

.events-drawer-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.events-table-card {
  margin-bottom: 20px;
}

.event-content-cell {
  line-height: 1.6;
  color: #606266;
  white-space: pre-wrap;
  word-break: break-word;
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
  
  .header-right {
    flex-wrap: wrap;
    gap: 8px;
  }
}
</style>
