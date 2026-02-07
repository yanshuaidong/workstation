<template>
  <el-drawer
    :model-value="visible"
    title="事件管理"
    direction="rtl"
    size="550px"
    @update:model-value="handleVisibleChange"
  >
    <div class="events-drawer-content">
      <div class="events-drawer-header">
        <el-button 
          type="primary" 
          icon="Plus"
          @click="handleAdd"
        >
          添加事件
        </el-button>
        <el-button 
          icon="Refresh"
          @click="handleRefresh"
          :loading="loading"
        >
          刷新
        </el-button>
      </div>

      <el-table
        :data="eventsData"
        stripe
        style="width: 100%"
        v-loading="loading"
      >
        <el-table-column prop="event_date" label="日期" width="100" />
        <el-table-column prop="title" label="标题" min-width="120" show-overflow-tooltip />
        <el-table-column label="方向" width="70">
          <template #default="scope">
            <el-tag 
              :type="getOutlookTagType(scope.row.outlook)"
              size="small"
            >
              {{ getOutlookLabel(scope.row.outlook) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
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

      <el-empty 
        v-if="eventsData.length === 0 && !loading"
        description="暂无事件记录"
      />
    </div>
  </el-drawer>
</template>

<script>
export default {
  name: 'EventsDrawer',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    eventsData: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:visible', 'add', 'edit', 'delete', 'refresh'],
  methods: {
    handleVisibleChange(val) {
      this.$emit('update:visible', val)
    },
    handleAdd() {
      this.$emit('add')
    },
    handleEdit(event) {
      this.$emit('edit', event)
    },
    handleDelete(id) {
      this.$emit('delete', id)
    },
    handleRefresh() {
      this.$emit('refresh')
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
.events-drawer-content {
  padding: 0 10px;
}

.events-drawer-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}
</style>
