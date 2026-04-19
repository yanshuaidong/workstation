<template>
  <div class="assistant-page">
    <div class="toolbar">
      <el-date-picker
        v-model="filters.date"
        type="date"
        value-format="YYYY-MM-DD"
        placeholder="选择日期"
        clearable
      />
      <el-select v-model="filters.indicator" clearable placeholder="指标" class="tool-item">
        <el-option
          v-for="item in indicatorOptions"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
      <el-select v-model="filters.direction" clearable placeholder="方向" class="tool-item">
        <el-option label="LONG" value="LONG" />
        <el-option label="SHORT" value="SHORT" />
      </el-select>
      <el-input v-model="filters.variety_name" clearable placeholder="品种筛选" class="tool-item" />
      <el-button type="primary" :loading="loading" :disabled="!filters.indicator" @click="fetchSignals">查询</el-button>
    </div>

    <div v-if="!activeSchema" class="empty-state-card">
      <el-empty description="请先选择一个具体指标，再查看该指标自己的信号表格。" />
    </div>

    <template v-else>
      <div class="schema-banner">
        <div class="schema-banner-title">{{ activeSchema.label }}</div>
        <div class="schema-banner-subtitle">{{ activeSchema.shortDesc }}</div>
      </div>

      <el-table
        v-loading="loading"
        :data="signals"
        row-key="id"
        stripe
        class="data-table"
        @expand-change="handleExpand"
      >
      <el-table-column type="expand">
        <template #default="{ row }">
          <div class="signal-detail-panel">
            <AssistantContextChart
              :loading="contextLoadingMap[getContextKey(row)]"
              :series-data="contextMap[getContextKey(row)] || []"
            />
          </div>
        </template>
      </el-table-column>
      <el-table-column
        v-for="column in activeSchema.columns"
        :key="column.key"
        :prop="column.prop"
        :label="column.label"
        :min-width="column.minWidth"
        :width="column.width"
      >
        <template #default="{ row }">
          <template v-if="column.type === 'direction'">
            <el-tag :type="row.direction === 'LONG' ? 'success' : 'danger'">
              {{ getDirectionLabel(row.direction) }}
            </el-tag>
          </template>
          <template v-else-if="column.type === 'plain'">
            <span>{{ column.value(row) }}</span>
          </template>
          <template v-else>
            <el-tooltip placement="top" :show-after="100">
              <template #content>
                <div class="signal-tooltip">
                  <div class="tooltip-title">{{ column.tooltipTitle }}</div>
                  <div
                    v-for="(line, index) in column.tooltipLines(row)"
                    :key="`${column.key}-${row.id}-${index}`"
                  >
                    {{ line }}
                  </div>
                </div>
              </template>
              <div class="metric-cell">
                <div class="metric-main">{{ column.mainText(row) }}</div>
                <div class="metric-sub">{{ column.subText(row) }}</div>
              </div>
            </el-tooltip>
          </template>
        </template>
      </el-table-column>
      </el-table>

      <div v-if="!loading && !signals.length" class="empty-state-card">
        <el-empty description="当前筛选条件下没有该指标的信号数据。" />
      </div>
    </template>
  </div>
</template>

<script>
import request from '@/utils/request'
import { getAssistantSignalsApi, getAssistantMarketContextApi } from '@/api'
import AssistantContextChart from './AssistantContextChart.vue'
import { getSignalTableSchema, indicatorOptions } from './signalTableSchema'
import { getDefaultSignalDate, getFirstIndicatorValue } from '@/utils/assistantSignalDefaults.mjs'

export default {
  name: 'AssistantSignalsView',
  components: {
    AssistantContextChart
  },
  data() {
    return {
      loading: false,
      signals: [],
      filters: {
        date: '',
        indicator: '',
        direction: '',
        variety_name: ''
      },
      indicatorOptions,
      contextMap: {},
      contextLoadingMap: {}
    }
  },
  computed: {
    activeSchema() {
      return getSignalTableSchema(this.filters.indicator)
    }
  },
  mounted() {
    this.initializeFilters()
    this.fetchSignals()
  },
  watch: {
    'filters.indicator'(nextIndicator, prevIndicator) {
      if (nextIndicator === prevIndicator) {
        return
      }
      this.signals = []
      this.contextMap = {}
      this.contextLoadingMap = {}
    }
  },
  methods: {
    initializeFilters() {
      this.filters.date = getDefaultSignalDate()
      this.filters.indicator = getFirstIndicatorValue(this.indicatorOptions)
    },
    getContextKey(row) {
      return `${row.variety_id}_${row.signal_date}`
    },
    getDirectionLabel(direction) {
      return direction === 'LONG' ? '偏多 LONG' : '偏空 SHORT'
    },
    async fetchSignals() {
      if (!this.filters.indicator) {
        this.signals = []
        return
      }
      this.loading = true
      try {
        const res = await request.get(getAssistantSignalsApi, {
          params: {
            date: this.filters.date || undefined,
            indicator: this.filters.indicator || undefined,
            direction: this.filters.direction || undefined,
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
    async handleExpand(row, expandedRows) {
      const expanded = expandedRows.some(item => item.id === row.id)
      const contextKey = this.getContextKey(row)
      if (!expanded || this.contextMap[contextKey]) {
        return
      }
      this.contextLoadingMap = {
        ...this.contextLoadingMap,
        [contextKey]: true
      }
      try {
        const res = await request.get(getAssistantMarketContextApi, {
          params: {
            variety_id: row.variety_id,
            end_date: row.signal_date,
            days: 10
          }
        })
        if (res.code === 0) {
          this.contextMap = {
            ...this.contextMap,
            [contextKey]: res.data?.series || []
          }
        }
      } catch (error) {
        console.error('获取市场上下文失败', error)
      } finally {
        this.contextLoadingMap = {
          ...this.contextLoadingMap,
          [contextKey]: false
        }
      }
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

.schema-banner,
.empty-state-card {
  padding: 18px 20px;
  border-radius: 16px;
  border: 1px solid #e7edf4;
  background: linear-gradient(180deg, #fbfdff 0%, #ffffff 100%);
}

.schema-banner-title {
  color: #1f3952;
  font-size: 16px;
  font-weight: 700;
}

.schema-banner-subtitle {
  margin-top: 6px;
  color: #6f8294;
  font-size: 13px;
  line-height: 1.7;
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

.data-table {
  width: 100%;
}

.signal-detail-panel {
  width: 100%;
}

.metric-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.metric-main {
  color: #243447;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.5;
}

.metric-sub {
  color: #8a98a8;
  font-size: 12px;
  line-height: 1.5;
}

.signal-tooltip {
  max-width: 320px;
  line-height: 1.7;
  font-size: 12px;
}

.tooltip-title {
  margin-bottom: 4px;
  font-size: 13px;
  font-weight: 700;
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
