<template>
  <div class="kline-view">
    <div class="toolbar">
      <el-select
        v-model="selectedVarietyId"
        placeholder="选择品种"
        style="width: 160px"
        @change="fetchData"
      >
        <el-option
          v-for="v in varieties"
          :key="v.id"
          :label="v.name"
          :value="v.id"
        />
      </el-select>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="—"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        :clearable="false"
        style="width: 240px"
        @change="fetchData"
      />
    </div>

    <div v-if="!selectedVarietyId" class="empty-hint">请选择品种</div>

    <template v-else>
      <div v-loading="loading">
        <div ref="klineChart" class="chart-kline" />
        <div ref="mainForceChart" class="chart-index" />
        <div ref="retailChart" class="chart-index" />
      </div>
    </template>
  </div>
</template>

<script>
import * as echarts from 'echarts'
import request from '@/utils/request'
import { getAssistantVarietyListApi, getAssistantVarietyKlineApi } from '@/api'

const DAYS_DEFAULT = 60

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}
function daysAgoStr(n) {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toISOString().slice(0, 10)
}

export default {
  name: 'KlineView',
  data() {
    return {
      varieties: [],
      selectedVarietyId: null,
      dateRange: [daysAgoStr(DAYS_DEFAULT), todayStr()],
      loading: false,
      klineInstance: null,
      mainForceInstance: null,
      retailInstance: null,
    }
  },
  mounted() {
    this.fetchVarieties()
  },
  beforeUnmount() {
    this.disposeCharts()
  },
  methods: {
    async fetchVarieties() {
      try {
        const res = await request.get(getAssistantVarietyListApi)
        if (res.code === 0) {
          this.varieties = res.data.varieties
        }
      } catch (e) {
        console.error('获取品种列表失败', e)
      }
    },

    async fetchData() {
      if (!this.selectedVarietyId) return
      this.loading = true
      try {
        const [start_date, end_date] = this.dateRange
        const res = await request.get(getAssistantVarietyKlineApi, {
          params: { variety_id: this.selectedVarietyId, start_date, end_date }
        })
        if (res.code === 0) {
          await this.$nextTick()
          this.renderCharts(res.data)
        }
      } catch (e) {
        console.error('获取K线数据失败', e)
      } finally {
        this.loading = false
      }
    },

    renderCharts(data) {
      const dates = data.kline.map(r => r.trade_date)
      const ohlcv = data.kline.map(r => [r.open, r.close, r.low, r.high])
      const volumes = data.kline.map(r => r.volume)
      const mainForce = data.strength.map(r => r.main_force)
      const retail = data.strength.map(r => r.retail)
      const varietyName = data.variety.name

      this.renderKline(dates, ohlcv, volumes, varietyName)
      this.renderIndex(this.$refs.mainForceChart, 'mainForceInstance', dates, mainForce, `${varietyName} 主力指数`, '#2f7cff')
      this.renderIndex(this.$refs.retailChart, 'retailInstance', dates, retail, `${varietyName} 散户指数`, '#db7c26')
    },

    renderKline(dates, ohlcv, volumes, title) {
      if (!this.klineInstance) {
        this.klineInstance = echarts.init(this.$refs.klineChart)
      }
      const upColor = '#ef5350'
      const downColor = '#26a69a'
      this.klineInstance.setOption({
        title: { text: `${title} K线`, left: 12, top: 8, textStyle: { fontSize: 13, color: '#3c5168' } },
        tooltip: { trigger: 'axis', axisPointer: { type: 'cross' } },
        axisPointer: { link: [{ xAxisIndex: [0, 1] }] },
        grid: [
          { left: 60, right: 16, top: 44, bottom: 80 },
          { left: 60, right: 16, height: 50, bottom: 20 }
        ],
        xAxis: [
          { type: 'category', data: dates, gridIndex: 0, axisLabel: { show: false } },
          { type: 'category', data: dates, gridIndex: 1, axisLabel: { fontSize: 11 } }
        ],
        yAxis: [
          { scale: true, gridIndex: 0, splitLine: { lineStyle: { color: '#f0f4f8' } } },
          { scale: true, gridIndex: 1, splitLine: { show: false }, axisLabel: { formatter: v => (v / 10000).toFixed(0) + 'w' } }
        ],
        dataZoom: [
          { type: 'inside', xAxisIndex: [0, 1], start: 60, end: 100 },
          { type: 'slider', xAxisIndex: [0, 1], bottom: 4, height: 14 }
        ],
        series: [
          {
            name: 'K线',
            type: 'candlestick',
            xAxisIndex: 0,
            yAxisIndex: 0,
            data: ohlcv,
            itemStyle: {
              color: upColor, color0: downColor,
              borderColor: upColor, borderColor0: downColor
            }
          },
          {
            name: '成交量',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: volumes,
            itemStyle: { color: '#b0bec5' }
          }
        ]
      }, true)
    },

    renderIndex(el, instanceKey, dates, values, title, color) {
      if (!this[instanceKey]) {
        this[instanceKey] = echarts.init(el)
      }
      this[instanceKey].setOption({
        title: { text: title, left: 12, top: 6, textStyle: { fontSize: 13, color: '#3c5168' } },
        tooltip: { trigger: 'axis' },
        grid: { left: 60, right: 16, top: 36, bottom: 28 },
        xAxis: { type: 'category', data: dates, axisLabel: { fontSize: 11 } },
        yAxis: { scale: true, splitLine: { lineStyle: { color: '#f0f4f8' } } },
        dataZoom: [{ type: 'inside', start: 60, end: 100 }],
        series: [{
          type: 'line',
          data: values,
          smooth: true,
          symbol: 'none',
          lineStyle: { color, width: 2 },
          areaStyle: { color: echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: color + '33' },
            { offset: 1, color: color + '00' }
          ]) }
        }]
      }, true)
    },

    disposeCharts() {
      ['klineInstance', 'mainForceInstance', 'retailInstance'].forEach(k => {
        if (this[k]) { this[k].dispose(); this[k] = null }
      })
    }
  }
}
</script>

<style scoped>
.kline-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.empty-hint {
  padding: 60px 0;
  text-align: center;
  color: #91a1b2;
  font-size: 14px;
}

.chart-kline {
  width: 100%;
  height: 360px;
  border-radius: 12px;
  border: 1px solid #edf2f7;
}

.chart-index {
  width: 100%;
  height: 180px;
  border-radius: 12px;
  border: 1px solid #edf2f7;
  margin-top: 12px;
}
</style>
