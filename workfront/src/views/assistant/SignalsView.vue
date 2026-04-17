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
        <el-option v-for="item in indicatorOptions" :key="item" :label="item" :value="item" />
      </el-select>
      <el-select v-model="filters.direction" clearable placeholder="方向" class="tool-item">
        <el-option label="LONG" value="LONG" />
        <el-option label="SHORT" value="SHORT" />
      </el-select>
      <el-input v-model="filters.variety_name" clearable placeholder="品种筛选" class="tool-item" />
      <el-button type="primary" :loading="loading" @click="fetchSignals">查询</el-button>
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
          <AssistantContextChart
            :loading="contextLoadingMap[row.variety_id]"
            :series-data="contextMap[row.variety_id] || []"
          />
        </template>
      </el-table-column>
      <el-table-column prop="signal_date" label="日期" width="120" />
      <el-table-column prop="variety_name" label="品种" min-width="110" />
      <el-table-column prop="indicator" label="指标" min-width="150" />
      <el-table-column label="方向" width="110">
        <template #default="{ row }">
          <el-tag :type="row.direction === 'LONG' ? 'success' : 'danger'">{{ row.direction }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="indicator_value" label="触发值" min-width="220" />
      <el-table-column label="强度" width="100">
        <template #default="{ row }">
          {{ row.strength !== null && row.strength !== undefined ? Number(row.strength).toFixed(2) : '--' }}
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script>
import request from '@/utils/request'
import { getAssistantSignalsApi, getAssistantMarketContextApi } from '@/api'
import AssistantContextChart from './AssistantContextChart.vue'

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
      indicatorOptions: [
        'MF_Edge3',
        'MF_Accel',
        'MF_Duration',
        'MS_Divergence',
        'MF_Magnitude',
        'MF_BreakZone',
        'Composite_Score'
      ],
      contextMap: {},
      contextLoadingMap: {}
    }
  },
  mounted() {
    this.fetchSignals()
  },
  methods: {
    async fetchSignals() {
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
      if (!expanded || this.contextMap[row.variety_id]) {
        return
      }
      this.contextLoadingMap = {
        ...this.contextLoadingMap,
        [row.variety_id]: true
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
            [row.variety_id]: res.data?.series || []
          }
        }
      } catch (error) {
        console.error('获取市场上下文失败', error)
      } finally {
        this.contextLoadingMap = {
          ...this.contextLoadingMap,
          [row.variety_id]: false
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

