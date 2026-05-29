<template>
  <div class="return-panel">
    <div class="return-header">
      <div class="return-tabs">
        <button
          v-for="tab in returnTabs"
          :key="tab.value"
          type="button"
          class="return-tab"
          :class="{ active: returnTab === tab.value }"
          @click="returnTab = tab.value"
        >
          {{ tab.label }}
        </button>
      </div>
      <label class="rate-toggle">
        <input v-model="showReturnRate" type="checkbox" class="rate-checkbox" />
        <span>收益率</span>
      </label>
    </div>

    <div class="return-toolbar">
      <div class="view-group">
        <button
          type="button"
          class="view-btn"
          :class="{ active: viewMode === 'calendar' }"
          @click="viewMode = 'calendar'"
        >
          日历图
        </button>
        <button
          type="button"
          class="view-btn"
          :class="{ active: viewMode === 'bar' }"
          @click="viewMode = 'bar'"
        >
          柱状图
        </button>
      </div>
      <div v-if="showPeriodNav" class="period-nav">
        <button type="button" class="nav-btn" @click="shiftPeriod(-1)">‹</button>
        <span class="period-label">{{ periodLabel }}</span>
        <button type="button" class="nav-btn" @click="shiftPeriod(1)">›</button>
      </div>
    </div>

    <div v-if="viewMode === 'calendar'" class="calendar-wrap">
      <div v-if="returnTab === 'day'" class="weekday-row">
        <div v-for="w in weekdays" :key="w" class="weekday-cell">{{ w }}</div>
      </div>
      <div class="calendar-grid" :class="{ 'month-grid': returnTab !== 'day' }">
        <div
          v-for="(cell, idx) in calendarCells"
          :key="idx"
          class="calendar-cell"
          :class="{
            empty: cell.isEmpty,
            today: cell.isToday,
            muted: !cell.isCurrent
          }"
          :style="cellStyle(cell)"
        >
          <template v-if="!cell.isEmpty">
            <div class="cell-date">
              <span v-if="cell.isToday" class="today-tag">今</span>
              <span v-else>{{ cell.label }}</span>
            </div>
            <div
              v-if="cell.value !== null && cell.value !== undefined"
              class="cell-value"
              :class="cell.value > 0 ? 'val-pos' : cell.value < 0 ? 'val-neg' : ''"
            >
              {{ formatValue(cell.value) }}
            </div>
          </template>
        </div>
      </div>
    </div>

    <div v-else class="bar-wrap">
      <div v-if="!barItems.length" class="bar-placeholder">暂无收益数据</div>
      <div v-else ref="barChartRef" class="bar-chart" />
    </div>

    <div class="return-footer">
      <span>{{ footerLabel }}</span>
    </div>
  </div>
</template>

<script>
import { markRaw } from 'vue'
import * as echarts from 'echarts'

const RETURN_TABS = [
  { label: '日收益', value: 'day' },
  { label: '月收益', value: 'month' },
  { label: '年收益', value: 'year' }
]

const WEEKDAYS = ['一', '二', '三', '四', '五', '六', '日']

function pad(n) {
  return String(n).padStart(2, '0')
}

function todayStr() {
  const d = new Date()
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

export default {
  name: 'DailyReturnPanel',
  props: {
    curve: {
      type: Array,
      default: () => []
    }
  },
  data() {
    const now = new Date()
    return {
      returnTab: 'day',
      showReturnRate: false,
      viewMode: 'calendar',
      returnTabs: RETURN_TABS,
      weekdays: WEEKDAYS,
      viewYear: now.getFullYear(),
      viewMonth: now.getMonth() + 1,
      barChart: null,
      resizeFrame: null,
      renderFrame: null
    }
  },
  computed: {
    sortedCurve() {
      return [...this.curve].sort((a, b) => a.record_date.localeCompare(b.record_date))
    },
    curveByDate() {
      const map = {}
      this.sortedCurve.forEach(row => {
        map[row.record_date] = row
      })
      return map
    },
    prevEquityByDate() {
      const map = {}
      this.sortedCurve.forEach((row, i) => {
        map[row.record_date] = i > 0 ? this.sortedCurve[i - 1].equity : row.equity - row.daily_pnl
      })
      return map
    },
    showPeriodNav() {
      return this.returnTab === 'day' || this.returnTab === 'month'
    },
    periodLabel() {
      if (this.returnTab === 'day') {
        return `${this.viewYear}年 ${this.viewMonth}月`
      }
      if (this.returnTab === 'month') {
        return `${this.viewYear}年`
      }
      return ''
    },
    calendarCells() {
      if (this.returnTab === 'day') return this.buildDayCalendarCells()
      if (this.returnTab === 'month') return this.buildMonthCalendarCells()
      return this.buildYearCalendarCells()
    },
    barItems() {
      if (this.returnTab === 'day') return this.buildDayBarItems()
      if (this.returnTab === 'month') return this.buildMonthBarItems()
      return this.buildYearBarItems()
    },
    maxAbsValue() {
      const values = this.calendarCells
        .filter(c => !c.isEmpty && c.value !== null && c.value !== undefined)
        .map(c => Math.abs(c.value))
      return Math.max(...values, 1)
    },
    footerLabel() {
      const total = this.currentPeriodTotal()
      const prefix = this.footerPrefix()
      if (this.showReturnRate) {
        return `${prefix}${this.formatSigned(total, true)}`
      }
      return `${prefix}${this.formatSigned(total, false)}`
    }
  },
  watch: {
    curve: {
      deep: true,
      handler() {
        this.$nextTick(() => this.scheduleBarRender())
      }
    },
    returnTab() {
      this.$nextTick(() => this.scheduleBarRender())
    },
    viewMode() {
      this.$nextTick(() => this.scheduleBarRender())
    },
    showReturnRate() {
      this.$nextTick(() => this.scheduleBarRender())
    },
    viewYear() {
      this.$nextTick(() => this.scheduleBarRender())
    },
    viewMonth() {
      this.$nextTick(() => this.scheduleBarRender())
    },
    barItems: {
      deep: true,
      handler() {
        this.$nextTick(() => this.scheduleBarRender())
      }
    }
  },
  mounted() {
    window.addEventListener('resize', this.handleResize)
    this.$nextTick(() => this.scheduleBarRender())
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize)
    if (this.resizeFrame) cancelAnimationFrame(this.resizeFrame)
    if (this.renderFrame) cancelAnimationFrame(this.renderFrame)
    if (this.barChart) {
      this.barChart.dispose()
      this.barChart = null
    }
  },
  methods: {
    shiftPeriod(step) {
      if (this.returnTab === 'day') {
        let m = this.viewMonth + step
        let y = this.viewYear
        if (m < 1) {
          m = 12
          y -= 1
        } else if (m > 12) {
          m = 1
          y += 1
        }
        this.viewMonth = m
        this.viewYear = y
        return
      }
      if (this.returnTab === 'month') {
        this.viewYear += step
      }
    },
    getMetric(row) {
      if (!row) return null
      if (this.showReturnRate) {
        const prev = this.prevEquityByDate[row.record_date]
        if (!prev) return 0
        return (row.daily_pnl / prev) * 100
      }
      return row.daily_pnl
    },
    sumRows(rows) {
      if (this.showReturnRate) {
        if (!rows.length) return 0
        const startEquity = this.prevEquityByDate[rows[0].record_date] || rows[0].equity - rows[0].daily_pnl
        if (!startEquity) return 0
        const totalPnl = rows.reduce((s, r) => s + r.daily_pnl, 0)
        return (totalPnl / startEquity) * 100
      }
      return rows.reduce((s, r) => s + r.daily_pnl, 0)
    },
    rowsInMonth(year, month) {
      const prefix = `${year}-${pad(month)}-`
      return this.sortedCurve.filter(r => r.record_date.startsWith(prefix))
    },
    rowsInYear(year) {
      const prefix = `${year}-`
      return this.sortedCurve.filter(r => r.record_date.startsWith(prefix))
    },
    buildDayCalendarCells() {
      const year = this.viewYear
      const month = this.viewMonth
      const first = new Date(year, month - 1, 1)
      const daysInMonth = new Date(year, month, 0).getDate()
      const firstWeek = first.getDay()
      const emptyDays = firstWeek === 0 ? 6 : firstWeek - 1
      const cells = []

      for (let i = 0; i < emptyDays; i++) {
        cells.push({ isEmpty: true })
      }

      for (let day = 1; day <= daysInMonth; day++) {
        const date = `${year}-${pad(month)}-${pad(day)}`
        const row = this.curveByDate[date]
        cells.push({
          isEmpty: false,
          isCurrent: true,
          isToday: date === todayStr(),
          label: day,
          value: row ? this.getMetric(row) : null
        })
      }
      return cells
    },
    buildMonthCalendarCells() {
      const cells = []
      for (let m = 1; m <= 12; m++) {
        const rows = this.rowsInMonth(this.viewYear, m)
        cells.push({
          isEmpty: false,
          isCurrent: true,
          isToday: false,
          label: `${m}月`,
          value: rows.length ? this.sumRows(rows) : null
        })
      }
      return cells
    },
    buildYearCalendarCells() {
      const years = [...new Set(this.sortedCurve.map(r => r.record_date.slice(0, 4)))]
        .sort((a, b) => Number(a) - Number(b))
      if (!years.length) {
        return Array.from({ length: 4 }, () => ({ isEmpty: true }))
      }
      return years.map(y => {
        const rows = this.rowsInYear(Number(y))
        return {
          isEmpty: false,
          isCurrent: true,
          isToday: false,
          label: `${y}年`,
          value: rows.length ? this.sumRows(rows) : null
        }
      })
    },
    buildDayBarItems() {
      const rows = this.rowsInMonth(this.viewYear, this.viewMonth)
      return rows.map(row => ({
        label: row.record_date.slice(8),
        value: this.getMetric(row)
      }))
    },
    buildMonthBarItems() {
      return Array.from({ length: 12 }, (_, i) => {
        const m = i + 1
        const rows = this.rowsInMonth(this.viewYear, m)
        return {
          label: `${m}月`,
          value: rows.length ? this.sumRows(rows) : 0
        }
      })
    },
    buildYearBarItems() {
      const years = [...new Set(this.sortedCurve.map(r => r.record_date.slice(0, 4)))]
        .sort((a, b) => Number(a) - Number(b))
      return years.map(y => {
        const rows = this.rowsInYear(Number(y))
        return {
          label: `${y}年`,
          value: rows.length ? this.sumRows(rows) : 0
        }
      })
    },
    currentPeriodTotal() {
      if (this.returnTab === 'day') {
        return this.sumRows(this.rowsInMonth(this.viewYear, this.viewMonth))
      }
      if (this.returnTab === 'month') {
        return this.sumRows(this.rowsInYear(this.viewYear))
      }
      return this.sumRows(this.sortedCurve)
    },
    footerPrefix() {
      if (this.returnTab === 'day') return `${this.viewMonth}月累计收益: `
      if (this.returnTab === 'month') return `${this.viewYear}年累计收益: `
      return '全部累计收益: '
    },
    cellStyle(cell) {
      if (cell.isEmpty || cell.value === null || cell.value === undefined) return {}
      if (cell.value === 0) return { background: '#fafafa' }
      const ratio = Math.min(Math.abs(cell.value) / this.maxAbsValue, 1)
      if (cell.value > 0) {
        return { background: `rgba(198, 40, 40, ${0.14 + ratio * 0.34})` }
      }
      return { background: `rgba(46, 125, 50, ${0.14 + ratio * 0.34})` }
    },
    formatValue(value) {
      if (this.showReturnRate) {
        const sign = value >= 0 ? '+' : ''
        return `${sign}${value.toFixed(2)}%`
      }
      const sign = value >= 0 ? '+' : ''
      if (Math.abs(value) >= 100) return `${sign}${Math.round(value)}`
      return `${sign}${value.toFixed(2)}`
    },
    formatSigned(value, isRate) {
      const sign = value >= 0 ? '+' : ''
      if (isRate) return `${sign}${value.toFixed(2)}%`
      return `${sign}${Number(value).toFixed(2)}`
    },
    handleResize() {
      if (this.resizeFrame) cancelAnimationFrame(this.resizeFrame)
      this.resizeFrame = requestAnimationFrame(() => {
        if (this.barChart) this.barChart.resize()
        this.resizeFrame = null
      })
    },
    scheduleBarRender() {
      if (this.renderFrame) cancelAnimationFrame(this.renderFrame)
      this.renderFrame = requestAnimationFrame(() => {
        this.renderBarChart()
        this.renderFrame = null
      })
    },
    renderBarChart() {
      if (this.viewMode !== 'bar') {
        if (this.barChart) {
          this.barChart.dispose()
          this.barChart = null
        }
        return
      }
      if (!this.$refs.barChartRef || !this.barItems.length) {
        if (this.barChart) {
          this.barChart.dispose()
          this.barChart = null
        }
        return
      }
      if (!this.barChart) {
        this.barChart = markRaw(echarts.init(this.$refs.barChartRef))
      }

      const labels = this.barItems.map(i => i.label)
      const values = this.barItems.map(i => i.value)
      const colors = values.map(v => (v >= 0 ? '#c62828' : '#2e7d32'))

      this.barChart.setOption({
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'shadow' },
          formatter: params => {
            const p = params[0]
            const val = this.formatValue(p.value)
            return `${p.axisValue}<br/>${p.marker}${val}`
          }
        },
        grid: { left: 48, right: 16, top: 16, bottom: 40 },
        xAxis: {
          type: 'category',
          data: labels,
          axisLabel: { color: '#5c5c5c', fontSize: 11 },
          axisLine: { lineStyle: { color: '#e0e0e0' } },
          axisTick: { show: false }
        },
        yAxis: {
          type: 'value',
          axisLabel: {
            color: '#5c5c5c',
            fontSize: 11,
            formatter: v => (this.showReturnRate ? `${v.toFixed(1)}%` : v.toFixed(0))
          },
          splitLine: { lineStyle: { color: '#f0f0f0' } },
          axisLine: { show: false },
          axisTick: { show: false }
        },
        series: [
          {
            type: 'bar',
            data: values.map((v, i) => ({
              value: v,
              itemStyle: { color: colors[i] }
            })),
            barMaxWidth: 28
          }
        ]
      }, true)
    }
  }
}
</script>

<style scoped>
.return-panel {
  padding: 16px 18px;
  border-radius: 8px;
  background: #ffffff;
  border: 1px solid #e0e0e0;
}

.return-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 10px;
}

.return-tabs {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.return-tab {
  padding: 0 0 8px;
  border: none;
  background: transparent;
  color: #5c5c5c;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  position: relative;
}

.return-tab.active {
  color: #c62828;
  font-weight: 600;
}

.return-tab.active::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 2px;
  background: #c62828;
}

.rate-toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #5c5c5c;
  font-size: 13px;
  cursor: pointer;
  user-select: none;
  flex-shrink: 0;
}

.rate-checkbox {
  accent-color: #c62828;
}

.return-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}

.view-group {
  display: inline-flex;
  padding: 2px;
  border-radius: 6px;
  background: #f5f5f5;
  border: 1px solid #e8e8e8;
}

.view-btn {
  padding: 5px 14px;
  border: none;
  border-radius: 5px;
  background: transparent;
  color: #5c5c5c;
  font-size: 13px;
  cursor: pointer;
}

.view-btn.active {
  background: #ffffff;
  color: #1a1a1a;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.06);
}

.period-nav {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-btn {
  width: 28px;
  height: 28px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #fafafa;
  color: #5c5c5c;
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
}

.nav-btn:hover {
  border-color: #bdbdbd;
  color: #1a1a1a;
}

.period-label {
  min-width: 96px;
  text-align: center;
  color: #1a1a1a;
  font-size: 14px;
  font-weight: 600;
}

.weekday-row {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
  margin-bottom: 6px;
}

.weekday-cell {
  text-align: center;
  color: #8a8a8a;
  font-size: 12px;
  font-weight: 500;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 6px;
}

.calendar-grid.month-grid {
  grid-template-columns: repeat(4, 1fr);
}

.calendar-cell {
  min-height: 72px;
  padding: 8px 6px;
  border-radius: 6px;
  border: 1px solid #f0f0f0;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 4px;
}

.calendar-cell.empty {
  border-color: transparent;
  background: transparent;
}

.calendar-cell.muted {
  opacity: 0.55;
}

.calendar-cell.today {
  border-color: #c62828;
}

.cell-date {
  color: #1a1a1a;
  font-size: 14px;
  font-weight: 600;
  line-height: 1.2;
}

.today-tag {
  display: inline-block;
  min-width: 22px;
  padding: 0 4px;
  border-radius: 4px;
  background: #c62828;
  color: #ffffff;
  font-size: 12px;
  text-align: center;
}

.cell-value {
  font-size: 12px;
  font-weight: 600;
  line-height: 1.2;
}

.val-pos {
  color: #c62828;
}

.val-neg {
  color: #2e7d32;
}

.bar-wrap {
  min-height: 280px;
}

.bar-chart {
  width: 100%;
  height: 280px;
}

.bar-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 280px;
  color: #8a8a8a;
  font-size: 13px;
}

.return-footer {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
  color: #1a1a1a;
  font-size: 13px;
  font-weight: 600;
}

@media (max-width: 768px) {
  .calendar-cell {
    min-height: 58px;
    padding: 6px 4px;
  }

  .cell-date {
    font-size: 12px;
  }

  .cell-value {
    font-size: 11px;
  }
}
</style>
