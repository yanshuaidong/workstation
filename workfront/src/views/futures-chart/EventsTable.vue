<template>
  <el-card class="events-table-card" v-if="showEvents && eventsData.length > 0">
    <template #header>
      <div class="card-header">
        <div class="header-left">
          <span>事件详情</span>
          <span class="data-count">（共 {{ eventsData.length }} 条事件）</span>
        </div>
        <el-button 
          type="primary" 
          size="small" 
          icon="Plus"
          @click="handleAdd"
        >
          添加事件
        </el-button>
      </div>
    </template>

    <el-table
      :data="eventsData"
      stripe
      border
      style="width: 100%"
      max-height="500"
      row-key="id"
    >
      <el-table-column prop="event_date" label="日期" width="110" sortable />
      <el-table-column prop="title" label="标题" min-width="180" show-overflow-tooltip />
      <el-table-column label="方向" width="90" align="center">
        <template #default="scope">
          <el-tag 
            :type="getOutlookTagType(scope.row.outlook)"
            size="small"
            effect="dark"
          >
            {{ getOutlookLabel(scope.row.outlook) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="强度" width="80" align="center">
        <template #default="scope">
          <span class="strength-value">{{ scope.row.strength || '-' }}</span>
        </template>
      </el-table-column>
      <el-table-column prop="content" label="内容" min-width="300">
        <template #default="scope">
          <div class="event-content-cell">
            {{ scope.row.content || '-' }}
          </div>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="120" fixed="right" align="center">
        <template #default="scope">
          <el-button 
            type="primary" 
            size="small" 
            text
            @click="handleEdit(scope.row)"
          >
            编辑
          </el-button>
          <el-popconfirm
            title="确定要删除这条事件吗？"
            confirm-button-text="确定"
            cancel-button-text="取消"
            @confirm="handleDelete(scope.row.id)"
          >
            <template #reference>
              <el-button type="danger" size="small" text>删除</el-button>
            </template>
          </el-popconfirm>
        </template>
      </el-table-column>
    </el-table>
  </el-card>
</template>

<script>
export default {
  name: 'EventsTable',
  props: {
    eventsData: {
      type: Array,
      default: () => []
    },
    showEvents: {
      type: Boolean,
      default: true
    }
  },
  emits: ['add', 'edit', 'delete'],
  methods: {
    handleAdd() {
      this.$emit('add')
    },
    handleEdit(event) {
      this.$emit('edit', event)
    },
    handleDelete(id) {
      this.$emit('delete', id)
    },
    getOutlookTagType(outlook) {
      const types = {
        'bullish': 'danger',
        'bearish': 'success',
        'ranging': 'warning',
        'uncertain': 'info'
      }
      return types[outlook] || 'info'
    },
    getOutlookLabel(outlook) {
      const labels = {
        'bullish': '看多',
        'bearish': '看空',
        'ranging': '震荡',
        'uncertain': '不确定'
      }
      return labels[outlook] || '-'
    }
  }
}
</script>

<style scoped>
.events-table-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.header-left {
  display: flex;
  align-items: center;
}

.data-count {
  font-size: 14px;
  font-weight: normal;
  color: #909399;
}

.strength-value {
  font-weight: bold;
  color: #409eff;
}

.event-content-cell {
  line-height: 1.6;
  color: #606266;
  white-space: pre-wrap;
  word-break: break-word;
}
</style>
