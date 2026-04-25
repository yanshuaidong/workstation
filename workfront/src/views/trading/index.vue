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
  gap: 18px;
}

.summary-card {
  padding: 20px 24px;
  border-radius: 18px;
  background: linear-gradient(135deg, #f0f7ff 0%, #ffffff 100%);
  border: 1px solid #d6e8f8;
  box-shadow: 0 12px 30px rgba(15, 36, 63, 0.06);
}

.summary-label {
  color: #5a7896;
  font-size: 13px;
  font-weight: 600;
}

.summary-equity {
  margin-top: 10px;
  color: #18324a;
  font-size: 32px;
  font-weight: 700;
}

.summary-meta {
  margin-top: 6px;
  color: #91a1b2;
  font-size: 12px;
}

.summary-inline {
  display: flex;
  gap: 20px;
  margin-top: 14px;
  color: #3c5168;
  font-size: 13px;
}

.pnl-pos {
  color: #1e8e5a;
}

.pnl-neg {
  color: #d14343;
}

.tabs-panel {
  padding: 20px 22px 24px;
  border-radius: 20px;
  background: #fff;
  border: 1px solid #e7edf5;
}
</style>
