<template>
  <div class="assistant-layout">
    <div class="hero-panel">
      <div class="hero-copy">
        <div class="hero-eyebrow">Assistant</div>
        <h2 class="hero-title">辅助决策中心</h2>
        <p class="hero-desc">把每日信号、机械建议、双账户持仓和资金曲线放到同一条工作流里。</p>
      </div>
      <el-button type="primary" class="refresh-btn" :loading="summaryLoading" @click="fetchSummary">
        刷新摘要
      </el-button>
    </div>

    <div class="summary-grid">
      <div class="summary-card">
        <div class="summary-label">机械账户</div>
        <div class="summary-equity">{{ formatNumber(summary.mechanical.equity) }}</div>
        <div class="summary-meta">净值日期 {{ summary.mechanical.record_date || '--' }}</div>
        <div class="summary-inline">
          <span>持仓 {{ summary.mechanical.open_positions || 0 }}</span>
          <span>当日盈亏 {{ formatSigned(summary.mechanical.daily_pnl) }}</span>
        </div>
      </div>
      <div class="summary-card llm-card">
        <div class="summary-label">LLM 账户</div>
        <div class="summary-equity">{{ formatNumber(summary.llm.equity) }}</div>
        <div class="summary-meta">净值日期 {{ summary.llm.record_date || '--' }}</div>
        <div class="summary-inline">
          <span>持仓 {{ summary.llm.open_positions || 0 }}</span>
          <span>当日盈亏 {{ formatSigned(summary.llm.daily_pnl) }}</span>
        </div>
      </div>
    </div>

    <div class="tabs-panel">
      <el-tabs :model-value="activeTab" @tab-change="handleTabChange">
        <el-tab-pane label="信号面板" name="/assistant/signals" />
        <el-tab-pane label="操作建议" name="/assistant/operations" />
        <el-tab-pane label="持仓盈亏" name="/assistant/positions" />
        <el-tab-pane label="资金曲线" name="/assistant/curve" />
        <el-tab-pane label="K线展示" name="/assistant/kline" />
      </el-tabs>
      <router-view />
    </div>
  </div>
</template>

<script>
import request from '@/utils/request'
import { getAssistantAccountSummaryApi } from '@/api'

const defaultSummary = {
  record_date: null,
  equity: 30000,
  cash: 30000,
  position_val: 0,
  daily_pnl: 0,
  open_positions: 0
}

export default {
  name: 'AssistantLayout',
  data() {
    return {
      summaryLoading: false,
      summary: {
        mechanical: { ...defaultSummary },
        llm: { ...defaultSummary }
      }
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
      this.summaryLoading = true
      try {
        const res = await request.get(getAssistantAccountSummaryApi)
        if (res.code === 0 && res.data?.summary) {
          this.summary = {
            mechanical: { ...defaultSummary, ...(res.data.summary.mechanical || {}) },
            llm: { ...defaultSummary, ...(res.data.summary.llm || {}) }
          }
        }
      } catch (error) {
        console.error('获取账户摘要失败', error)
      } finally {
        this.summaryLoading = false
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
.assistant-layout {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.hero-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20px;
  padding: 24px 28px;
  border-radius: 22px;
  background:
    radial-gradient(circle at top left, rgba(73, 128, 255, 0.18), transparent 36%),
    linear-gradient(135deg, #132840 0%, #1c4665 55%, #285e77 100%);
  color: #fff;
}

.hero-eyebrow {
  margin-bottom: 8px;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  opacity: 0.72;
}

.hero-title {
  margin: 0 0 8px;
  font-size: 30px;
  font-weight: 700;
}

.hero-desc {
  margin: 0;
  max-width: 520px;
  color: rgba(255, 255, 255, 0.82);
  line-height: 1.6;
}

.refresh-btn {
  flex-shrink: 0;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
}

.summary-card {
  padding: 20px 22px;
  border-radius: 18px;
  background: #fff;
  border: 1px solid #e6edf5;
  box-shadow: 0 12px 30px rgba(15, 36, 63, 0.06);
}

.llm-card {
  background: linear-gradient(180deg, #fff8ef 0%, #ffffff 100%);
}

.summary-label {
  color: #627387;
  font-size: 13px;
  font-weight: 600;
}

.summary-equity {
  margin-top: 10px;
  color: #18324a;
  font-size: 30px;
  font-weight: 700;
}

.summary-meta {
  margin-top: 6px;
  color: #91a1b2;
  font-size: 12px;
}

.summary-inline {
  display: flex;
  gap: 18px;
  margin-top: 14px;
  color: #3c5168;
  font-size: 13px;
}

.tabs-panel {
  padding: 20px 22px 24px;
  border-radius: 20px;
  background: #fff;
  border: 1px solid #e7edf5;
}

@media (max-width: 900px) {
  .hero-panel {
    flex-direction: column;
    align-items: flex-start;
  }

  .summary-grid {
    grid-template-columns: 1fr;
  }

  .summary-inline {
    flex-direction: column;
    gap: 6px;
  }
}
</style>

