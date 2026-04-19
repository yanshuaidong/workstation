<template>
  <div class="assistant-page">
    <div class="toolbar-card">
      <el-alert
        title="这些建议来自机械规则归纳，不是收益承诺。综合分主要用于当前页面内排序，不建议跨策略、跨指标直接硬比较。"
        type="info"
        :closable="false"
        show-icon
      />

      <div class="toolbar">
        <el-date-picker
          v-model="filters.date"
          type="date"
          value-format="YYYY-MM-DD"
          placeholder="选择日期"
          clearable
        />
        <el-select v-model="filters.account_type" placeholder="账户类型" class="tool-item">
          <el-option label="机械规则账户" value="mechanical" />
          <el-option label="LLM 账户" value="llm" />
        </el-select>
        <el-select v-model="filters.direction" clearable placeholder="方向" class="tool-item">
          <el-option label="偏多 LONG" value="LONG" />
          <el-option label="偏空 SHORT" value="SHORT" />
        </el-select>
        <el-input v-model="filters.variety_name" clearable placeholder="品种筛选" class="tool-item" />
        <el-button type="primary" :loading="loading" @click="fetchOperations">查询</el-button>
      </div>
    </div>

    <div v-if="!loading && !sortedOperations.length" class="empty-state-card">
      <el-empty description="当前筛选条件下没有操作建议。" />
    </div>

    <div v-else class="dual-pane">
      <div class="list-pane">
        <div class="pane-header">
          <div>
            <div class="pane-title">建议列表</div>
            <div class="pane-subtitle">先看左侧排序，再在右侧读完整链路</div>
          </div>
          <el-tag type="info">共 {{ sortedOperations.length }} 条</el-tag>
        </div>

        <div v-loading="loading" class="operation-list">
          <button
            v-for="operation in sortedOperations"
            :key="operation.id"
            type="button"
            class="operation-card"
            :class="{ active: operation.id === selectedOperationId }"
            @click="selectOperation(operation)"
          >
            <div class="operation-card-top">
              <div>
                <div class="operation-variety">{{ operation.variety_name || '--' }}</div>
                <div class="operation-strategy">
                  {{ operation.strategy_meta?.label_cn || operation.strategy_label || operation.strategy }}
                </div>
              </div>
              <el-tag size="small" :type="operation.direction === 'LONG' ? 'success' : 'danger'">
                {{ getDirectionLabel(operation.direction) }}
              </el-tag>
            </div>

            <div class="operation-action-row">
              <el-tag effect="dark" :type="getActionTagType(operation.action_advice?.label)">
                {{ operation.action_advice?.label || '继续观察' }}
              </el-tag>
              <span class="operation-score">{{ formatScore(operation.composite_score) }}</span>
            </div>

            <div class="operation-summary">
              {{ operation.summary || '当前接口尚未返回摘要。' }}
            </div>

            <div class="operation-meta">
              <span>{{ operation.signal_date || '--' }}</span>
              <span>{{ operation.score_explanation?.score_text || '综合分用于同页排序' }}</span>
            </div>
          </button>
        </div>
      </div>

      <div class="detail-pane" v-loading="loading">
        <template v-if="selectedOperation">
          <div class="detail-hero">
            <div class="detail-eyebrow">当前选中建议</div>
            <div class="detail-title-row">
              <div>
                <div class="detail-title">
                  {{ selectedOperation.variety_name || '--' }} ·
                  {{ selectedOperation.strategy_meta?.label_cn || selectedOperation.strategy_label || selectedOperation.strategy }}
                </div>
                <div class="detail-subtitle">
                  {{ selectedOperation.strategy_meta?.thesis || '当前策略意图暂无说明。' }}
                </div>
              </div>
              <el-tag size="large" :type="selectedOperation.direction === 'LONG' ? 'success' : 'danger'">
                {{ getDirectionLabel(selectedOperation.direction) }}
              </el-tag>
            </div>

            <div class="hero-grid">
              <div class="hero-metric action">
                <div class="hero-label">建议动作</div>
                <div class="hero-value">{{ selectedOperation.action_advice?.label || '继续观察' }}</div>
                <div class="hero-note">{{ selectedOperation.action_advice?.reason || '--' }}</div>
              </div>
              <div class="hero-metric score">
                <div class="hero-label">综合分</div>
                <div class="hero-value">{{ Number(selectedOperation.composite_score || 0).toFixed(2) }}</div>
                <div class="hero-note">{{ selectedOperation.score_explanation?.usage_tip || '--' }}</div>
              </div>
              <div class="hero-metric status">
                <div class="hero-label">执行状态</div>
                <div class="hero-value">{{ selectedOperation.executed ? '已执行' : '未执行' }}</div>
                <div class="hero-note">日期 {{ selectedOperation.signal_date || '--' }}</div>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <div class="section-heading">1. 为什么会触发这条建议</div>
            <div class="section-summary">
              {{ selectedOperation.summary || '当前接口尚未返回摘要。' }}
            </div>
            <div class="trigger-grid">
              <div
                v-for="item in selectedOperation.trigger_explanations || []"
                :key="`${selectedOperation.id}-${item.indicator}`"
                class="trigger-card"
              >
                <div class="trigger-label">{{ item.label_cn }}</div>
                <div class="trigger-value">{{ item.value_cn }}</div>
                <div class="trigger-meaning">{{ item.meaning }}</div>
                <div class="trigger-read">{{ item.how_to_read }}</div>
              </div>
            </div>
          </div>

          <div class="detail-section">
            <div class="section-heading">2. 当前更适合怎么做</div>
            <div class="decision-card">
              <div class="decision-title">{{ selectedOperation.action_advice?.label || '继续观察' }}</div>
              <div class="decision-body">{{ selectedOperation.action_advice?.reason || '--' }}</div>
            </div>
          </div>

          <div class="detail-section">
            <div class="section-heading">3. 综合分应该怎么看</div>
            <div class="score-panel">
              <div class="score-line">{{ selectedOperation.score_explanation?.score_text || '--' }}</div>
              <div class="score-line">{{ selectedOperation.score_explanation?.usage_tip || '--' }}</div>
              <div class="score-line">{{ selectedOperation.score_explanation?.threshold_tip || '--' }}</div>
            </div>
          </div>

          <div class="detail-section">
            <div class="section-heading">4. 风险提醒</div>
            <div class="risk-card">
              {{ selectedOperation.risk_note || '当前没有额外风险提示。' }}
            </div>
          </div>

          <div class="detail-section">
            <div class="section-heading">5. 规则出处</div>
            <div class="source-grid">
              <div class="source-item">
                <div class="source-label">策略代号</div>
                <div class="source-value">{{ selectedOperation.strategy_meta?.code || selectedOperation.strategy }}</div>
              </div>
              <div class="source-item">
                <div class="source-label">策略中文名</div>
                <div class="source-value">
                  {{ selectedOperation.strategy_meta?.label_cn || selectedOperation.strategy_label || '--' }}
                </div>
              </div>
              <div class="source-item">
                <div class="source-label">账户类型</div>
                <div class="source-value">{{ getAccountTypeLabel(selectedOperation.account_type) }}</div>
              </div>
              <div class="source-item">
                <div class="source-label">原始触发条件</div>
                <div class="source-value source-list">
                  <span
                    v-for="(value, key) in selectedOperation.trigger_indicators || {}"
                    :key="`${selectedOperation.id}-${key}`"
                    class="source-chip"
                  >
                    {{ key }}={{ value }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </template>

        <div v-else class="empty-state-card detail-empty">
          <el-empty description="请选择左侧一条建议查看详情。" />
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import request from '@/utils/request'
import { getAssistantOperationsApi } from '@/api'

export default {
  name: 'AssistantOperationsView',
  data() {
    return {
      loading: false,
      operations: [],
      selectedOperationId: null,
      filters: {
        date: '',
        account_type: 'mechanical',
        direction: '',
        variety_name: ''
      }
    }
  },
  computed: {
    sortedOperations() {
      return [...this.operations].sort((left, right) => {
        const scoreDiff = Number(right.composite_score || 0) - Number(left.composite_score || 0)
        if (scoreDiff !== 0) {
          return scoreDiff
        }
        return String(left.variety_name || '').localeCompare(String(right.variety_name || ''), 'zh-Hans-CN')
      })
    },
    selectedOperation() {
      return this.sortedOperations.find(item => item.id === this.selectedOperationId) || this.sortedOperations[0] || null
    }
  },
  mounted() {
    this.fetchOperations()
  },
  methods: {
    async fetchOperations() {
      this.loading = true
      try {
        const res = await request.get(getAssistantOperationsApi, {
          params: {
            date: this.filters.date || undefined,
            account_type: this.filters.account_type || undefined,
            direction: this.filters.direction || undefined,
            variety_name: this.filters.variety_name || undefined
          }
        })
        if (res.code === 0) {
          this.operations = res.data?.operations || []
          if (!this.filters.date && res.data?.date) {
            this.filters.date = res.data.date
          }
          const hasCurrentSelection = this.operations.some(item => item.id === this.selectedOperationId)
          this.selectedOperationId = hasCurrentSelection ? this.selectedOperationId : (this.sortedOperations[0]?.id || null)
        }
      } catch (error) {
        console.error('获取操作建议失败', error)
      } finally {
        this.loading = false
      }
    },
    selectOperation(operation) {
      this.selectedOperationId = operation.id
    },
    formatScore(score) {
      const value = Number(score || 0)
      return `综合分 ${value.toFixed(2)}`
    },
    getDirectionLabel(direction) {
      return direction === 'LONG' ? '偏多 LONG' : '偏空 SHORT'
    },
    getAccountTypeLabel(accountType) {
      return accountType === 'llm' ? 'LLM 账户' : '机械规则账户'
    },
    getActionTagType(label) {
      if (label && label.includes('做多')) {
        return 'success'
      }
      if (label && label.includes('做空')) {
        return 'danger'
      }
      if (label && label.includes('观察')) {
        return 'warning'
      }
      return 'info'
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

.toolbar-card,
.empty-state-card {
  padding: 18px 20px;
  border-radius: 18px;
  border: 1px solid #e7edf4;
  background: linear-gradient(180deg, #fbfdff 0%, #ffffff 100%);
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  margin-top: 14px;
}

.tool-item {
  width: 180px;
}

.dual-pane {
  display: grid;
  grid-template-columns: minmax(320px, 420px) minmax(0, 1fr);
  gap: 16px;
  min-height: 720px;
}

.list-pane,
.detail-pane {
  border: 1px solid #e7edf4;
  border-radius: 22px;
  background: #fff;
  box-shadow: 0 14px 30px rgba(21, 43, 70, 0.06);
}

.list-pane {
  padding: 18px;
  display: flex;
  flex-direction: column;
}

.detail-pane {
  padding: 20px;
  overflow: hidden;
}

.pane-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.pane-title,
.section-heading {
  color: #16324a;
  font-size: 17px;
  font-weight: 700;
}

.pane-subtitle {
  margin-top: 6px;
  color: #7f90a3;
  font-size: 13px;
}

.operation-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 220px;
}

.operation-card {
  width: 100%;
  padding: 16px;
  border: 1px solid #e7edf4;
  border-radius: 18px;
  background: linear-gradient(180deg, #fbfdff 0%, #ffffff 100%);
  text-align: left;
  cursor: pointer;
  transition: all 0.2s ease;
}

.operation-card:hover,
.operation-card.active {
  border-color: #7aa7d9;
  box-shadow: 0 10px 24px rgba(57, 103, 159, 0.14);
  transform: translateY(-1px);
}

.operation-card-top,
.operation-action-row,
.operation-meta,
.detail-title-row,
.source-grid {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.operation-card-top {
  align-items: flex-start;
}

.operation-variety {
  color: #17324b;
  font-size: 18px;
  font-weight: 700;
}

.operation-strategy {
  margin-top: 6px;
  color: #688095;
  font-size: 13px;
  line-height: 1.6;
}

.operation-action-row {
  align-items: center;
  margin-top: 14px;
}

.operation-score {
  color: #1e5077;
  font-size: 13px;
  font-weight: 600;
}

.operation-summary,
.section-summary,
.decision-body,
.score-line,
.risk-card,
.hero-note,
.trigger-meaning,
.trigger-read,
.source-value,
.detail-subtitle {
  color: #52667c;
  line-height: 1.75;
}

.operation-summary {
  margin-top: 12px;
  font-size: 13px;
}

.operation-meta {
  margin-top: 12px;
  color: #8a99aa;
  font-size: 12px;
}

.detail-pane {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.detail-hero,
.detail-section {
  padding: 18px 20px;
  border: 1px solid #e8eef5;
  border-radius: 18px;
  background: linear-gradient(180deg, #ffffff 0%, #f9fbfd 100%);
}

.detail-eyebrow,
.hero-label,
.trigger-label,
.source-label {
  color: #74879a;
  font-size: 12px;
  font-weight: 600;
}

.detail-title {
  color: #16324a;
  font-size: 22px;
  font-weight: 700;
}

.detail-subtitle {
  margin-top: 8px;
  font-size: 13px;
}

.hero-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-top: 18px;
}

.hero-metric {
  padding: 16px;
  border-radius: 16px;
}

.hero-metric.action {
  background: #f4fbf7;
}

.hero-metric.score {
  background: #f4f9ff;
}

.hero-metric.status {
  background: #fcf7ef;
}

.hero-value,
.decision-title,
.trigger-value {
  margin-top: 8px;
  color: #16324a;
  font-size: 20px;
  font-weight: 700;
}

.trigger-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 16px;
}

.trigger-card,
.decision-card,
.score-panel,
.risk-card,
.source-item {
  padding: 16px;
  border-radius: 16px;
  background: #fff;
  border: 1px solid #e9eef4;
}

.trigger-meaning,
.trigger-read {
  margin-top: 10px;
  font-size: 13px;
}

.decision-title {
  margin-top: 0;
}

.score-panel {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.source-grid {
  flex-wrap: wrap;
  margin-top: 14px;
}

.source-item {
  flex: 1 1 220px;
}

.source-value {
  margin-top: 8px;
  font-size: 14px;
}

.source-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.source-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  background: #f1f6fb;
  color: #47627d;
  font-size: 12px;
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

  .hero-grid,
  .trigger-grid {
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

  .operation-card-top,
  .operation-action-row,
  .operation-meta,
  .detail-title-row,
  .source-grid {
    flex-direction: column;
  }
}
</style>
