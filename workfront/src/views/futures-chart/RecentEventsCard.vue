<template>
  <el-card class="recent-events-card">
    <template #header>
      <div class="card-header clickable" @click="handleToggle">
        <div class="header-left">
          <el-icon class="collapse-icon" :class="{ collapsed: collapsed }">
            <ArrowDown />
          </el-icon>
          <span>最近添加的事件</span>
          <span class="data-count" v-if="recentEventsData.length">
            （共 {{ recentEventsData.length }} 条）
          </span>
        </div>
        <div class="header-right" @click.stop>
          <el-button-group class="recent-days-group">
            <el-button 
              size="small" 
              :type="days === 7 ? 'primary' : ''"
              @click="handleSetDays(7)"
            >7天</el-button>
            <el-button 
              size="small" 
              :type="days === 14 ? 'primary' : ''"
              @click="handleSetDays(14)"
            >14天</el-button>
            <el-button 
              size="small" 
              :type="days === 30 ? 'primary' : ''"
              @click="handleSetDays(30)"
            >1个月</el-button>
          </el-button-group>
          <el-button 
            size="small" 
            icon="Refresh"
            @click="handleRefresh"
            :loading="loading"
            style="margin-left: 12px;"
          >
            刷新
          </el-button>
        </div>
      </div>
    </template>

    <el-collapse-transition>
      <div v-show="!collapsed" v-loading="loading">
        <!-- 品种统计标签 -->
        <div class="symbol-stats" v-if="Object.keys(symbolStats).length > 0">
          <span class="stats-label">品种分布：</span>
          <el-tag 
            v-for="(stat, symbol) in symbolStats" 
            :key="symbol"
            class="symbol-tag"
            size="small"
            effect="plain"
            @click="handleJumpToSymbol(symbol)"
          >
            {{ stat.name }} ({{ stat.count }})
          </el-tag>
        </div>

        <!-- 事件列表 -->
        <div class="recent-events-list" v-if="recentEventsData.length > 0">
          <div 
            class="event-item" 
            v-for="event in recentEventsData" 
            :key="event.id"
            @click="handleJumpToEvent(event)"
          >
            <div class="event-left">
              <el-tag 
                :type="getOutlookTagType(event.outlook)"
                size="small"
                effect="dark"
                class="outlook-tag"
              >
                {{ getOutlookLabel(event.outlook) }}
              </el-tag>
              <span class="event-symbol">{{ event.symbol_name }}</span>
              <span class="event-title">{{ event.title }}</span>
            </div>
            <div class="event-right">
              <span class="event-date">{{ event.event_date }}</span>
              <span class="event-created">{{ formatRelativeTime(event.created_at) }}</span>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <el-empty 
          v-if="recentEventsData.length === 0 && !loading"
          description="最近30天暂无添加事件"
          :image-size="60"
        />
      </div>
    </el-collapse-transition>
  </el-card>
</template>

<script>
import { ArrowDown } from '@element-plus/icons-vue'

export default {
  name: 'RecentEventsCard',
  components: {
    ArrowDown
  },
  props: {
    recentEventsData: {
      type: Array,
      default: () => []
    },
    symbolStats: {
      type: Object,
      default: () => ({})
    },
    loading: {
      type: Boolean,
      default: false
    },
    days: {
      type: Number,
      default: 7
    }
  },
  data() {
    return {
      collapsed: false
    }
  },
  emits: ['jump-to-symbol', 'jump-to-event', 'set-days', 'refresh'],
  methods: {
    handleToggle() {
      this.collapsed = !this.collapsed
    },
    handleSetDays(days) {
      this.$emit('set-days', days)
    },
    handleRefresh() {
      this.$emit('refresh')
    },
    handleJumpToSymbol(symbol) {
      this.$emit('jump-to-symbol', symbol)
    },
    handleJumpToEvent(event) {
      this.$emit('jump-to-event', event)
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
    },
    formatRelativeTime(dateStr) {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      const now = new Date()
      const diff = now - date
      
      const minutes = Math.floor(diff / 60000)
      const hours = Math.floor(diff / 3600000)
      const days = Math.floor(diff / 86400000)
      
      if (minutes < 60) {
        return `${minutes}分钟前`
      } else if (hours < 24) {
        return `${hours}小时前`
      } else if (days < 7) {
        return `${days}天前`
      } else {
        return dateStr.split(' ')[0]
      }
    }
  }
}
</script>

<style scoped>
.recent-events-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.card-header.clickable {
  cursor: pointer;
  user-select: none;
}

.card-header.clickable:hover {
  opacity: 0.8;
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
}

.collapse-icon {
  transition: transform 0.3s;
  margin-right: 8px;
}

.collapse-icon.collapsed {
  transform: rotate(-90deg);
}

.data-count {
  font-size: 14px;
  font-weight: normal;
  color: #909399;
}

.symbol-stats {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.stats-label {
  color: #909399;
  font-size: 13px;
}

.symbol-tag {
  cursor: pointer;
  transition: all 0.2s;
}

.symbol-tag:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.recent-events-list {
  max-height: 300px;
  overflow-y: auto;
}

.event-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 1px solid #f0f0f0;
}

.event-item:last-child {
  border-bottom: none;
}

.event-item:hover {
  background: linear-gradient(135deg, #f5f7fa 0%, #e8f4ff 100%);
  transform: translateX(4px);
}

.event-left {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  min-width: 0;
}

.outlook-tag {
  flex-shrink: 0;
}

.event-symbol {
  font-weight: 600;
  color: #409eff;
  font-size: 13px;
  flex-shrink: 0;
}

.event-title {
  color: #303133;
  font-size: 13px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.event-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
  margin-left: 16px;
}

.event-date {
  color: #606266;
  font-size: 12px;
  font-family: monospace;
}

.event-created {
  color: #909399;
  font-size: 11px;
  min-width: 60px;
  text-align: right;
}
</style>
