<template>
  <div class="trading-page">
    <div class="info-bar">
      <el-alert
        title="操作建议仅展示池子A（12个品种）的信号，并已应用组合约束（最多3槽、板块互斥、main_score降序）。落选记录说明了具体原因。"
        type="info"
        :closable="false"
        show-icon
      />
    </div>

    <div class="toolbar">
      <el-date-picker
        v-model="filters.date"
        type="date"
        value-format="YYYY-MM-DD"
        placeholder="选择日期"
        clearable
      />
      <el-select v-model="filters.is_selected" clearable placeholder="筛选状态" class="tool-item">
        <el-option label="已选中" value="1" />
        <el-option label="落选" value="0" />
      </el-select>
      <el-input v-model="filters.variety_name" clearable placeholder="品种筛选" class="tool-item" />
      <el-button type="primary" :loading="loading" @click="fetchOperations">查询</el-button>
    </div>

    <div class="dual-pane" v-if="operations.length || loading">
      <div class="list-pane">
        <div class="pane-header">
          <div>
            <div class="pane-title">建议列表</div>
            <div class="pane-subtitle">绿色=已选中执行，灰色=落选</div>
          </div>
          <div class="count-tags">
            <el-tag type="success" size="small">选中 {{ selectedCount }}</el-tag>
            <el-tag type="info" size="small">落选 {{ rejectedCount }}</el-tag>
          </div>
        </div>

        <div v-loading="loading" class="op-list">
          <button
            v-for="op in operations"
            :key="op.id"
            type="button"
            class="op-card"
            :class="{ selected: op.is_selected, active: op.id === activeId }"
            @click="activeId = op.id"
          >
            <div class="op-top">
              <span class="op-variety">{{ op.variety_name }}</span>
              <el-tag
                size="small"
                :type="op.signal_type === 'A_OPEN_LONG' ? 'success' : 'danger'"
              >
                {{ op.signal_type === 'A_OPEN_LONG' ? '开多' : '开空' }}
              </el-tag>
            </div>
            <div class="op-sector">{{ op.sector }}</div>
            <div class="op-bottom">
              <el-tag :type="op.is_selected ? 'success' : 'info'" size="small" effect="plain">
                {{ op.is_selected ? '✓ 已选中' : ('✗ ' + rejectLabel(op.reject_reason)) }}
              </el-tag>
              <span class="op-score">
                {{ op.main_score !== null && op.main_score !== undefined
                  ? `分位 ${(op.main_score * 100).toFixed(1)}%`
                  : '分位 --' }}
              </span>
            </div>
          </button>
        </div>
      </div>

      <div class="detail-pane">
        <template v-if="activeOp">
          <div class="detail-header">
            <div class="detail-title">{{ activeOp.variety_name }}</div>
            <el-tag
              :type="activeOp.signal_type === 'A_OPEN_LONG' ? 'success' : 'danger'"
            >
              {{ activeOp.signal_type === 'A_OPEN_LONG' ? 'A-开多' : 'A-开空' }}
            </el-tag>
          </div>

          <div class="detail-grid">
            <div class="detail-item">
              <div class="detail-label">信号日期</div>
              <div class="detail-value">{{ activeOp.signal_date }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">板块</div>
              <div class="detail-value">{{ activeOp.sector }}</div>
            </div>
            <div class="detail-item">
              <div class="detail-label">动量分位分</div>
              <div class="detail-value">
                {{ activeOp.main_score !== null && activeOp.main_score !== undefined
                  ? (activeOp.main_score * 100).toFixed(1) + '%'
                  : '--（历史不足30日）' }}
              </div>
            </div>
            <div class="detail-item">
              <div class="detail-label">执行状态</div>
              <div class="detail-value" :class="activeOp.is_selected ? 'text-green' : 'text-gray'">
                {{ activeOp.is_selected ? '✓ 已选中执行' : ('✗ 落选：' + rejectLabel(activeOp.reject_reason)) }}
              </div>
            </div>
          </div>

          <div class="detail-section" v-if="!activeOp.is_selected">
            <div class="section-title">落选原因说明</div>
            <div class="reject-note">{{ rejectDetail(activeOp.reject_reason) }}</div>
          </div>

          <div class="detail-section">
            <div class="section-title">分位分说明</div>
            <div class="score-note">
              <p>动量分位分 m3 = main_force[t] - main_force[t-2]，</p>
              <p>取该品种过去30个交易日的 |m3| 历史序列，计算当前值的百分位。</p>
              <p>分位越高，代表当前主力3日动量越强。NaN 表示历史不足30日，排序时放最后但仍可被选中。</p>
            </div>
          </div>
        </template>
        <div v-else class="empty-card detail-empty">
          <el-empty description="请选择左侧一条记录查看详情" />
        </div>
      </div>
    </div>

    <div v-if="!loading && !operations.length" class="empty-card">
      <el-empty description="当前条件下没有操作建议数据" />
    </div>
  </div>
</template>

<script>
import request from '@/utils/request'
import { getTradingOperationsApi } from '@/api'

const REJECT_LABELS = {
  capacity_full: '槽位已满',
  sector_conflict: '板块冲突',
}

const REJECT_DETAILS = {
  capacity_full: '当日持仓数已达3槽上限（或含当日新开仓后），不再新增持仓。',
  sector_conflict: '该品种所在板块已有持仓（组合约束：同一板块最多1个持仓）。',
}

export default {
  name: 'TradingOperationsView',
  data() {
    return {
      loading: false,
      operations: [],
      activeId: null,
      filters: {
        date: '',
        is_selected: '',
        variety_name: ''
      }
    }
  },
  computed: {
    activeOp() {
      return this.operations.find(o => o.id === this.activeId) || this.operations[0] || null
    },
    selectedCount() {
      return this.operations.filter(o => o.is_selected).length
    },
    rejectedCount() {
      return this.operations.filter(o => !o.is_selected).length
    }
  },
  mounted() {
    this.fetchOperations()
  },
  methods: {
    async fetchOperations() {
      this.loading = true
      try {
        const res = await request.get(getTradingOperationsApi, {
          params: {
            date: this.filters.date || undefined,
            is_selected: this.filters.is_selected !== '' ? this.filters.is_selected : undefined,
            variety_name: this.filters.variety_name || undefined
          }
        })
        if (res.code === 0) {
          this.operations = res.data?.operations || []
          if (!this.filters.date && res.data?.date) {
            this.filters.date = res.data.date
          }
          if (!this.operations.find(o => o.id === this.activeId)) {
            this.activeId = this.operations[0]?.id || null
          }
        }
      } catch (error) {
        console.error('获取操作建议失败', error)
      } finally {
        this.loading = false
      }
    },
    rejectLabel(reason) {
      return REJECT_LABELS[reason] || reason || '未知'
    },
    rejectDetail(reason) {
      return REJECT_DETAILS[reason] || '暂无详细说明。'
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

.info-bar,
.empty-card {
  padding: 14px 18px;
  border-radius: 14px;
  border: 1px solid #e7edf4;
  background: #fbfdff;
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
}

.tool-item {
  width: 180px;
}

.dual-pane {
  display: grid;
  grid-template-columns: minmax(280px, 380px) minmax(0, 1fr);
  gap: 16px;
  min-height: 600px;
}

.list-pane,
.detail-pane {
  border: 1px solid #e7edf4;
  border-radius: 20px;
  background: #fff;
}

.list-pane {
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.detail-pane {
  padding: 20px;
}

.pane-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 14px;
}

.pane-title {
  font-size: 16px;
  font-weight: 700;
  color: #16324a;
}

.pane-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: #7f90a3;
}

.count-tags {
  display: flex;
  gap: 6px;
}

.op-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.op-card {
  width: 100%;
  padding: 14px;
  border: 1px solid #e7edf4;
  border-radius: 14px;
  background: #f8fafc;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
}

.op-card.selected {
  background: linear-gradient(180deg, #f0fbf5 0%, #fff 100%);
  border-color: #6ac48a;
}

.op-card.active,
.op-card:hover {
  border-color: #7aa7d9;
  box-shadow: 0 6px 18px rgba(57, 103, 159, 0.12);
  transform: translateY(-1px);
}

.op-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.op-variety {
  font-size: 17px;
  font-weight: 700;
  color: #17324b;
}

.op-sector {
  margin-top: 5px;
  font-size: 12px;
  color: #688095;
}

.op-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.op-score {
  font-size: 12px;
  color: #1e5077;
  font-weight: 600;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.detail-title {
  font-size: 24px;
  font-weight: 700;
  color: #16324a;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 18px;
}

.detail-item {
  padding: 14px 16px;
  border-radius: 14px;
  background: #f7fbff;
  border: 1px solid #e6eef7;
}

.detail-label {
  font-size: 12px;
  color: #74879a;
  font-weight: 600;
}

.detail-value {
  margin-top: 8px;
  font-size: 16px;
  font-weight: 600;
  color: #16324a;
}

.text-green {
  color: #1e8e5a;
}

.text-gray {
  color: #8a99aa;
}

.detail-section {
  padding: 16px;
  border-radius: 14px;
  border: 1px solid #e8eef5;
  margin-bottom: 12px;
}

.section-title {
  font-size: 14px;
  font-weight: 700;
  color: #243447;
  margin-bottom: 10px;
}

.reject-note,
.score-note {
  font-size: 13px;
  color: #52667c;
  line-height: 1.75;
}

.score-note p {
  margin: 0 0 4px;
}

.detail-empty {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 1100px) {
  .dual-pane {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .toolbar {
    flex-direction: column;
    align-items: stretch;
  }
  .tool-item {
    width: 100%;
  }
  .detail-grid {
    grid-template-columns: 1fr;
  }
}
</style>
