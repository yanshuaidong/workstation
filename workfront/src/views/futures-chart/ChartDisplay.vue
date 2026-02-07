<template>
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
            :model-value="showEvents"
            active-text="显示事件标记"
            inactive-text=""
            @change="handleShowEventsChange"
            style="margin-right: 16px;"
          />
          <el-button 
            type="primary" 
            size="small" 
            icon="List"
            @click="handleOpenEventsDrawer"
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
</template>

<script>
import { markRaw } from 'vue'
import * as echarts from 'echarts'

export default {
  name: 'ChartDisplay',
  props: {
    selectedContract: {
      type: String,
      default: ''
    },
    selectedContractName: {
      type: String,
      default: ''
    },
    historyData: {
      type: Array,
      default: () => []
    },
    eventsData: {
      type: Array,
      default: () => []
    },
    showEvents: {
      type: Boolean,
      default: true
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
    chartTitle() {
      if (this.selectedContractName) {
        return `${this.selectedContractName} K线走势图`
      }
      return '期货K线走势图'
    }
  },
  emits: ['update:showEvents', 'open-events-drawer'],
  watch: {
    historyData: {
      handler() {
        this.$nextTick(() => {
          this.renderChart()
        })
      },
      deep: true
    },
    eventsData: {
      handler() {
        if (this.historyData.length > 0) {
          this.$nextTick(() => {
            this.renderChart()
          })
        }
      },
      deep: true
    },
    showEvents() {
      if (this.historyData.length > 0) {
        this.$nextTick(() => {
          this.renderChart()
        })
      }
    }
  },
  mounted() {
    window.addEventListener('resize', this.handleResize)
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.handleResize)
    if (this.chart) {
      this.chart.dispose()
    }
  },
  methods: {
    handleShowEventsChange(val) {
      this.$emit('update:showEvents', val)
    },
    handleOpenEventsDrawer() {
      this.$emit('open-events-drawer')
    },
    handleResize() {
      if (this.chart) {
        this.chart.resize()
      }
    },
    renderChart() {
      if (!this.historyData.length) return

      const container = this.$refs.chartContainer
      if (!container) return

      // 销毁旧的图表实例并重新创建
      if (this.chart) {
        this.chart.dispose()
        this.chart = null
      }
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

      // 准备事件标记线
      const markLines = []
      const markPoints = []
      
      if (this.showEvents && this.eventsData.length > 0) {
        this.eventsData.forEach(event => {
          const dateIndex = dates.indexOf(event.event_date)
          if (dateIndex !== -1) {
            const item = this.historyData[dateIndex]
            const color = this.getOutlookColor(event.outlook)
            const colorLight = this.getOutlookColorLight(event.outlook)
            
            markLines.push({
              xAxis: event.event_date,
              label: { show: false },
              lineStyle: {
                color: colorLight,
                type: [4, 4],
                width: 1,
                opacity: 0.6
              }
            })
            
            const isBearish = event.outlook === 'bearish'
            const pricePosition = isBearish ? item.raw.high_price : item.raw.low_price
            const symbolOffset = isBearish ? [0, -12] : [0, 12]
            const labelPosition = isBearish ? 'top' : 'bottom'
            
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

      const option = this.buildChartOption(dates, ohlc, volumes, openInterests, volumeColors, markLines, markPoints)
      this.chart.setOption(option, { notMerge: true })
    },
    buildChartOption(dates, ohlc, volumes, openInterests, volumeColors, markLines, markPoints) {
      return {
        animation: true,
        legend: {
          data: ['K线', '成交量', '持仓量'],
          top: 10,
          left: 'center',
          textStyle: { fontSize: 12 }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross',
            crossStyle: { color: '#758696' },
            lineStyle: { color: '#758696', type: 'dashed' }
          },
          backgroundColor: 'rgba(30, 39, 46, 0.95)',
          borderWidth: 1,
          borderColor: 'rgba(255, 255, 255, 0.1)',
          padding: 12,
          textStyle: { color: '#e0e0e0' },
          extraCssText: 'box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3); border-radius: 6px;',
          formatter: this.tooltipFormatter
        },
        axisPointer: {
          link: [{ xAxisIndex: 'all' }],
          label: { backgroundColor: '#777' }
        },
        toolbox: {
          feature: {
            dataZoom: { xAxisIndex: [0, 1, 2], yAxisIndex: 'none' },
            restore: {},
            saveAsImage: {}
          },
          right: 20,
          top: 5
        },
        grid: [
          { left: '8%', right: '8%', top: '10%', height: '45%' },
          { left: '8%', right: '8%', top: '60%', height: '13%' },
          { left: '8%', right: '8%', top: '76%', height: '13%' }
        ],
        xAxis: [
          {
            type: 'category',
            gridIndex: 0,
            data: dates,
            boundaryGap: true,
            axisLine: { onZero: false },
            splitLine: { show: false },
            axisLabel: { rotate: 45, fontSize: 10 },
            min: 'dataMin',
            max: 'dataMax',
            axisPointer: { z: 100 }
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
            splitArea: { show: true },
            axisLabel: { fontSize: 10 }
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
              color: '#ef5350',
              color0: '#26a69a',
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
                color: volumeColors[i] > 0 ? 'rgba(239, 83, 80, 0.6)' : 'rgba(38, 166, 154, 0.6)'
              }
            })),
            emphasis: { disabled: true }
          },
          {
            name: '持仓量',
            type: 'bar',
            xAxisIndex: 2,
            yAxisIndex: 2,
            data: openInterests,
            itemStyle: { color: 'rgba(66, 165, 245, 0.6)' },
            emphasis: { disabled: true }
          }
        ]
      }
    },
    tooltipFormatter(params) {
      const dataIndex = params[0]?.dataIndex
      if (dataIndex === undefined) return ''
      
      const item = this.historyData[dataIndex]
      const raw = item.raw
      const changeColor = raw.change_pct >= 0 ? '#ef5350' : '#26a69a'
      const changeSign = raw.change_pct >= 0 ? '+' : ''
      
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
    },
    getOutlookColor(outlook) {
      const colors = {
        'bullish': '#ef5350',
        'bearish': '#26a69a',
        'ranging': '#ff9800',
        'uncertain': '#78909c'
      }
      return colors[outlook] || '#2196f3'
    },
    getOutlookColorLight(outlook) {
      const colors = {
        'bullish': 'rgba(239, 83, 80, 0.3)',
        'bearish': 'rgba(38, 166, 154, 0.3)',
        'ranging': 'rgba(255, 152, 0, 0.3)',
        'uncertain': 'rgba(120, 144, 156, 0.3)'
      }
      return colors[outlook] || 'rgba(33, 150, 243, 0.3)'
    },
    getOutlookIcon(outlook) {
      const icons = {
        'bullish': '▲',
        'bearish': '▼',
        'ranging': '◆',
        'uncertain': '●'
      }
      return icons[outlook] || '◉'
    },
    formatVolume(volume) {
      if (!volume) return '0'
      if (volume >= 100000000) {
        return (volume / 100000000).toFixed(2) + '亿'
      } else if (volume >= 10000) {
        return (volume / 10000).toFixed(2) + '万'
      }
      return volume.toString()
    },
    formatAxisVolume(value) {
      if (value >= 100000000) {
        return (value / 100000000).toFixed(1) + '亿'
      } else if (value >= 10000) {
        return (value / 10000).toFixed(0) + '万'
      }
      return value
    }
  }
}
</script>

<style scoped>
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

@media (max-width: 1200px) {
  .chart-container {
    height: 500px;
  }
}

@media (max-width: 768px) {
  .chart-container {
    height: 400px;
  }
}
</style>
