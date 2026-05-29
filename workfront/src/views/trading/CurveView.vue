<template>
  <div class="trading-page">
    <div class="filter-panel">
      <div class="filter-row">
        <span class="filter-label">时间</span>
        <div class="filter-group">
          <button
            v-for="opt in timeOptions"
            :key="opt.value"
            type="button"
            class="filter-btn"
            :class="{ active: timeRange === opt.value }"
            @click="timeRange = opt.value"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>
      <div class="filter-row">
        <span class="filter-label">指标</span>
        <div class="filter-group">
          <button
            v-for="opt in metricOptions"
            :key="opt.value"
            type="button"
            class="filter-btn"
            :class="{ active: metricType === opt.value }"
            @click="metricType = opt.value"
          >
            {{ opt.label }}
          </button>
        </div>
      </div>
    </div>

    <div class="chart-card">
      <div class="chart-header">
        <span class="chart-title">{{ currentMetricLabel }}</span>
        <span v-if="filteredCurve.length" class="chart-range">
          {{ filteredCurve[0].record_date }} — {{ filteredCurve[filteredCurve.length - 1].record_date }}
        </span>
      </div>
      <div v-if="loading" class="chart-placeholder">正在加载资金曲线...</div>
      <div v-else-if="!filteredCurve.length" class="chart-placeholder">暂无账户净值数据</div>
      <div v-else ref="chartRef" class="curve-chart" />
    </div>
  </div>
</template>

<script>
import { markRaw } from 'vue'
import * as echarts from 'echarts'
import request from '@/utils/request'
import { getTradingAccountCurveApi } from '@/api'

const TIME_OPTIONS = [
  { label: '本月', value: 'month' },
  { label: '最近3月', value: '3months' },
  { label: '今年', value: 'year' },
  { label: '全部', value: 'all' }
]

const METRIC_OPTIONS = [
  { label: '收益率', value: 'return' },
  { label: '盈亏金额', value: 'pnl' },
  { label: '总资产', value: 'equity' }
]

function pad(n) {
  return String(n).padStart(2, '0')
}

function formatDate(d) {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`
}

function getTimeRangeDates(range) {
  const today = new Date()
  today.setHours(0, 0, 0, 0)
  const end = formatDate(today)

  if (range === 'all') {
    return { start: null, end: null }
  }
  if (range === 'month') {
    const start = new Date(today.getFullYear(), today.getMonth(), 1)
    return { start: formatDate(start), end }
  }
  if (range === '3months') {
    const start = new Date(today)
    start.setMonth(start.getMonth() - 3)
    return { start: formatDate(start), end }
  }
  if (range === 'year') {
    const start = new Date(today.getFullYear(), 0, 1)
    return { start: formatDate(start), end }
  }
  return { start: null, end: null }
}

export default {
  name: 'TradingCurveView',
  inject: {
    refreshAccountSummary: { default: null }
  },
  data() {
    return {
      loading: false,
      curve: [],
      timeRange: 'month',
      metricType: 'equity',
      timeOptions: TIME_OPTIONS,
      metricOptions: METRIC_OPTIONS,
      chart: null,
      resizeFrame: null,
      renderFrame: null
    }
  },
  computed: {
    filteredCurve() {
      if (!this.curve.length) return []
      const { start, end } = getTimeRangeDates(this.timeRange)
      return this.curve.filter(row => {
        if (start && row.record_date < start) return false
        if (end && row.record_date > end) return false
        return true
      })
    },
    currentMetricLabel() {
      return METRIC_OPTIONS.find(o => o.value === this.metricType)?.label || ''
    },
    chartSeries() {
      const data = this.filteredCurve
      if (!data.length) return { dates: [], values: [], yAxisName: '', tooltipFormatter: null }

      const dates = data.map(r => r.record_date)
      const baseEquity = data[0].equity

      if (this.metricType === 'equity') {
        return {
          dates,
          values: data.map(r => r.equity),
          yAxisName: '总资产（元）',
          tooltipFormatter: v => `${Number(v).toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} 元`
        }
      }
      if (this.metricType === 'pnl') {
        return {
          dates,
          values: data.map(r => r.equity - baseEquity),
          yAxisName: '盈亏金额（元）',
          tooltipFormatter: v => {
            const num = Number(v)
            const sign = num >= 0 ? '+' : ''
            return `${sign}${num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })} 元`
          }
        }
      }
      // return rate
      return {
        dates,
        values: data.map(r => ((r.equity - baseEquity) / baseEquity) * 100),
        yAxisName: '收益率（%）',
        tooltipFormatter: v => {
          const num = Number(v)
          const sign = num >= 0 ? '+' : ''
          return `${sign}${num.toFixed(2)}%`
        }
      }
    }
  },
  watch: {
    filteredCurve: {
      deep: true,
      handler() {
        this.$nextTick(() => this.scheduleRender())
      }
    },
    metricType() {
      this.$nextTick(() => this.scheduleRender())
    }
  },
  mounted() {
    this.fetchCurve()
    window.addEventListener('resize', this.handleResize)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize)
    if (this.resizeFrame) cancelAnimationFrame(this.resizeFrame)
    if (this.renderFrame) cancelAnimationFrame(this.renderFrame)
    if (this.chart) {
      this.chart.dispose()
      this.chart = null
    }
  },
  methods: {
    handleResize() {
      if (this.resizeFrame) cancelAnimationFrame(this.resizeFrame)
      this.resizeFrame = requestAnimationFrame(() => {
        if (this.chart) this.chart.resize()
        this.resizeFrame = null
      })
    },
    scheduleRender() {
      if (this.renderFrame) cancelAnimationFrame(this.renderFrame)
      this.renderFrame = requestAnimationFrame(() => {
        this.renderChart()
        this.renderFrame = null
      })
    },
    async fetchCurve() {
      this.loading = true
      try {
        const res = await request.get(getTradingAccountCurveApi)
        if (res.code === 0) {
          this.curve = res.data?.curve || []
        }
        if (this.refreshAccountSummary) {
          this.refreshAccountSummary()
        }
      } catch (error) {
        console.error('获取资金曲线失败', error)
      } finally {
        this.loading = false
      }
    },
    lineColor() {
      if (this.metricType === 'equity') return '#424242'
      const last = this.chartSeries.values[this.chartSeries.values.length - 1]
      if (last >= 0) return '#c62828'
      return '#2e7d32'
    },
    renderChart() {
      if (!this.$refs.chartRef || !this.filteredCurve.length) {
        if (this.chart) {
          this.chart.dispose()
          this.chart = null
        }
        return
      }
      if (!this.chart) {
        this.chart = markRaw(echarts.init(this.$refs.chartRef))
      }

      const { dates, values, yAxisName, tooltipFormatter } = this.chartSeries
      const color = this.lineColor()
      const showArea = this.metricType === 'equity'

      this.chart.setOption({
        color: [color],
        tooltip: {
          trigger: 'axis',
          formatter(params) {
            const p = params[0]
            const val = tooltipFormatter(p.value)
            return `${p.axisValue}<br/>${p.marker}${p.seriesName}：${val}`
          }
        },
        grid: { left: 64, right: 24, top: 16, bottom: 40 },
        xAxis: {
          type: 'category',
          data: dates,
          boundaryGap: false,
          axisLabel: { color: '#5c5c5c', fontSize: 11 },
          axisLine: { lineStyle: { color: '#e0e0e0' } },
          axisTick: { show: false }
        },
        yAxis: {
          type: 'value',
          name: yAxisName,
          scale: this.metricType === 'equity',
          nameTextStyle: { color: '#8a8a8a', fontSize: 11 },
          axisLabel: {
            color: '#5c5c5c',
            fontSize: 11,
            formatter: v => {
              if (this.metricType === 'return') return `${v.toFixed(1)}%`
              if (Math.abs(v) >= 10000) return `${(v / 10000).toFixed(1)}万`
              return v.toFixed(0)
            }
          },
          splitLine: { lineStyle: { color: '#f0f0f0' } },
          axisLine: { show: false },
          axisTick: { show: false }
        },
        series: [
          {
            name: this.currentMetricLabel,
            type: 'line',
            symbol: 'circle',
            symbolSize: 7,
            showSymbol: dates.length <= 31,
            data: values,
            lineStyle: { width: 2, color },
            itemStyle: { color },
            areaStyle: showArea ? { color: 'rgba(0,0,0,0.04)' } : undefined,
            markLine: this.metricType !== 'equity' ? {
              silent: true,
              symbol: 'none',
              lineStyle: { color: '#bdbdbd', type: 'dashed', width: 1 },
              data: [{ yAxis: 0 }]
            } : undefined
          }
        ]
      }, true)
    }
  }
}
</script>

<style scoped>
.trading-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.filter-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 14px 16px;
  border-radius: 8px;
  background: #ffffff;
  border: 1px solid #e0e0e0;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.filter-label {
  flex-shrink: 0;
  width: 36px;
  color: #8a8a8a;
  font-size: 12px;
  font-weight: 500;
}

.filter-group {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.filter-btn {
  padding: 5px 14px;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  background: #fafafa;
  color: #5c5c5c;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s, color 0.15s;
  line-height: 1.4;
}

.filter-btn:hover {
  border-color: #bdbdbd;
  color: #1a1a1a;
}

.filter-btn.active {
  background: #1a1a1a;
  border-color: #1a1a1a;
  color: #ffffff;
}

.chart-card {
  padding: 16px 18px;
  border-radius: 8px;
  background: #ffffff;
  border: 1px solid #e0e0e0;
  box-shadow: none;
}

.chart-header {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.chart-title {
  color: #1a1a1a;
  font-size: 14px;
  font-weight: 600;
}

.chart-range {
  color: #8a8a8a;
  font-size: 12px;
}

.curve-chart {
  width: 100%;
  height: 420px;
}

.chart-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 420px;
  color: #8a8a8a;
  font-size: 13px;
}
</style>
