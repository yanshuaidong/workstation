<template>
  <div class="trading-page">
    <div class="toolbar">
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        value-format="YYYY-MM-DD"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        clearable
      />
      <el-button type="primary" :loading="loading" @click="fetchCurve">刷新曲线</el-button>
    </div>

    <div class="chart-card">
      <div v-if="loading" class="chart-placeholder">正在加载资金曲线...</div>
      <div v-else-if="!curve.length" class="chart-placeholder">暂无账户净值数据</div>
      <div v-else ref="chartRef" class="curve-chart" />
    </div>
  </div>
</template>

<script>
import { markRaw } from 'vue'
import * as echarts from 'echarts'
import request from '@/utils/request'
import { getTradingAccountCurveApi } from '@/api'

export default {
  name: 'TradingCurveView',
  inject: {
    refreshAccountSummary: { default: null }
  },
  data() {
    return {
      loading: false,
      dateRange: [],
      curve: [],
      chart: null,
      resizeFrame: null,
      renderFrame: null
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
  watch: {
    curve: {
      deep: true,
      handler() {
        this.$nextTick(() => this.scheduleRender())
      }
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
        const res = await request.get(getTradingAccountCurveApi, {
          params: {
            start_date: this.dateRange?.[0] || undefined,
            end_date: this.dateRange?.[1] || undefined
          }
        })
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
    renderChart() {
      if (!this.$refs.chartRef || !this.curve.length) return
      if (!this.chart) {
        this.chart = markRaw(echarts.init(this.$refs.chartRef))
      }
      const dates = this.curve.map(r => r.record_date)
      const equities = this.curve.map(r => r.equity)
      const dailyPnls = this.curve.map(r => r.daily_pnl)

      this.chart.setOption({
        color: ['#2f7cff', '#db7c26'],
        tooltip: { trigger: 'axis' },
        legend: { top: 0, data: ['账户净值', '当日盈亏'] },
        grid: { left: 60, right: 24, top: 40, bottom: 40 },
        xAxis: { type: 'category', data: dates, boundaryGap: false },
        yAxis: [
          { type: 'value', name: '净值（元）', scale: true },
          { type: 'value', name: '当日盈亏', scale: true, splitLine: { show: false } }
        ],
        series: [
          {
            name: '账户净值',
            type: 'line',
            smooth: true,
            symbolSize: 5,
            data: equities,
            lineStyle: { width: 3 },
            areaStyle: { opacity: 0.1 },
            yAxisIndex: 0
          },
          {
            name: '当日盈亏',
            type: 'bar',
            data: dailyPnls,
            yAxisIndex: 1,
            itemStyle: {
              color: params => params.value >= 0 ? '#52c41a' : '#ff4d4f',
              opacity: 0.7
            }
          }
        ]
      })
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

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.chart-card {
  padding: 14px 16px;
  border-radius: 18px;
  background: linear-gradient(180deg, #f7fbff 0%, #ffffff 100%);
  border: 1px solid #e6eef7;
}

.curve-chart {
  width: 100%;
  height: 420px;
}

.chart-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
  color: #8a98a8;
}
</style>
