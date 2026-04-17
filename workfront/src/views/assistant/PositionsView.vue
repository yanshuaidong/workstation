<template>
  <div class="assistant-page">
    <div class="toolbar">
      <el-select v-model="accountType" class="tool-item" @change="fetchAll">
        <el-option label="全部账户" value="" />
        <el-option label="mechanical" value="mechanical" />
        <el-option label="llm" value="llm" />
      </el-select>
      <el-button type="primary" :loading="loading" @click="fetchAll">刷新</el-button>
    </div>

    <div class="section-title">当前持仓</div>
    <el-table v-loading="loading" :data="positions" stripe class="data-table">
      <el-table-column prop="account_type" label="账户" width="110" />
      <el-table-column prop="variety_name" label="品种" min-width="100" />
      <el-table-column label="方向" width="100">
        <template #default="{ row }">
          <el-tag :type="row.direction === 'LONG' ? 'success' : 'danger'">{{ row.direction }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="open_date" label="开仓日" width="120" />
      <el-table-column prop="open_price" label="入场价" width="110" />
      <el-table-column prop="current_price" label="当前价" width="110" />
      <el-table-column label="浮盈浮亏" min-width="170">
        <template #default="{ row }">
          <span :class="Number(row.floating_pnl_amount || 0) >= 0 ? 'pnl-positive' : 'pnl-negative'">
            {{ formatSigned(row.floating_pnl_amount) }} / {{ formatSigned(row.floating_pnl_pct) }}%
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="holding_days" label="持有天数" width="110" />
      <el-table-column prop="remaining_days" label="剩余天数" width="110" />
      <el-table-column prop="strategy" label="来源策略" min-width="130" />
    </el-table>

    <div class="section-title">最近历史持仓</div>
    <el-table v-loading="historyLoading" :data="history" stripe class="data-table">
      <el-table-column prop="account_type" label="账户" width="110" />
      <el-table-column prop="variety_name" label="品种" min-width="100" />
      <el-table-column prop="direction" label="方向" width="100" />
      <el-table-column prop="open_date" label="开仓日" width="120" />
      <el-table-column prop="close_date" label="平仓日" width="120" />
      <el-table-column label="收益率" width="120">
        <template #default="{ row }">
          <span :class="Number(row.pnl_pct || 0) >= 0 ? 'pnl-positive' : 'pnl-negative'">
            {{ formatSigned(row.pnl_pct) }}%
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="strategy" label="策略" min-width="120" />
    </el-table>
  </div>
</template>

<script>
import request from '@/utils/request'
import { getAssistantPositionsApi, getAssistantPositionsHistoryApi } from '@/api'

export default {
  name: 'AssistantPositionsView',
  data() {
    return {
      loading: false,
      historyLoading: false,
      accountType: '',
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
      this.historyLoading = true
      try {
        const [positionsRes, historyRes] = await Promise.all([
          request.get(getAssistantPositionsApi, {
            params: {
              account_type: this.accountType || undefined
            }
          }),
          request.get(getAssistantPositionsHistoryApi, {
            params: {
              account_type: this.accountType || undefined,
              limit: 50
            }
          })
        ])
        if (positionsRes.code === 0) {
          this.positions = positionsRes.data?.positions || []
        }
        if (historyRes.code === 0) {
          this.history = historyRes.data?.history || []
        }
      } catch (error) {
        console.error('获取持仓数据失败', error)
      } finally {
        this.loading = false
        this.historyLoading = false
      }
    },
    formatSigned(value) {
      const num = Number(value || 0)
      return `${num >= 0 ? '+' : ''}${num.toFixed(2)}`
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
  gap: 12px;
  align-items: center;
}

.tool-item {
  width: 180px;
}

.section-title {
  color: #243447;
  font-size: 15px;
  font-weight: 700;
}

.pnl-positive {
  color: #1e8e5a;
}

.pnl-negative {
  color: #d14343;
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

