<template>
  <div class="trading-page">
    <div class="note-bar">
      操作建议仅展示池子 A（12 个品种）的信号，并已应用组合约束（最多 3 槽、板块互斥、main_score 降序）。落选记录说明了具体原因。
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
      <el-button :loading="loading" @click="fetchOperations">查询</el-button>
    </div>

    <div class="dual-pane" v-if="operations.length || loading">
      <div class="list-pane">
        <div class="pane-header">
          <div class="pane-header-main">
            <div class="pane-title">建议列表</div>
            <div class="pane-subtitle">浅底加左边线=当前聚焦；与「开多/开空」颜色无关</div>
          </div>
          <div class="count-tags">
            <span class="count-pill">选中 {{ selectedCount }}</span>
            <span class="count-pill count-pill-muted">落选 {{ rejectedCount }}</span>
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
              <span
                class="op-dir"
                :class="op.signal_type === 'A_OPEN_LONG' ? 'dir-long' : 'dir-short'"
              >
                {{ op.signal_type === 'A_OPEN_LONG' ? '开多' : '开空' }}
              </span>
            </div>
            <div class="op-sector">{{ op.sector }}</div>
            <div class="op-bottom">
              <span class="op-status" :class="op.is_selected ? 'status-on' : 'status-off'">
                {{ op.is_selected ? '已选中执行' : ('落选：' + rejectLabel(op.reject_reason)) }}
              </span>
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
            <span
              class="detail-dir"
              :class="activeOp.signal_type === 'A_OPEN_LONG' ? 'dir-long' : 'dir-short'"
            >
              {{ activeOp.signal_type === 'A_OPEN_LONG' ? 'A-开多' : 'A-开空' }}
            </span>
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
              <div class="detail-value" :class="activeOp.is_selected ? 'state-ok' : 'state-muted'">
                {{ activeOp.is_selected ? '已选中执行' : ('落选：' + rejectLabel(activeOp.reject_reason)) }}
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

.note-bar {
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  background: #fafafa;
  font-size: 13px;
  line-height: 1.6;
  color: #5c5c5c;
}

.empty-card {
  padding: 14px 18px;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  background: #fafafa;
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
  border: 1px solid #e0e0e0;
  border-radius: 8px;
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
  gap: 20px;
  margin-bottom: 14px;
}

.pane-header-main {
  flex: 1;
  min-width: 0;
}

.pane-title {
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
}

.pane-subtitle {
  margin-top: 4px;
  font-size: 12px;
  color: #8a8a8a;
  line-height: 1.5;
}

.count-tags {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  flex-shrink: 0;
}

.count-pill {
  font-size: 12px;
  color: #1a1a1a;
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
  background: #fafafa;
  white-space: nowrap;
}

.count-pill-muted {
  color: #8a8a8a;
  background: #fff;
}

.op-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.op-card {
  width: 100%;
  padding: 14px;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #fafafa;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.15s ease, background-color 0.15s ease;
}

.op-card.selected {
  background: #f0f0f0;
  border-color: #bdbdbd;
}

.op-card.active {
  border-left: 3px solid #1a1a1a;
  padding-left: 11px;
  background: #fff;
}

.op-card:hover {
  border-color: #bdbdbd;
}

.op-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.op-variety {
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.op-dir {
  font-size: 12px;
  font-weight: 600;
}

.op-dir.dir-long {
  color: #c62828;
}

.op-dir.dir-short {
  color: #2e7d32;
}

.op-sector {
  margin-top: 5px;
  font-size: 12px;
  color: #8a8a8a;
}

.op-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 10px;
}

.op-status {
  font-size: 12px;
  font-weight: 500;
}

.op-status.status-on {
  color: #1a1a1a;
}

.op-status.status-off {
  color: #8a8a8a;
}

.op-score {
  font-size: 12px;
  color: #5c5c5c;
  font-weight: 500;
}

.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.detail-title {
  font-size: 20px;
  font-weight: 600;
  color: #1a1a1a;
}

.detail-dir {
  font-size: 13px;
  font-weight: 600;
}

.detail-dir.dir-long {
  color: #c62828;
}

.detail-dir.dir-short {
  color: #2e7d32;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 18px;
}

.detail-item {
  padding: 14px 16px;
  border-radius: 8px;
  background: #fafafa;
  border: 1px solid #e0e0e0;
}

.detail-label {
  font-size: 12px;
  color: #8a8a8a;
  font-weight: 600;
}

.detail-value {
  margin-top: 8px;
  font-size: 15px;
  font-weight: 600;
  color: #1a1a1a;
}

.state-ok {
  color: #1a1a1a;
}

.state-muted {
  color: #8a8a8a;
}

.detail-section {
  padding: 16px;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  margin-bottom: 12px;
  background: #fff;
}

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 10px;
}

.reject-note,
.score-note {
  font-size: 13px;
  color: #5c5c5c;
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
