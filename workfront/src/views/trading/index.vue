<template>
  <div class="trading-layout">
    <div class="summary-card">
      <div class="summary-label">自动化账户</div>
      <div class="summary-equity">{{ formatNumber(summary.equity) }}</div>
      <div class="summary-meta">净值日期 {{ summary.record_date || '--' }}</div>
      <div class="summary-inline">
        <span>持仓 {{ summary.open_positions || 0 }} / 3</span>
        <span :class="summary.daily_pnl >= 0 ? 'pnl-pos' : 'pnl-neg'">
          当日盈亏 {{ formatSigned(summary.daily_pnl) }}
        </span>
      </div>
    </div>

    <div class="tabs-panel">
      <el-tabs :model-value="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="信号面板" name="/trading/signals" />
        <el-tab-pane label="操作建议" name="/trading/operations" />
        <el-tab-pane label="持仓盈亏" name="/trading/positions" />
        <el-tab-pane label="资金曲线" name="/trading/curve" />
        <el-tab-pane label="K线展示" name="/trading/kline" />
        <el-tab-pane label="池子管理" name="/trading/pool" />
      </el-tabs>
      <router-view />
    </div>
  </div>
</template>

<script>
import request from '@/utils/request'
import { getTradingAccountSummaryApi } from '@/api'

const defaultSummary = {
  record_date: null,
  equity: 30000,
  cash: 30000,
  position_val: 0,
  daily_pnl: 0,
  open_positions: 0
}

export default {
  name: 'TradingLayout',
  provide() {
    return {
      refreshAccountSummary: () => this.fetchSummary()
    }
  },
  data() {
    return {
      summary: { ...defaultSummary }
    }
  },
  computed: {
    activeTab() {
      return this.$route.path
    }
  },
  mounted() {
    this.fetchSummary()
  },
  methods: {
    async fetchSummary() {
      try {
        const res = await request.get(getTradingAccountSummaryApi)
        if (res.code === 0 && res.data?.summary) {
          this.summary = { ...defaultSummary, ...res.data.summary }
        }
      } catch (error) {
        console.error('获取账户摘要失败', error)
      }
    },
    handleTabChange(path) {
      if (path && path !== this.$route.path) {
        this.$router.push(path)
      }
    },
    formatNumber(value) {
      return Number(value || 0).toFixed(2)
    },
    formatSigned(value) {
      const num = Number(value || 0)
      return `${num >= 0 ? '+' : ''}${num.toFixed(2)}`
    }
  }
}
</script>

<style scoped>
.trading-layout {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.summary-card {
  padding: 20px 22px;
  border-radius: 8px;
  background: #ffffff;
  border: 1px solid #e0e0e0;
  box-shadow: none;
}

.summary-label {
  color: #5c5c5c;
  font-size: 13px;
  font-weight: 600;
}

.summary-equity {
  margin-top: 10px;
  color: #1a1a1a;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.summary-meta {
  margin-top: 6px;
  color: #8a8a8a;
  font-size: 12px;
}

.summary-inline {
  display: flex;
  gap: 20px;
  margin-top: 14px;
  color: #1a1a1a;
  font-size: 13px;
}

/* 盈亏：国内期货常见着色（盈红亏绿） */
.pnl-pos {
  color: #c62828;
  font-weight: 600;
}

.pnl-neg {
  color: #2e7d32;
  font-weight: 600;
}

.tabs-panel {
  padding: 12px 0 0;
  border-radius: 8px;
  background: transparent;
  border: none;
}

.tabs-panel :deep(.el-tabs__header) {
  margin: 0 0 16px;
  border-bottom: 1px solid #e0e0e0;
}

.tabs-panel :deep(.el-tabs__nav-wrap::after) {
  display: none;
}

.tabs-panel :deep(.el-tabs__item) {
  color: #5c5c5c;
  font-weight: 500;
  font-size: 13px;
}

.tabs-panel :deep(.el-tabs__item.is-active) {
  color: #1a1a1a;
  font-weight: 600;
}

.tabs-panel :deep(.el-tabs__active-bar) {
  background-color: #1a1a1a;
  height: 2px;
}
</style>
