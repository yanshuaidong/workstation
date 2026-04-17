<template>
  <div class="context-chart-card">
    <div class="chart-title">近 {{ chartDays }} 日价格 / 主力 / 散户上下文</div>
    <div v-if="loading" class="chart-placeholder">正在加载图表...</div>
    <div v-else-if="!seriesData.length" class="chart-placeholder">暂无上下文数据</div>
    <div v-else ref="chartRef" class="chart-canvas"></div>
  </div>
</template>

<script>
import * as echarts from 'echarts'

export default {
  name: 'AssistantContextChart',
  props: {
    seriesData: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      chart: null
    }
  },
  computed: {
    chartDays() {
      return this.seriesData.length || 10
    }
  },
  mounted() {
    this.renderChart()
    window.addEventListener('resize', this.handleResize)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize)
    if (this.chart) {
      this.chart.dispose()
      this.chart = null
    }
  },
  watch: {
    seriesData: {
      deep: true,
      handler() {
        this.renderChart()
      }
    },
    loading() {
      this.$nextTick(() => {
        this.renderChart()
      })
    }
  },
  methods: {
    handleResize() {
      if (this.chart) {
        this.chart.resize()
      }
    },
    renderChart() {
      if (this.loading || !this.$refs.chartRef || !this.seriesData.length) {
        return
      }

      if (!this.chart) {
        this.chart = echarts.init(this.$refs.chartRef)
      }

      const dates = this.seriesData.map(item => item.trade_date)
      const closeSeries = this.seriesData.map(item => item.close_price)
      const mainForceSeries = this.seriesData.map(item => item.main_force)
      const retailSeries = this.seriesData.map(item => item.retail)

      this.chart.setOption({
        color: ['#2f7cff', '#db7c26', '#2f9d62'],
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          top: 0
        },
        grid: [
          { top: 40, left: 50, right: 20, height: '42%' },
          { left: 50, right: 20, top: '60%', height: '28%' }
        ],
        xAxis: [
          {
            type: 'category',
            data: dates,
            boundaryGap: false
          },
          {
            type: 'category',
            data: dates,
            boundaryGap: false,
            gridIndex: 1
          }
        ],
        yAxis: [
          {
            type: 'value',
            scale: true,
            name: '收盘价'
          },
          {
            type: 'value',
            scale: true,
            gridIndex: 1,
            name: '资金值'
          }
        ],
        series: [
          {
            name: '收盘价',
            type: 'line',
            smooth: true,
            symbol: 'circle',
            symbolSize: 6,
            data: closeSeries,
            lineStyle: { width: 3 },
            areaStyle: {
              opacity: 0.12
            }
          },
          {
            name: 'main_force',
            type: 'line',
            xAxisIndex: 1,
            yAxisIndex: 1,
            smooth: true,
            symbolSize: 6,
            data: mainForceSeries,
            lineStyle: { width: 2 }
          },
          {
            name: 'retail',
            type: 'line',
            xAxisIndex: 1,
            yAxisIndex: 1,
            smooth: true,
            symbolSize: 6,
            data: retailSeries,
            lineStyle: { width: 2 }
          }
        ]
      })
    }
  }
}
</script>

<style scoped>
.context-chart-card {
  margin: 6px 0;
  padding: 14px 16px;
  border-radius: 16px;
  background: linear-gradient(180deg, #f7fbff 0%, #ffffff 100%);
  border: 1px solid #e5eef8;
}

.chart-title {
  margin-bottom: 12px;
  color: #243447;
  font-size: 14px;
  font-weight: 600;
}

.chart-canvas {
  width: 100%;
  height: 360px;
}

.chart-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 180px;
  color: #8a98a8;
  font-size: 13px;
}
</style>

