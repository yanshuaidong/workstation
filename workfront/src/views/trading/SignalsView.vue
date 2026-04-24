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
      <el-select v-model="filters.signal_type" clearable placeholder="信号类型" class="tool-item">
        <el-option label="A_OPEN_LONG（开多）" value="A_OPEN_LONG" />
        <el-option label="A_OPEN_SHORT（开空）" value="A_OPEN_SHORT" />
        <el-option label="A_CLOSE_LONG（平多）" value="A_CLOSE_LONG" />
        <el-option label="A_CLOSE_SHORT（平空）" value="A_CLOSE_SHORT" />
      </el-select>
      <el-input v-model="filters.variety_name" clearable placeholder="品种筛选" class="tool-item" />
      <el-button type="primary" :loading="loading" @click="fetchSignals">查询</el-button>
    </div>

    <div class="stats-row" v-if="!loading && signals.length">
      <el-tag type="success">开多 {{ countByType('A_OPEN_LONG') }}</el-tag>
      <el-tag type="danger">开空 {{ countByType('A_OPEN_SHORT') }}</el-tag>
      <el-tag type="warning">平多 {{ countByType('A_CLOSE_LONG') }}</el-tag>
      <el-tag>平空 {{ countByType('A_CLOSE_SHORT') }}</el-tag>
      <span class="total-hint">共 {{ signals.length }} 条</span>
    </div>

    <el-table v-loading="loading" :data="signals" stripe class="data-table">
      <el-table-column prop="signal_date" label="日期" width="120" />
      <el-table-column prop="variety_name" label="品种" min-width="100" />
      <el-table-column label="信号类型" min-width="150">
        <template #default="{ row }">
          <el-tag :type="getSignalTagType(row.signal_type)" size="small">
            {{ getSignalLabel(row.signal_type) }}
          </el-tag>
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
import request from '@/utils/request'
import { getTradingSignalsApi } from '@/api'

const SIGNAL_META = {
  A_OPEN_LONG: { label: 'A-开多', type: 'success' },
  A_OPEN_SHORT: { label: 'A-开空', type: 'danger' },
  A_CLOSE_LONG: { label: 'A-平多', type: 'warning' },
  A_CLOSE_SHORT: { label: 'A-平空', type: 'info' },
}

export default {
  name: 'TradingSignalsView',
  data() {
    return {
      loading: false,
      signals: [],
      filters: {
        date: '',
        signal_type: '',
        variety_name: ''
      }
    }
  },
  mounted() {
    this.fetchSignals()
  },
  methods: {
    async fetchSignals() {
      this.loading = true
      try {
        const res = await request.get(getTradingSignalsApi, {
          params: {
            date: this.filters.date || undefined,
            signal_type: this.filters.signal_type || undefined,
            variety_name: this.filters.variety_name || undefined
          }
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
    getSignalLabel(type) {
      return SIGNAL_META[type]?.label || type
    },
    getSignalTagType(type) {
      return SIGNAL_META[type]?.type || 'info'
    },
    countByType(type) {
      return this.signals.filter(s => s.signal_type === type).length
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

.tool-item {
  width: 200px;
}

.stats-row {
  display: flex;
  gap: 10px;
  align-items: center;
  flex-wrap: wrap;
}

.total-hint {
  color: #8a98a8;
  font-size: 13px;
}

.empty-card {
  padding: 18px 20px;
  border-radius: 16px;
  border: 1px solid #e7edf4;
  background: #fbfdff;
}

.data-table {
  width: 100%;
}

.dim {
  color: #bbb;
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .tool-item {
    width: 100%;
  }
}
</style>
