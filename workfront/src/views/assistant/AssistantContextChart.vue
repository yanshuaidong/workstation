<template>
  <div class="context-chart-card">
    <div class="chart-title">近 {{ chartDays }} 日价格 / 主力 / 散户上下文</div>
    <div v-if="loading" class="chart-placeholder">正在加载图表...</div>
    <div v-else-if="!seriesData.length" class="chart-placeholder">暂无上下文数据</div>
    <div v-else ref="chartRef" class="chart-canvas"></div>
    <div v-if="seriesData.length" class="chart-footnote">hover 任一点可查看当天收盘价、主力值和散户值，用来判断价格与资金是否共振或背离。</div>
  </div>
</template>

<script>
import { markRaw } from 'vue'
import * as echarts from 'echarts'
import { buildAssistantContextChartOption } from '@/utils/assistantContextChartOptions.mjs'

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
      chart: null,
      resizeFrame: null,
      renderFrame: null
    }
  },
  computed: {
    chartDays() {
      return this.seriesData.length || 10
    }
  },
  mounted() {
    this.scheduleRender()
    window.addEventListener('resize', this.handleResize)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize)
    if (this.resizeFrame) {
      cancelAnimationFrame(this.resizeFrame)
      this.resizeFrame = null
    }
    if (this.renderFrame) {
      cancelAnimationFrame(this.renderFrame)
      this.renderFrame = null
    }
    if (this.chart) {
      this.chart.dispose()
      this.chart = null
    }
  },
  watch: {
    seriesData: {
      deep: true,
      handler() {
        this.scheduleRender()
      }
    },
    loading() {
      this.$nextTick(() => {
        this.scheduleRender()
      })
    }
  },
  methods: {
    handleResize() {
      if (this.resizeFrame) {
        cancelAnimationFrame(this.resizeFrame)
      }
      this.resizeFrame = requestAnimationFrame(() => {
        if (this.chart) {
          this.chart.resize()
        }
        this.resizeFrame = null
      })
    },
    scheduleRender() {
      if (this.renderFrame) {
        cancelAnimationFrame(this.renderFrame)
      }
      this.renderFrame = requestAnimationFrame(() => {
        this.renderChart()
        this.renderFrame = null
      })
    },
    renderChart() {
      if (this.loading || !this.$refs.chartRef || !this.seriesData.length) {
        return
      }

      if (!this.chart) {
        this.chart = markRaw(echarts.init(this.$refs.chartRef))
      }

      this.chart.setOption(buildAssistantContextChartOption({ seriesData: this.seriesData }))
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

.chart-footnote {
  margin-top: 10px;
  color: #7d8d9c;
  font-size: 12px;
  line-height: 1.6;
}
</style>
