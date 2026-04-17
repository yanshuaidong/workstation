<template>
  <div class="assistant-page">
    <el-alert
      title="当前版本先保留只读操作建议面板，人工确认开关的写库动作后续可继续接。"
      type="warning"
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
        <el-option label="mechanical" value="mechanical" />
        <el-option label="llm" value="llm" />
      </el-select>
      <el-select v-model="filters.direction" clearable placeholder="方向" class="tool-item">
        <el-option label="LONG" value="LONG" />
        <el-option label="SHORT" value="SHORT" />
      </el-select>
      <el-input v-model="filters.variety_name" clearable placeholder="品种筛选" class="tool-item" />
      <el-button type="primary" :loading="loading" @click="fetchOperations">查询</el-button>
    </div>

    <el-table v-loading="loading" :data="operations" stripe class="data-table">
      <el-table-column prop="signal_date" label="日期" width="120" />
      <el-table-column prop="variety_name" label="品种" min-width="110" />
      <el-table-column prop="strategy" label="策略" width="100" />
      <el-table-column prop="strategy_label" label="策略说明" min-width="180" />
      <el-table-column label="方向" width="110">
        <template #default="{ row }">
          <el-tag :type="row.direction === 'LONG' ? 'success' : 'danger'">{{ row.direction }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="触发指标" min-width="280">
        <template #default="{ row }">
          <div class="trigger-list">
            <span v-for="(value, key) in row.trigger_indicators" :key="key" class="trigger-chip">
              {{ key }}={{ value }}
            </span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="综合分" width="110">
        <template #default="{ row }">
          {{ Number(row.composite_score || 0).toFixed(2) }}
        </template>
      </el-table-column>
      <el-table-column label="已执行" width="100">
        <template #default="{ row }">
          <el-tag :type="row.executed ? 'success' : 'info'">{{ row.executed ? '是' : '否' }}</el-tag>
        </template>
      </el-table-column>
    </el-table>
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
      filters: {
        date: '',
        account_type: 'mechanical',
        direction: '',
        variety_name: ''
      }
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
        }
      } catch (error) {
        console.error('获取操作建议失败', error)
      } finally {
        this.loading = false
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

.trigger-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.trigger-chip {
  display: inline-flex;
  align-items: center;
  padding: 4px 8px;
  border-radius: 999px;
  background: #f1f6fb;
  color: #47627d;
  font-size: 12px;
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

