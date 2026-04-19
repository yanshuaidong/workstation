<template>
  <div class="assistant-page">
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
      <div v-else-if="!hasCurveData" class="chart-placeholder">暂无账户净值数据</div>
      <div v-else ref="chartRef" class="curve-chart"></div>
    </div>
  </div>
</template>

<script>
import { markRaw } from 'vue'
import * as echarts from 'echarts'
import request from '@/utils/request'
import { getAssistantAccountCurveApi } from '@/api'

export default {
  name: 'AssistantCurveView',
  data() {
    return {
      loading: false,
      dateRange: [],
      curves: {
        mechanical: [],
        llm: []
      },
      chart: null,
      resizeFrame: null,
      renderFrame: null
    }
  },
  computed: {
    hasCurveData() {
      return (this.curves.mechanical?.length || 0) > 0 || (this.curves.llm?.length || 0) > 0
    }
  },
  mounted() {
    this.fetchCurve()
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
    curves: {
      deep: true,
      handler() {
        this.$nextTick(() => {
          this.scheduleRender()
        })
      }
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
    async fetchCurve() {
      this.loading = true
      try {
        const res = await request.get(getAssistantAccountCurveApi, {
          params: {
            start_date: this.dateRange?.[0] || undefined,
            end_date: this.dateRange?.[1] || undefined
          }
        })
        if (res.code === 0) {
          this.curves = res.data?.curves || { mechanical: [], llm: [] }
        }
      } catch (error) {
        console.error('获取资金曲线失败', error)
      } finally {
        this.loading = false
      }
    },
    renderChart() {
      if (!this.$refs.chartRef || !this.hasCurveData) {
        return
      }

      if (!this.chart) {
        this.chart = markRaw(echarts.init(this.$refs.chartRef))
      }

      const allDates = Array.from(
        new Set(
          [...(this.curves.mechanical || []), ...(this.curves.llm || [])].map(item => item.record_date)
        )
      ).sort()

      const mechanicalMap = Object.fromEntries((this.curves.mechanical || []).map(item => [item.record_date, item.equity]))
      const llmMap = Object.fromEntries((this.curves.llm || []).map(item => [item.record_date, item.equity]))

      this.chart.setOption({
        color: ['#2f7cff', '#db7c26'],
        tooltip: {
          trigger: 'axis'
        },
        legend: {
          top: 0
        },
        grid: {
          left: 56,
          right: 24,
          top: 40,
          bottom: 40
        },
        xAxis: {
          type: 'category',
          data: allDates,
          boundaryGap: false
        },
        yAxis: {
          type: 'value',
          scale: true,
          name: '账户净值'
        },
        series: [
          {
            name: 'mechanical',
            type: 'line',
            smooth: true,
            symbolSize: 7,
            data: allDates.map(date => mechanicalMap[date] ?? null),
            lineStyle: { width: 3 },
            areaStyle: { opacity: 0.12 }
          },
          {
            name: 'llm',
            type: 'line',
            smooth: true,
            symbolSize: 7,
            data: allDates.map(date => llmMap[date] ?? null),
            lineStyle: { width: 3 }
          }
        ]
      })
    }
  }
}
</script>

<style scoped>
.assistant-page {
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
  min-height: 220px;
  color: #8a98a8;
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
}
</style>
