<template>
  <div class="trading-page">
    <div class="toolbar">
      <el-button :loading="loading || histLoading" @click="fetchAll">刷新</el-button>
    </div>

    <div class="section-title">当前持仓（最多3槽）</div>
    <el-table v-loading="loading" :data="positions" stripe class="data-table">
      <el-table-column prop="variety_name" label="品种" min-width="90" />
      <el-table-column prop="sector" label="板块" min-width="100" />
      <el-table-column label="方向" width="90">
        <template #default="{ row }">
          <span :class="row.direction === 'LONG' ? 'dir-long' : 'dir-short'">
            {{ directionLabel(row.direction) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="open_date" label="开仓日" width="115" />
      <el-table-column prop="open_price" label="入场价" width="100" />
      <el-table-column label="当前价" width="100">
        <template #default="{ row }">
          {{ row.current_price !== null ? row.current_price : '--' }}
        </template>
      </el-table-column>
      <el-table-column label="浮盈浮亏（含10x杠杆）" min-width="200">
        <template #default="{ row }">
          <span :class="Number(row.floating_pnl_amount || 0) >= 0 ? 'pnl-pos' : 'pnl-neg'">
            {{ formatSigned(row.floating_pnl_amount) }} 元 /
            {{ formatSigned(row.floating_pnl_pct) }}%
          </span>
        </template>
      </el-table-column>
      <el-table-column label="主力" width="80">
        <template #default="{ row }">
          <span :class="row.main_force > 0 ? 'pos' : row.main_force < 0 ? 'neg' : ''">
            {{ row.main_force !== null ? row.main_force.toFixed(2) : '--' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="latest_trade_date" label="数据日期" width="115" />
    </el-table>

    <div v-if="!loading && !positions.length" class="empty-hint">当前无持仓</div>

    <div class="section-title" style="margin-top: 8px">历史持仓（最近100条）</div>
    <el-table v-loading="histLoading" :data="history" stripe class="data-table">
      <el-table-column prop="variety_name" label="品种" min-width="90" />
      <el-table-column prop="sector" label="板块" min-width="100" />
      <el-table-column label="方向" width="90">
        <template #default="{ row }">
          <span :class="row.direction === 'LONG' ? 'dir-long' : 'dir-short'">
            {{ directionLabel(row.direction) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="open_date" label="开仓日" width="115" />
      <el-table-column prop="close_date" label="平仓日" width="115" />
      <el-table-column label="无杠杆收益率" width="130">
        <template #default="{ row }">
          <span v-if="row.pnl_pct !== null" :class="Number(row.pnl_pct) >= 0 ? 'pnl-pos' : 'pnl-neg'">
            {{ formatSigned(row.pnl_pct * 100) }}%
          </span>
          <span v-else class="dim">--</span>
        </template>
      </el-table-column>
      <el-table-column prop="open_price" label="入场价" width="100" />
      <el-table-column prop="close_price" label="出场价" width="100" />
    </el-table>
  </div>
</template>

<script>
import request from '@/utils/request'
import { getTradingPositionsApi, getTradingPositionsHistoryApi } from '@/api'

export default {
  name: 'TradingPositionsView',
  inject: {
    refreshAccountSummary: { default: null }
  },
  data() {
    return {
      loading: false,
      histLoading: false,
      positions: [],
      history: []
    }
  },
  mounted() {
    this.fetchAll()
  },
  methods: {
    async fetchAll() {
      this.loading = true
      this.histLoading = true
      try {
        const [posRes, histRes] = await Promise.all([
          request.get(getTradingPositionsApi),
          request.get(getTradingPositionsHistoryApi, { params: { limit: 100 } })
        ])
        if (posRes.code === 0) {
          this.positions = posRes.data?.positions || []
        }
        if (histRes.code === 0) {
          this.history = histRes.data?.history || []
        }
        if (this.refreshAccountSummary) {
          this.refreshAccountSummary()
        }
      } catch (error) {
        console.error('获取持仓数据失败', error)
      } finally {
        this.loading = false
        this.histLoading = false
      }
    },
    formatSigned(value) {
      const num = Number(value || 0)
      return `${num >= 0 ? '+' : ''}${num.toFixed(2)}`
    },
    directionLabel(direction) {
      if (direction === 'LONG') return '多'
      if (direction === 'SHORT') return '空'
      return direction ?? '--'
    }
  }
}
</script>

<style scoped>
.trading-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.section-title {
  color: #1a1a1a;
  font-size: 14px;
  font-weight: 600;
}

.data-table {
  width: 100%;
}

.empty-hint {
  padding: 20px 0;
  color: #8a8a8a;
  font-size: 13px;
}

.dir-long {
  color: #c62828;
  font-weight: 600;
  font-size: 12px;
}

.dir-short {
  color: #2e7d32;
  font-weight: 600;
  font-size: 12px;
}

/* 浮盈与主力指数：红正绿负（涨/多方向为正时用红） */
.pnl-pos {
  color: #c62828;
  font-weight: 600;
}

.pnl-neg {
  color: #2e7d32;
  font-weight: 600;
}

.pos {
  color: #c62828;
}

.neg {
  color: #2e7d32;
}

.dim {
  color: #b0b0b0;
}
</style>
