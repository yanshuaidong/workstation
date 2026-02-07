<template>
  <div class="events-calendar-container">
    <el-card shadow="hover" class="calendar-card">
      <!-- 标题和控制栏 -->
      <div class="calendar-header">
        <div class="calendar-title clickable" @click="handleToggle">
          <el-icon class="collapse-icon" :class="{ collapsed: collapsed }">
            <ArrowDown />
          </el-icon>
          <i class="el-icon-date"></i>
          <span>事件日历</span>
          <el-tag size="small" type="info" style="margin-left: 10px;">
            {{ totalEventsCount }} 个事件
          </el-tag>
        </div>
        
        <div class="calendar-controls" @click.stop>
          <!-- 月份选择器 -->
          <el-button 
            size="small" 
            icon="el-icon-arrow-left" 
            @click="previousMonth"
            circle
          />
          <el-date-picker
            v-model="currentMonth"
            type="month"
            placeholder="选择月份"
            size="small"
            style="width: 130px; margin: 0 10px;"
            :clearable="false"
            @change="onMonthChange"
          />
          <el-button 
            size="small" 
            icon="el-icon-arrow-right" 
            @click="nextMonth"
            circle
          />
          <el-button 
            size="small" 
            @click="goToday"
            style="margin-left: 10px;"
          >
            今天
          </el-button>
          
          <!-- 刷新按钮 -->
          <el-button
            size="small"
            icon="el-icon-refresh"
            :loading="loading"
            @click="handleRefresh"
            style="margin-left: 10px;"
          >
            刷新
          </el-button>
        </div>
      </div>

      <!-- 日历表格 -->
      <div v-show="!collapsed" class="calendar-body" v-loading="loading">
        <!-- 星期标题 -->
        <div class="calendar-weekdays">
          <div 
            v-for="day in weekdays" 
            :key="day"
            class="weekday-cell"
          >
            {{ day }}
          </div>
        </div>

        <!-- 日期格子 -->
        <div class="calendar-grid">
          <div
            v-for="(day, index) in calendarDays"
            :key="index"
            :class="[
              'calendar-day',
              {
                'empty-day': day.isEmpty,
                'other-month': !day.isCurrentMonth,
                'today': day.isToday,
                'has-events': day.events.length > 0,
                'weekend': day.isWeekend
              }
            ]"
          >
            <template v-if="!day.isEmpty">
              <div class="day-header">
                <span class="day-number">{{ day.day }}</span>
                <el-badge 
                  v-if="day.events.length > 0" 
                  :value="day.events.length"
                  :type="getBadgeType(day.events)"
                  class="event-badge"
                />
              </div>

              <!-- 事件列表 -->
              <div class="day-events">
                <el-popover
                  v-for="event in day.events.slice(0, 3)"
                  :key="event.id"
                  placement="top"
                  :width="300"
                  trigger="hover"
                  :open-delay="200"
                >
                  <template #reference>
                    <div 
                      :class="['event-item', `outlook-${event.outlook || 'neutral'}`]"
                      @click="handleEventClick(event)"
                    >
                      <span class="event-symbol">{{ event.symbol_name || event.symbol }}</span>
                      <span class="event-title">{{ event.title }}</span>
                    </div>
                  </template>
                  
                  <!-- 悬浮显示的详细内容 -->
                  <div class="event-popover">
                    <div class="event-popover-header">
                      <el-tag :type="getOutlookTagType(event.outlook)" size="small">
                        {{ event.symbol_name || event.symbol }}
                      </el-tag>
                      <el-tag 
                        v-if="event.outlook" 
                        :type="getOutlookTagType(event.outlook)"
                        size="small"
                        style="margin-left: 8px;"
                      >
                        {{ getOutlookText(event.outlook) }}
                      </el-tag>
                    </div>
                    <h4 class="event-popover-title">{{ event.title }}</h4>
                    <div class="event-popover-date">
                      <i class="el-icon-time"></i>
                      {{ event.event_date }}
                    </div>
                    <div v-if="event.content" class="event-popover-content">
                      <strong>详细内容：</strong>
                      <p>{{ event.content }}</p>
                    </div>
                    <div v-if="event.strength" class="event-popover-strength">
                      <strong>重要程度：</strong>
                      <el-rate 
                        v-model="event.strength" 
                        disabled 
                        show-score 
                        text-color="#ff9900"
                        :max="10"
                      />
                    </div>
                  </div>
                </el-popover>

                <!-- 如果事件超过3个，显示"更多"提示 -->
                <div 
                  v-if="day.events.length > 3" 
                  class="more-events"
                  @click="showMoreEvents(day)"
                >
                  +{{ day.events.length - 3 }} 更多...
                </div>
              </div>
            </template>
          </div>
        </div>

        <!-- 图例说明 -->
        <div class="calendar-legend">
          <div class="legend-item">
            <span class="legend-dot outlook-bullish"></span>
            <span>看多</span>
          </div>
          <div class="legend-item">
            <span class="legend-dot outlook-bearish"></span>
            <span>看空</span>
          </div>
          <div class="legend-item">
            <span class="legend-dot outlook-neutral"></span>
            <span>中性/震荡</span>
          </div>
        </div>
      </div>
    </el-card>

    <!-- 更多事件对话框 -->
    <el-dialog
      v-model="moreEventsDialogVisible"
      :title="`${selectedDay?.date} 的所有事件 (${selectedDay?.events?.length || 0}个)`"
      width="600px"
    >
      <div class="more-events-list">
        <div
          v-for="event in selectedDay?.events || []"
          :key="event.id"
          :class="['event-detail-card', `outlook-${event.outlook || 'neutral'}`]"
          @click="handleEventClick(event)"
        >
          <div class="event-detail-header">
            <el-tag :type="getOutlookTagType(event.outlook)" size="small">
              {{ event.symbol_name || event.symbol }}
            </el-tag>
            <el-tag 
              v-if="event.outlook" 
              :type="getOutlookTagType(event.outlook)"
              size="small"
            >
              {{ getOutlookText(event.outlook) }}
            </el-tag>
          </div>
          <h4>{{ event.title }}</h4>
          <p v-if="event.content">{{ event.content }}</p>
          <div class="event-detail-footer">
            <el-rate 
              v-if="event.strength"
              v-model="event.strength" 
              disabled 
              show-score 
              text-color="#ff9900"
              :max="10"
              size="small"
            />
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ArrowDown } from '@element-plus/icons-vue'

export default {
  name: 'EventsCalendar',
  components: {
    ArrowDown
  },
  props: {
    // 事件数据列表
    eventsData: {
      type: Array,
      default: () => []
    },
    // 加载状态
    loading: {
      type: Boolean,
      default: false
    },
    // 天数范围（用于加载事件）
    days: {
      type: Number,
      default: 30
    }
  },
  emits: ['refresh', 'event-click'],
  data() {
    return {
      weekdays: ['一', '二', '三', '四', '五', '六', '日'],
      currentMonth: new Date(),
      moreEventsDialogVisible: false,
      selectedDay: null,
      collapsed: false
    }
  },
  computed: {
    // 当前月份的年份
    currentYear() {
      return this.currentMonth.getFullYear()
    },
    // 当前月份（0-11）
    currentMonthNum() {
      return this.currentMonth.getMonth()
    },
    // 日历天数数组
    calendarDays() {
      const days = []
      const year = this.currentYear
      const month = this.currentMonthNum
      
      // 当月第一天
      const firstDay = new Date(year, month, 1)
      // 当月最后一天
      const lastDay = new Date(year, month + 1, 0)
      
      // 第一天是星期几（0-6，0表示周日）
      const firstDayWeek = firstDay.getDay()
      // 当月有多少天
      const daysInMonth = lastDay.getDate()
      
      // 计算第一天前需要空出的格子数（周一为第一天）
      // 如果是周日(0)，需要空6格；如果是周一(1)，需要空0格
      const emptyDays = firstDayWeek === 0 ? 6 : firstDayWeek - 1
      
      // 填充空白格子
      for (let i = 0; i < emptyDays; i++) {
        days.push({
          day: null,
          date: null,
          isCurrentMonth: false,
          isToday: false,
          isWeekend: false,
          isEmpty: true,
          events: []
        })
      }
      
      // 填充当月的日期
      for (let day = 1; day <= daysInMonth; day++) {
        const date = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`
        const dayOfWeek = new Date(year, month, day).getDay()
        days.push({
          day,
          date,
          isCurrentMonth: true,
          isToday: this.isToday(date),
          isWeekend: dayOfWeek === 0 || dayOfWeek === 6,
          isEmpty: false,
          events: this.getEventsForDate(date)
        })
      }
      
      return days
    },
    // 总事件数
    totalEventsCount() {
      return this.eventsData.length
    }
  },
  methods: {
    // 切换折叠状态
    handleToggle() {
      this.collapsed = !this.collapsed
    },
    
    // 判断是否是今天
    isToday(date) {
      const today = new Date()
      const todayStr = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`
      return date === todayStr
    },
    
    // 获取指定日期的事件
    getEventsForDate(date) {
      return this.eventsData.filter(event => event.event_date === date)
    },
    
    // 上一月
    previousMonth() {
      const newMonth = new Date(this.currentMonth)
      newMonth.setMonth(newMonth.getMonth() - 1)
      this.currentMonth = newMonth
      this.emitRefresh()
    },
    
    // 下一月
    nextMonth() {
      const newMonth = new Date(this.currentMonth)
      newMonth.setMonth(newMonth.getMonth() + 1)
      this.currentMonth = newMonth
      this.emitRefresh()
    },
    
    // 回到今天
    goToday() {
      this.currentMonth = new Date()
      this.emitRefresh()
    },
    
    // 月份改变
    onMonthChange() {
      this.emitRefresh()
    },
    
    // 刷新事件数据
    handleRefresh() {
      this.emitRefresh()
    },
    
    // 触发刷新事件
    emitRefresh() {
      // 计算当前月份的起止日期
      const year = this.currentYear
      const month = this.currentMonthNum
      const startDate = new Date(year, month, 1)
      const endDate = new Date(year, month + 1, 0)
      
      this.$emit('refresh', {
        startDate: startDate.toISOString().split('T')[0],
        endDate: endDate.toISOString().split('T')[0]
      })
    },
    
    // 获取outlook的tag类型
    getOutlookTagType(outlook) {
      const typeMap = {
        'bullish': 'danger',    // 利好用红色
        'bearish': 'success',   // 利空用绿色
        'neutral': 'warning',   // 中性用黄色
        'ranging': 'warning',   // 震荡用黄色
        'uncertain': 'info'     // 不确定用灰色
      }
      return typeMap[outlook] || 'info'
    },
    
    // 获取outlook的文字
    getOutlookText(outlook) {
      const textMap = {
        'bullish': '看多',
        'bearish': '看空',
        'neutral': '中性',
        'ranging': '震荡',
        'uncertain': '不确定'
      }
      return textMap[outlook] || '未知'
    },
    
    // 根据事件获取badge类型
    getBadgeType(events) {
      // 如果有看多或看空事件，优先显示
      const hasBullish = events.some(e => e.outlook === 'bullish')
      const hasBearish = events.some(e => e.outlook === 'bearish')
      
      if (hasBullish && hasBearish) return 'warning'  // 既有看多又有看空，用黄色
      if (hasBullish) return 'danger'   // 看多用红色
      if (hasBearish) return 'success'  // 看空用绿色
      return 'info'
    },
    
    // 显示更多事件
    showMoreEvents(day) {
      this.selectedDay = day
      this.moreEventsDialogVisible = true
    },
    
    // 点击事件
    handleEventClick(event) {
      this.$emit('event-click', event)
    }
  }
}
</script>

<style scoped>
.events-calendar-container {
  margin-bottom: 20px;
}

.calendar-card {
  border-radius: 8px;
}

.calendar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 15px;
  border-bottom: 1px solid #e8e8e8;
}

.calendar-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  display: flex;
  align-items: center;
}

.calendar-title.clickable {
  cursor: pointer;
  user-select: none;
}

.calendar-title.clickable:hover {
  opacity: 0.8;
}

.calendar-title i {
  margin-right: 8px;
  font-size: 20px;
  color: #409eff;
}

.collapse-icon {
  transition: transform 0.3s;
  margin-right: 8px;
  font-size: 18px;
  color: #606266;
}

.collapse-icon.collapsed {
  transform: rotate(-90deg);
}

.calendar-controls {
  display: flex;
  align-items: center;
}

.calendar-body {
  min-height: 400px;
  padding-top: 20px;
}

.calendar-weekdays {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
  margin-bottom: 1px;
  background-color: #f5f7fa;
}

.weekday-cell {
  padding: 10px;
  text-align: center;
  font-weight: bold;
  color: #606266;
  background-color: #fff;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 1px;
  background-color: #e8e8e8;
  border: 1px solid #e8e8e8;
}

.calendar-day {
  min-height: 100px;
  padding: 8px;
  background-color: #fff;
  position: relative;
  cursor: pointer;
  transition: all 0.3s ease;
}

.calendar-day:hover {
  background-color: #f5f7fa;
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.calendar-day.empty-day {
  background-color: #fafafa;
  cursor: default;
  pointer-events: none;
}

.calendar-day.empty-day:hover {
  background-color: #fafafa;
  transform: none;
  box-shadow: none;
}

.calendar-day.other-month {
  background-color: #fafafa;
  color: #c0c4cc;
}

.calendar-day.today {
  background-color: #ecf5ff;
  border: 2px solid #409eff;
}

.calendar-day.weekend {
  background-color: #fafafa;
}

.day-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}

.day-number {
  font-weight: bold;
  font-size: 14px;
  color: #303133;
}

.calendar-day.other-month .day-number {
  color: #c0c4cc;
}

.calendar-day.today .day-number {
  color: #409eff;
  font-size: 16px;
}

.event-badge {
  font-size: 12px;
}

.day-events {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.event-item {
  padding: 4px 6px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 4px;
}

.event-item:hover {
  transform: translateX(2px);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.event-item.outlook-bullish {
  background-color: #fef0f0;
  border-left: 3px solid #f56c6c;
  color: #f56c6c;
}

.event-item.outlook-bearish {
  background-color: #f0f9ff;
  border-left: 3px solid #67c23a;
  color: #67c23a;
}

.event-item.outlook-neutral {
  background-color: #fdf6ec;
  border-left: 3px solid #e6a23c;
  color: #e6a23c;
}

.event-item.outlook-ranging {
  background-color: #fdf6ec;
  border-left: 3px solid #e6a23c;
  color: #e6a23c;
}

.event-item.outlook-uncertain {
  background-color: #f4f4f5;
  border-left: 3px solid #909399;
  color: #909399;
}

.event-symbol {
  font-weight: bold;
  flex-shrink: 0;
}

.event-title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #303133;
}

.more-events {
  padding: 4px 6px;
  text-align: center;
  font-size: 12px;
  color: #409eff;
  cursor: pointer;
  border-radius: 4px;
  background-color: #ecf5ff;
}

.more-events:hover {
  background-color: #d9ecff;
}

/* 悬浮弹窗样式 */
.event-popover {
  padding: 5px;
}

.event-popover-header {
  margin-bottom: 10px;
}

.event-popover-title {
  margin: 10px 0;
  font-size: 16px;
  color: #303133;
}

.event-popover-date {
  margin-bottom: 10px;
  color: #909399;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.event-popover-content {
  margin: 10px 0;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.6;
}

.event-popover-content p {
  margin: 5px 0 0 0;
  color: #606266;
}

.event-popover-strength {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #e8e8e8;
  font-size: 13px;
}

/* 图例 */
.calendar-legend {
  display: flex;
  gap: 20px;
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #e8e8e8;
  justify-content: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: #606266;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-dot.outlook-bullish {
  background-color: #f56c6c;
}

.legend-dot.outlook-bearish {
  background-color: #67c23a;
}

.legend-dot.outlook-neutral {
  background-color: #e6a23c;
}

/* 更多事件对话框 */
.more-events-list {
  max-height: 500px;
  overflow-y: auto;
}

.event-detail-card {
  padding: 15px;
  margin-bottom: 10px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  border-left: 4px solid;
}

.event-detail-card:hover {
  transform: translateX(5px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.event-detail-card.outlook-bullish {
  background-color: #fef0f0;
  border-left-color: #f56c6c;
}

.event-detail-card.outlook-bearish {
  background-color: #f0f9ff;
  border-left-color: #67c23a;
}

.event-detail-card.outlook-neutral {
  background-color: #fdf6ec;
  border-left-color: #e6a23c;
}

.event-detail-card.outlook-ranging {
  background-color: #fdf6ec;
  border-left-color: #e6a23c;
}

.event-detail-card.outlook-uncertain {
  background-color: #f4f4f5;
  border-left-color: #909399;
}

.event-detail-header {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.event-detail-card h4 {
  margin: 10px 0;
  font-size: 15px;
  color: #303133;
}

.event-detail-card p {
  margin: 10px 0;
  color: #606266;
  font-size: 13px;
  line-height: 1.6;
}

.event-detail-footer {
  margin-top: 10px;
  padding-top: 10px;
  border-top: 1px solid #e8e8e8;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .calendar-header {
    flex-direction: column;
    gap: 15px;
    align-items: flex-start;
  }
  
  .calendar-title {
    width: 100%;
  }
  
  .calendar-controls {
    flex-wrap: wrap;
    width: 100%;
  }
  
  .calendar-day {
    min-height: 80px;
    padding: 5px;
  }
  
  .event-item {
    font-size: 10px;
    padding: 2px 4px;
  }
  
  .day-number {
    font-size: 12px;
  }
}
</style>
