<template>
  <div class="anomaly-page">
    <!-- 筛选栏 -->
    <div class="toolbar">
      <el-date-picker
        v-model="filters.dateRange"
        type="daterange"
        value-format="YYYY-MM-DD"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        :shortcuts="dateShortcuts"
        class="tool-item date-range"
      />
      <el-select
        v-model="filters.metric"
        clearable
        placeholder="指标类型"
        class="tool-item"
      >
        <el-option
          v-for="m in metricOptions"
          :key="m.value"
          :label="m.label"
          :value="m.value"
        />
      </el-select>
      <el-input
        v-model="filters.variety_name"
        clearable
        placeholder="品种筛选"
        class="tool-item"
        @keyup.enter="fetchSignals"
      />
      <el-select
        v-model="filters.minZ"
        clearable
        placeholder="最小|Z|"
        class="tool-item min-z-select"
      >
        <el-option label="|Z| ≥ 2.5（所有）" :value="0" />
        <el-option label="|Z| ≥ 3.0" :value="3.0" />
        <el-option label="|Z| ≥ 4.0" :value="4.0" />
        <el-option label="|Z| ≥ 5.0" :value="5.0" />
      </el-select>
      <el-button :loading="loading" type="primary" @click="fetchSignals">查询</el-button>
      <el-button @click="resetFilters">重置</el-button>
    </div>

    <!-- 统计条 -->
    <div class="stats-row" v-if="!loading">
      <span class="stat-label">{{ statsLabel }}</span>
      <span
        v-for="m in metricOptions"
        :key="m.value"
        class="stat-chip"
        :class="`metric-${m.value}`"
        @click="filterByMetric(m.value)"
        :title="`点击筛选 ${m.label}`"
      >
        {{ m.shortLabel }}
        <em>{{ todayStats[m.value] || 0 }}</em>
      </span>
      <span class="total-hint">查询结果共 {{ signals.length }} 条</span>
    </div>

    <!-- 数据表格 -->
    <el-table
      v-loading="loading"
      :data="signals"
      stripe
      class="data-table"
      :default-sort="{ prop: 'signal_date', order: 'descending' }"
    >
      <el-table-column prop="signal_date" label="日期" width="105" sortable />
      <el-table-column prop="variety_name" label="品种" width="90" />
      <el-table-column label="指标" width="115">
        <template #default="{ row }">
          <span class="metric-tag" :class="`metric-${row.metric}`">
            {{ metricLabel(row.metric) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="方向" width="72">
        <template #default="{ row }">
          <span :class="row.direction === 'up' ? 'dir-up' : 'dir-down'">
            {{ row.direction === 'up' ? '▲ 偏高' : '▼ 偏低' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="当日值" width="95" align="right">
        <template #default="{ row }">
          <span :class="row.direction === 'up' ? 'val-up' : 'val-down'">
            {{ fmtValue(row.metric, row.current_value) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="基准均值" width="95" align="right">
        <template #default="{ row }">
          {{ fmtValue(row.metric, row.baseline_mean) }}
        </template>
      </el-table-column>
      <el-table-column label="Z-Score" width="100" align="right" sortable prop="z_score">
        <template #default="{ row }">
          <span class="z-score-cell" :class="zClass(row.z_score)">
            {{ row.z_score !== null ? row.z_score.toFixed(2) : '--' }}σ
          </span>
        </template>
      </el-table-column>
      <el-table-column label="异常描述" min-width="260" show-overflow-tooltip>
        <template #default="{ row }">
          <span class="desc-text">{{ row.description }}</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="88" fixed="right">
        <template #default="{ row }">
          <el-button
            type="danger"
            link
            :disabled="untrustingId === row.id"
            @click="confirmUntrust(row)"
          >不可信</el-button>
        </template>
      </el-table-column>
    </el-table>

    <!-- 空状态 -->
    <div class="empty-hint" v-if="!loading && signals.length === 0">
      <el-empty description="当前筛选条件下暂无异常信号" :image-size="80" />
    </div>
  </div>
</template>

<script>
import request from '@/utils/request'
import { ElMessageBox } from 'element-plus'
import { getTradingAnomalySignalsApi, untrustTradingAnomalySignalApi } from '@/api'

const METRIC_OPTIONS = [
  { value: 'change_pct',    label: '涨跌幅',   shortLabel: '涨跌幅' },
  { value: 'volume',        label: '成交量',   shortLabel: '成交量' },
  { value: 'open_interest', label: '持仓量',   shortLabel: '持仓量' },
  { value: 'main_force',    label: '大单指数', shortLabel: '大单' },
  { value: 'retail',        label: '散单指数', shortLabel: '散单' },
]

function todayISO() {
  return new Date().toISOString().slice(0, 10)
}
function daysAgoISO(n) {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toISOString().slice(0, 10)
}

export default {
  name: 'AnomalyView',
  data() {
    return {
      loading: false,
      signals: [],
      todayStats: {},
      statsDate: '',
      untrustingId: null,
      metricOptions: METRIC_OPTIONS,
      filters: {
        dateRange: [daysAgoISO(7), todayISO()],
        metric: '',
        variety_name: '',
        minZ: 0,
      },
      dateShortcuts: [
        {
          text: '今日',
          value: () => {
            const t = todayISO()
            return [t, t]
          },
        },
        {
          text: '近3天',
          value: () => [daysAgoISO(3), todayISO()],
        },
        {
          text: '近7天',
          value: () => [daysAgoISO(7), todayISO()],
        },
        {
          text: '近30天',
          value: () => [daysAgoISO(30), todayISO()],
        },
      ],
    }
  },
  computed: {
    statsLabel() {
      return this.statsDate ? `异常日 ${this.statsDate}` : '暂无异常'
    },
  },
  mounted() {
    this.fetchSignals()
  },
  methods: {
    async fetchSignals() {
      this.loading = true
      try {
        const params = {}
        if (this.filters.dateRange && this.filters.dateRange.length === 2) {
          params.date_from = this.filters.dateRange[0]
          params.date_to   = this.filters.dateRange[1]
        }
        if (this.filters.metric)       params.metric       = this.filters.metric
        if (this.filters.variety_name) params.variety_name = this.filters.variety_name
        if (this.filters.minZ > 0)     params.min_z_score  = this.filters.minZ

        const res = await request.get(getTradingAnomalySignalsApi, { params })
        if (res.code === 0) {
          this.signals    = res.data.signals || []
          this.todayStats = res.data.today_stats || {}
          this.statsDate  = res.data.stats_date || ''
        } else {
          this.$message.error(res.message || '查询失败')
        }
      } catch (err) {
        console.error('获取异常信号失败', err)
        this.$message.error('请求失败，请检查网络')
      } finally {
        this.loading = false
      }
    },
    resetFilters() {
      this.filters = {
        dateRange: [daysAgoISO(7), todayISO()],
        metric: '',
        variety_name: '',
        minZ: 0,
      }
      this.fetchSignals()
    },
    filterByMetric(metric) {
      this.filters.metric = this.filters.metric === metric ? '' : metric
      this.fetchSignals()
    },
    confirmUntrust(row) {
      ElMessageBox.confirm(
        `确定将「${row.variety_name}」的${this.metricLabel(row.metric)}信号标记为不可信？标记后不再展示。`,
        '标记不可信',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      ).then(() => this.untrustSignal(row.id)).catch(() => {})
    },
    async untrustSignal(id) {
      this.untrustingId = id
      try {
        const res = await request.post(`${untrustTradingAnomalySignalApi}/${id}/untrust`)
        if (res.code === 0) {
          this.$message.success(res.message || '已标记为不可信')
          await this.fetchSignals()
        } else {
          this.$message.error(res.message || '标记失败')
        }
      } catch (err) {
        console.error('标记不可信失败', err)
        this.$message.error('请求失败，请检查网络')
      } finally {
        this.untrustingId = null
      }
    },
    metricLabel(metric) {
      const m = METRIC_OPTIONS.find(o => o.value === metric)
      return m ? m.label : metric
    },
    fmtValue(metric, val) {
      if (val === null || val === undefined) return '--'
      if (metric === 'change_pct') return `${val.toFixed(2)}%`
      if (metric === 'main_force' || metric === 'retail') return val.toFixed(2)
      // 成交量/持仓量：整数，适当缩放显示
      if (val >= 1e8) return `${(val / 1e8).toFixed(2)}亿`
      if (val >= 1e4) return `${(val / 1e4).toFixed(2)}万`
      return Math.round(val).toLocaleString()
    },
    zClass(z) {
      if (z === null || z === undefined) return ''
      const abs = Math.abs(z)
      if (abs >= 4)   return 'z-extreme'
      if (abs >= 2.5) return 'z-warning'
      return ''
    },
  },
}
</script>

<style scoped>
.anomaly-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* ── 筛选栏 ── */
.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.tool-item {
  width: 140px;
}
.date-range {
  width: 240px;
}
.min-z-select {
  width: 130px;
}

/* ── 统计条 ── */
.stats-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  padding: 10px 14px;
  background: #f7f8fa;
  border-radius: 6px;
  font-size: 13px;
}
.stat-label {
  color: #5c5c5c;
  font-weight: 600;
  margin-right: 4px;
}
.stat-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border-radius: 12px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  border: 1px solid transparent;
  transition: opacity 0.15s;
}
.stat-chip:hover {
  opacity: 0.8;
}
.stat-chip em {
  font-style: normal;
  font-weight: 700;
}
.total-hint {
  margin-left: auto;
  color: #8a8a8a;
  font-size: 12px;
}

/* ── 指标颜色系 ── */
.metric-change_pct,
.stat-chip.metric-change_pct {
  background: #fff0f0;
  color: #c62828;
  border-color: #ffcdd2;
}
.metric-volume,
.stat-chip.metric-volume {
  background: #fff8e1;
  color: #f57f17;
  border-color: #ffe082;
}
.metric-open_interest,
.stat-chip.metric-open_interest {
  background: #f3e5f5;
  color: #7b1fa2;
  border-color: #ce93d8;
}
.metric-main_force,
.stat-chip.metric-main_force {
  background: #e8f5e9;
  color: #2e7d32;
  border-color: #a5d6a7;
}
.metric-retail,
.stat-chip.metric-retail {
  background: #e3f2fd;
  color: #1565c0;
  border-color: #90caf9;
}

/* ── 方向 ── */
.dir-up {
  color: #c62828;
  font-weight: 600;
  font-size: 12px;
}
.dir-down {
  color: #2e7d32;
  font-weight: 600;
  font-size: 12px;
}
.val-up { color: #c62828; font-weight: 600; }
.val-down { color: #2e7d32; font-weight: 600; }

/* ── Z-Score 着色 ── */
.z-score-cell {
  font-weight: 600;
  font-size: 13px;
}
.z-warning {
  color: #f57f17;
}
.z-extreme {
  color: #c62828;
}

/* ── 指标 tag ── */
.metric-tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
}

/* ── 描述文字 ── */
.desc-text {
  color: #444;
  font-size: 12px;
}

/* ── 表格 ── */
.data-table {
  width: 100%;
  border-radius: 6px;
  overflow: hidden;
}

.empty-hint {
  padding: 40px 0;
  text-align: center;
}
</style>
