<template>
  <div class="futures-chart">
    <!-- 控制面板 -->
    <ControlPanel
      v-model:selected-contract="selectedContract"
      v-model:date-range="dateRange"
      :contracts-list="contractsList"
      :loading="loading"
      @contract-change="onContractChange"
      @query="queryData"
      @set-date-range="setDateRange"
    />

    <!-- 事件日历视图 -->
    <EventsCalendar
      :events-data="calendarEventsData"
      :loading="calendarLoading"
      @refresh="loadCalendarEvents"
      @event-click="jumpToEvent"
    />

    <!-- 最近事件卡片 -->
    <RecentEventsCard
      :recent-events-data="recentEventsData"
      :symbol-stats="recentSymbolStats"
      :loading="recentEventsLoading"
      :days="recentEventsDays"
      @jump-to-symbol="jumpToSymbol"
      @jump-to-event="jumpToEvent"
      @set-days="setRecentDays"
      @refresh="loadRecentEvents"
    />

    <!-- 图表展示区 -->
    <ChartDisplay
      :selected-contract="selectedContract"
      :selected-contract-name="selectedContractName"
      :history-data="historyData"
      :events-data="eventsData"
      v-model:show-events="showEvents"
      :loading="loading"
      @open-events-drawer="openEventsDrawer"
    />

    <!-- 事件详情表格 -->
    <EventsTable
      :events-data="eventsData"
      :show-events="showEvents"
      @add="openEventDialog()"
      @edit="openEventDialog"
      @delete="deleteEvent"
    />

    <!-- 事件管理抽屉 -->
    <EventsDrawer
      v-model:visible="eventsDrawerVisible"
      :events-data="eventsData"
      :loading="eventsLoading"
      @add="openEventDialog()"
      @edit="openEventDialog"
      @delete="deleteEvent"
      @refresh="loadEvents"
    />

    <!-- 事件编辑弹窗 -->
    <EventDialog
      v-model:visible="eventDialogVisible"
      :event-form="eventForm"
      :selected-contract="selectedContract"
      :selected-contract-name="selectedContractName"
      :submitting="eventSubmitting"
      @submit="submitEvent"
      @cancel="eventDialogVisible = false"
    />
  </div>
</template>

<script>
import request from '@/utils/request'
import { 
  getContractsListApi, 
  getHistoryDataApi,
  getEventsListApi,
  getRecentEventsApi,
  createEventApi,
  updateEventApi,
  deleteEventApi
} from '@/api'
import ControlPanel from './ControlPanel.vue'
import EventsCalendar from './EventsCalendar.vue'
import RecentEventsCard from './RecentEventsCard.vue'
import ChartDisplay from './ChartDisplay.vue'
import EventsTable from './EventsTable.vue'
import EventsDrawer from './EventsDrawer.vue'
import EventDialog from './EventDialog.vue'

export default {
  name: 'FuturesChart',
  components: {
    ControlPanel,
    EventsCalendar,
    RecentEventsCard,
    ChartDisplay,
    EventsTable,
    EventsDrawer,
    EventDialog
  },
  data() {
    return {
      // 合约相关
      contractsList: [],
      selectedContract: '',
      selectedContractName: '',
      
      // 日期相关
      dateRange: [],
      
      // 历史数据
      historyData: [],
      loading: false,
      
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
      
      // 最近事件相关
      recentEventsData: [],
      recentEventsLoading: false,
      recentSymbolStats: {},
      recentEventsDays: 7,
      
      // 日历事件相关
      calendarEventsData: [],
      calendarLoading: false
    }
  },

  async mounted() {
    await this.loadContractsList()
    this.initDateRange()
    this.loadRecentEvents()
    this.loadCalendarEvents()
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

    // 打开事件管理抽屉
    openEventsDrawer() {
      if (!this.selectedContract) {
        this.$message.warning('请先选择期货品种')
        return
      }
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
        // 新增模式
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
    async submitEvent(formData) {
      this.eventSubmitting = true
      try {
        const data = {
          symbol: this.selectedContract,
          event_date: formData.event_date,
          title: formData.title,
          content: formData.content,
          outlook: formData.outlook || null,
          strength: formData.strength
        }
        
        let response
        if (formData.id) {
          // 更新
          response = await request.put(`${updateEventApi}/${formData.id}`, data)
        } else {
          // 创建
          response = await request.post(createEventApi, data)
        }
        
        if (response.code === 0) {
          this.$message.success(formData.id ? '更新成功' : '添加成功')
          this.eventDialogVisible = false
          // 刷新事件列表
          await this.loadEvents()
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
          // 刷新事件列表
          await this.loadEvents()
        } else {
          this.$message.error(response.message)
        }
      } catch (error) {
        console.error('删除事件失败:', error)
        this.$message.error('删除失败: ' + error.message)
      }
    },

    // 加载最近事件
    async loadRecentEvents() {
      this.recentEventsLoading = true
      try {
        const params = new URLSearchParams({
          days: this.recentEventsDays,
          limit: 100
        })
        
        const response = await request.get(`${getRecentEventsApi}?${params}`)
        
        if (response.code === 0) {
          this.recentEventsData = response.data.events || []
          this.recentSymbolStats = response.data.symbol_stats || {}
        }
      } catch (error) {
        console.error('加载最近事件失败:', error)
      } finally {
        this.recentEventsLoading = false
      }
    },

    // 设置最近事件天数并刷新
    setRecentDays(days) {
      this.recentEventsDays = days
      this.loadRecentEvents()
    },

    // 点击品种标签，快速选择品种并查询
    async jumpToSymbol(symbol) {
      this.selectedContract = symbol
      const contract = this.contractsList.find(c => c.symbol === symbol)
      this.selectedContractName = contract ? contract.name : symbol
      
      this.setDateRange(60)
      await this.queryData()
    },

    // 点击最近事件，快速跳转到对应品种
    async jumpToEvent(event) {
      this.selectedContract = event.symbol
      this.selectedContractName = event.symbol_name || event.symbol
      
      // 设置日期范围：事件日期前后30天
      const eventDate = new Date(event.event_date)
      const startDate = new Date(eventDate)
      const endDate = new Date(eventDate)
      startDate.setDate(startDate.getDate() - 30)
      endDate.setDate(endDate.getDate() + 30)
      
      // 确保结束日期不超过今天
      const today = new Date()
      if (endDate > today) {
        endDate.setTime(today.getTime())
      }
      
      this.dateRange = [
        startDate.toISOString().split('T')[0],
        endDate.toISOString().split('T')[0]
      ]
      
      await this.queryData()
      this.$message.success(`已跳转到 ${this.selectedContractName} - ${event.event_date}`)
    },

    // 加载日历事件（加载指定月份的所有品种的事件）
    async loadCalendarEvents(dateRange = null) {
      this.calendarLoading = true
      try {
        let startDate, endDate
        
        if (dateRange) {
          // 如果提供了日期范围，使用提供的日期
          startDate = dateRange.startDate
          endDate = dateRange.endDate
        } else {
          // 默认加载当前月份
          const now = new Date()
          const year = now.getFullYear()
          const month = now.getMonth()
          startDate = new Date(year, month, 1).toISOString().split('T')[0]
          endDate = new Date(year, month + 1, 0).toISOString().split('T')[0]
        }
        
        const params = new URLSearchParams({
          start_date: startDate,
          end_date: endDate,
          limit: 1000  // 获取所有事件
        })
        
        const response = await request.get(`${getRecentEventsApi}?${params}`)
        
        if (response.code === 0) {
          this.calendarEventsData = response.data.events || []
        }
      } catch (error) {
        console.error('加载日历事件失败:', error)
      } finally {
        this.calendarLoading = false
      }
    }
  }
}
</script>

<style scoped>
.futures-chart {
  padding: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .futures-chart {
    padding: 10px;
  }
}
</style>
