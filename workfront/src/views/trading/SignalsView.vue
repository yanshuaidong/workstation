<template>
  <div class="trading-page">
    <div class="toolbar">
      <el-date-picker
        v-model="filters.date"
        type="date"
        value-format="YYYY-MM-DD"
        placeholder="选择日期"
        clearable
      />
      <el-select
        v-model="filters.signal_type"
        clearable
        placeholder="信号类型"
        class="tool-item signal-type-filter"
        :class="filters.signal_type ? signalPillClass(filters.signal_type) : ''"
      >
        <el-option label="A_OPEN_LONG（开多）" value="A_OPEN_LONG">
          <span class="signal-pill" :class="signalPillClass('A_OPEN_LONG')">A_OPEN_LONG（开多）</span>
        </el-option>
        <el-option label="A_OPEN_SHORT（开空）" value="A_OPEN_SHORT">
          <span class="signal-pill" :class="signalPillClass('A_OPEN_SHORT')">A_OPEN_SHORT（开空）</span>
        </el-option>
        <el-option label="A_CLOSE_LONG（平多）" value="A_CLOSE_LONG">
          <span class="signal-pill" :class="signalPillClass('A_CLOSE_LONG')">A_CLOSE_LONG（平多）</span>
        </el-option>
        <el-option label="A_CLOSE_SHORT（平空）" value="A_CLOSE_SHORT">
          <span class="signal-pill" :class="signalPillClass('A_CLOSE_SHORT')">A_CLOSE_SHORT（平空）</span>
        </el-option>
      </el-select>
      <el-input v-model="filters.variety_name" clearable placeholder="品种筛选" class="tool-item" />
      <el-button :loading="loading" @click="fetchSignals">查询</el-button>
    </div>

    <div class="stats-row" v-if="!loading && signals.length">
      <span class="stat-line">
        <span class="sig-long">开多</span> {{ countByType('A_OPEN_LONG') }}
        <span class="stat-sep">·</span>
        <span class="sig-short">开空</span> {{ countByType('A_OPEN_SHORT') }}
        <span class="stat-sep">·</span>
        <span class="sig-long">平多</span> {{ countByType('A_CLOSE_LONG') }}
        <span class="stat-sep">·</span>
        <span class="sig-short">平空</span> {{ countByType('A_CLOSE_SHORT') }}
      </span>
      <span class="total-hint">共 {{ signals.length }} 条 · 点击行展开计算过程</span>
    </div>

    <el-table
      v-loading="loading"
      :data="signals"
      stripe
      class="data-table"
      row-key="id"
      @expand-change="onExpandChange"
    >
      <el-table-column type="expand">
        <template #default="{ row: sig }">
          <div class="sig-detail">
            <template v-if="sig.extra_json && sig.extra_json.window && sig.extra_json.window.length">
              <!-- ECharts 图表区 -->
              <div
                :ref="el => { if (el) chartRefs[sig.id] = el }"
                class="signal-chart"
              ></div>

              <!-- 图表下方关键数字 + 条件 -->
              <div class="info-bar">
                <!-- 开仓：背景期数值 -->
                <template v-if="isOpen(sig.signal_type) && sig.extra_json.bg">
                  <div class="info-section">
                    <span class="section-label">背景期</span>
                    <span v-for="k in ['bg1', 'bg2', 'bg3', 'bg4', 'bg5']" :key="k" class="kv-chip">
                      <span class="kv-name">{{ k }}</span>
                      <span :class="numCls(sig.extra_json.bg[k])">{{ fmtNum(sig.extra_json.bg[k]) }}</span>
                    </span>
                  </div>

                  <!-- 开仓：触发期差值 -->
                  <div class="info-section" v-if="sig.extra_json.trigger">
                    <span class="section-label">触发期</span>
                    <span class="kv-chip">
                      <span class="kv-name">主力diff[t-1]</span>
                      <span :class="numCls(sig.extra_json.trigger.main_diff_t1)">{{ fmtNum(sig.extra_json.trigger.main_diff_t1) }}</span>
                    </span>
                    <span class="kv-chip">
                      <span class="kv-name">主力diff[t]</span>
                      <span :class="numCls(sig.extra_json.trigger.main_diff_t)">{{ fmtNum(sig.extra_json.trigger.main_diff_t) }}</span>
                    </span>
                    <span class="kv-chip">
                      <span class="kv-name">散户diff[t-1]</span>
                      <span :class="numCls(sig.extra_json.trigger.retail_diff_t1)">{{ fmtNum(sig.extra_json.trigger.retail_diff_t1) }}</span>
                    </span>
                    <span class="kv-chip">
                      <span class="kv-name">散户diff[t]</span>
                      <span :class="numCls(sig.extra_json.trigger.retail_diff_t)">{{ fmtNum(sig.extra_json.trigger.retail_diff_t) }}</span>
                    </span>
                  </div>
                </template>

                <!-- 平仓：m3 值 -->
                <template v-else-if="!isOpen(sig.signal_type)">
                  <div class="info-section">
                    <span class="section-label">平仓指标</span>
                    <span class="kv-chip">
                      <span class="kv-name">m3 = main[t]−main[t-2]</span>
                      <span :class="numCls(sig.extra_json.m3)">{{ fmtNum(sig.extra_json.m3) }}</span>
                    </span>
                  </div>
                </template>

                <!-- 条件分解 -->
                <div class="info-section">
                  <span class="section-label">条件</span>
                  <span
                    v-for="(val, key) in sig.extra_json.conditions"
                    :key="key"
                    class="cond-chip"
                    :class="val ? 'cond-pass' : 'cond-fail'"
                  >
                    {{ val ? '✓' : '✗' }} {{ getCondLabel(key, sig.signal_type) }}
                  </span>
                </div>
              </div>
            </template>

            <div v-else class="no-detail">
              旧数据未存储计算过程，请重新运行 <code>daily_run</code> 补录
            </div>
          </div>
        </template>
      </el-table-column>

      <el-table-column prop="signal_date" label="日期" width="120" />
      <el-table-column prop="variety_name" label="品种" min-width="100" />
      <el-table-column label="信号类型" min-width="150">
        <template #default="{ row }">
          <span class="signal-pill" :class="signalPillClass(row.signal_type)">
            {{ getSignalLabel(row.signal_type) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="动量分位分" width="130">
        <template #default="{ row }">
          <span v-if="row.main_score !== null && row.main_score !== undefined">
            {{ (row.main_score * 100).toFixed(1) }}%
          </span>
          <span v-else class="dim">--</span>
        </template>
      </el-table-column>
      <el-table-column prop="variety_id" label="品种ID" width="90" />
    </el-table>

    <div v-if="!loading && !signals.length" class="empty-card">
      <el-empty description="当前条件下没有信号数据" />
    </div>
  </div>
</template>

<script>
import { markRaw } from 'vue'
import * as echarts from 'echarts'
import request from '@/utils/request'
import { getTradingSignalsApi } from '@/api'

const SIGNAL_META = {
  A_OPEN_LONG:  { label: 'A-开多' },
  A_OPEN_SHORT: { label: 'A-开空' },
  A_CLOSE_LONG: { label: 'A-平多' },
  A_CLOSE_SHORT:{ label: 'A-平空' },
}

const COND_LABELS = {
  A_OPEN_LONG: {
    cont7:              '连续7日无中断',
    bg1_lt0:            'bg1<0',
    bg2_lt0:            'bg2<0',
    bg3_lt0:            'bg3<0',
    bg4_lt0:            'bg4<0',
    bg5_lt0:            'bg5<0',
    bg5_is_min:         'bg5是背景期最低点（极值唯一性）',
    main_diff_t1_gt0:   '主力diff[t-1]>0',
    main_diff_t_gt0:    '主力diff[t]>0',
    retail_diff_t1_lt0: '散户diff[t-1]<0',
    retail_diff_t_lt0:  '散户diff[t]<0',
  },
  A_OPEN_SHORT: {
    cont7:              '连续7日无中断',
    bg1_gt0:            'bg1>0',
    bg2_gt0:            'bg2>0',
    bg3_gt0:            'bg3>0',
    bg4_gt0:            'bg4>0',
    bg5_gt0:            'bg5>0',
    bg5_is_max:         'bg5是背景期最高点（极值唯一性）',
    main_diff_t1_lt0:   '主力diff[t-1]<0',
    main_diff_t_lt0:    '主力diff[t]<0',
    retail_diff_t1_gt0: '散户diff[t-1]>0',
    retail_diff_t_gt0:  '散户diff[t]>0',
  },
  A_CLOSE_LONG: {
    cont3:  '连续3日无中断',
    m3_lt0: 'm3<0（主力3日拐头向下）',
  },
  A_CLOSE_SHORT: {
    cont3:  '连续3日无中断',
    m3_gt0: 'm3>0（主力3日拐头向上）',
  },
}

export default {
  name: 'TradingSignalsView',
  data() {
    return {
      loading: false,
      signals: [],
      filters: { date: '', signal_type: '', variety_name: '' },
      chartRefs: {},
      chartInstances: {},
    }
  },
  watch: {
    signals() {
      Object.values(this.chartInstances).forEach(inst => inst.dispose())
      this.chartInstances = {}
      this.chartRefs = {}
    },
  },
  mounted() {
    this.fetchSignals()
  },
  beforeUnmount() {
    Object.values(this.chartInstances).forEach(inst => inst.dispose())
  },
  methods: {
    async fetchSignals() {
      this.loading = true
      try {
        const res = await request.get(getTradingSignalsApi, {
          params: {
            date: this.filters.date || undefined,
            signal_type: this.filters.signal_type || undefined,
            variety_name: this.filters.variety_name || undefined,
          },
        })
        if (res.code === 0) {
          this.signals = res.data?.signals || []
          if (!this.filters.date && res.data?.date) {
            this.filters.date = res.data.date
          }
        }
      } catch (error) {
        console.error('获取信号失败', error)
      } finally {
        this.loading = false
      }
    },

    async onExpandChange(row, expandedRows) {
      const id = row.id
      const isExpanded = expandedRows.some(r => r.id === id)
      if (isExpanded) {
        await this.$nextTick()
        const el = this.chartRefs[id]
        if (!el) return
        const extra = row.extra_json
        if (!extra?.window?.length) return
        if (this.chartInstances[id]) {
          this.chartInstances[id].dispose()
        }
        const inst = markRaw(echarts.init(el))
        inst.setOption(this.buildChartOption(row))
        this.chartInstances[id] = inst
      } else {
        const inst = this.chartInstances[id]
        if (inst) {
          inst.dispose()
          delete this.chartInstances[id]
        }
      }
    },

    buildChartOption(sig) {
      const extra = sig.extra_json
      const win = extra.window
      const isOpenSig = this.isOpen(sig.signal_type)
      const dates = win.map(w => w.trade_date.slice(5))
      const mainData = win.map(w => w.main_force ?? null)
      const retailData = win.map(w => w.retail ?? null)

      // 主力线：触发期两点放大标注
      const mainSeriesData = mainData.map((v, i) => {
        if (isOpenSig && win.length === 7 && i >= 5) {
          return { value: v, symbolSize: 10, itemStyle: { color: '#616161', borderColor: '#fff', borderWidth: 2 } }
        }
        return v
      })

      const mainSeries = {
        name: '主力净持仓',
        type: 'line',
        data: mainSeriesData,
        symbol: 'circle',
        symbolSize: 5,
        lineStyle: { color: '#616161', width: 2 },
        itemStyle: { color: '#616161' },
        // y=0 参考线
        markLine: {
          silent: true,
          symbol: 'none',
          data: [{ yAxis: 0, lineStyle: { color: '#d0d7e3', type: 'dashed', width: 1 }, label: { show: false } }],
        },
      }

      // 开仓信号：标注背景期和触发期分区（bg1..bg5=dates[0..4]，触发期=dates[5..6]）
      if (isOpenSig && win.length === 7) {
        mainSeries.markArea = {
          silent: true,
          data: [
            [
              {
                name: '背景期',
                xAxis: dates[0],
                itemStyle: { color: 'rgba(0,0,0,0.06)' },
                label: { color: '#8a8a8a', fontSize: 10, position: 'insideTopLeft' },
              },
              { xAxis: dates[4] },
            ],
            [
              {
                name: '触发期',
                xAxis: dates[5],
                itemStyle: { color: 'rgba(0,0,0,0.08)' },
                label: { color: '#5c5c5c', fontSize: 10, position: 'insideTopLeft' },
              },
              { xAxis: dates[6] },
            ],
          ],
        }
      }

      const retailSeries = {
        name: '散户净持仓',
        type: 'line',
        data: retailData,
        symbol: 'circle',
        symbolSize: 5,
        lineStyle: { color: '#9e9e9e', width: 2 },
        itemStyle: { color: '#9e9e9e' },
      }

      return {
        backgroundColor: 'transparent',
        grid: { top: 36, right: 24, bottom: 28, left: 64 },
        tooltip: {
          trigger: 'axis',
          formatter(params) {
            let s = `<b>${params[0].axisValue}</b><br/>`
            params.forEach(p => {
              const v = p.value !== null && p.value !== undefined ? Number(p.value).toFixed(4) : '--'
              s += `${p.marker}${p.seriesName}: <b>${v}</b><br/>`
            })
            return s
          },
        },
        legend: { top: 4, right: 12, textStyle: { fontSize: 11 } },
        xAxis: {
          type: 'category',
          data: dates,
          axisLabel: { fontSize: 11 },
          axisLine: { lineStyle: { color: '#e0e0e0' } },
          axisTick: { lineStyle: { color: '#e0e0e0' } },
        },
        yAxis: {
          type: 'value',
          axisLabel: { fontSize: 10, formatter: v => v.toFixed(2) },
          splitLine: { lineStyle: { color: '#f0f0f0' } },
        },
        series: [mainSeries, retailSeries],
      }
    },

    getSignalLabel(type)    { return SIGNAL_META[type]?.label || type },
    signalPillClass(type) {
      if (type === 'A_OPEN_LONG' || type === 'A_CLOSE_LONG') return 'pill-long'
      if (type === 'A_OPEN_SHORT' || type === 'A_CLOSE_SHORT') return 'pill-short'
      return 'pill-neutral'
    },
    countByType(type)       { return this.signals.filter(s => s.signal_type === type).length },
    isOpen(type)            { return type === 'A_OPEN_LONG' || type === 'A_OPEN_SHORT' },
    getCondLabel(key, type) { return COND_LABELS[type]?.[key] || key },

    fmtNum(v) {
      if (v === null || v === undefined || isNaN(v)) return '--'
      return Number(v).toFixed(4)
    },
    numCls(v) {
      if (v === null || v === undefined || isNaN(v)) return ''
      return v > 0 ? 'pos' : v < 0 ? 'neg' : ''
    },
  },
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

.tool-item { width: 200px; }

/* 选中项与表格 pill 同色（Element Plus 2 选中文本节点在 .el-select__selected-item 内） */
.signal-type-filter.pill-long :deep(.el-select__selected-item) {
  color: #c62828;
}
.signal-type-filter.pill-short :deep(.el-select__selected-item) {
  color: #2e7d32;
}

.stats-row {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.total-hint { color: #8a8a8a; font-size: 13px; }

.stat-line {
  font-size: 13px;
  color: #1a1a1a;
}

.stat-sep {
  margin: 0 8px;
  color: #d0d0d0;
}

.sig-long {
  color: #c62828;
  font-weight: 600;
  margin-right: 4px;
}

.sig-short {
  color: #2e7d32;
  font-weight: 600;
  margin-right: 4px;
}

.signal-pill {
  font-size: 13px;
  font-weight: 600;
}

.signal-pill.pill-long {
  color: #c62828;
}

.signal-pill.pill-short {
  color: #2e7d32;
}

.signal-pill.pill-neutral {
  color: #1a1a1a;
}

.empty-card {
  padding: 18px 20px;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  background: #fafafa;
}

.data-table { width: 100%; }
.dim { color: #bbb; }

/* ── 展开区域 ── */
.sig-detail {
  padding: 16px 20px 18px;
  background: #fafafa;
  border-top: 1px solid #e0e0e0;
}

/* ECharts 容器 */
.signal-chart {
  width: 100%;
  height: 210px;
  margin-bottom: 12px;
}

/* 图表下方信息栏 */
.info-bar {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-section {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}

.section-label {
  font-size: 11px;
  font-weight: 600;
  color: #8a8a8a;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  margin-right: 2px;
  white-space: nowrap;
}

/* 数值 chip */
.kv-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  background: #f0f0f0;
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 12px;
}

.kv-name { color: #8a8a8a; }

/* 条件 chip — 灰阶，避免与涨跌语义色冲突 */
.cond-chip {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 12px;
  font-weight: 500;
}

.cond-pass { background: #f5f5f5; color: #1a1a1a; border: 1px solid #e0e0e0; }
.cond-fail { background: #fafafa; color: #9e9e9e; border: 1px dashed #e0e0e0; }

/* 数值着色（红涨绿跌） */
.pos { color: #c62828; font-weight: 600; }
.neg { color: #2e7d32; font-weight: 600; }

.no-detail {
  color: #8a8a8a;
  font-size: 13px;
  padding: 8px 0;
}

.no-detail code {
  background: #f0f0f0;
  padding: 1px 5px;
  border-radius: 3px;
  font-size: 12px;
  color: #1a1a1a;
}

@media (max-width: 768px) {
  .toolbar { flex-direction: column; align-items: stretch; }
  .tool-item { width: 100%; }
}
</style>
