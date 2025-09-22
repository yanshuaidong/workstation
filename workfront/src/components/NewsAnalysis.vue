<template>
  <div class="news-analysis">
    <!-- 统计信息区 -->
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span>财联社新闻管理系统</span>
          <el-tag type="success">运行中</el-tag>
        </div>
      </template>

      <!-- 统计信息展示 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-value">{{ stats.total }}</div>
            <div class="stat-label">总新闻数</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-value success">{{ stats.today_count }}</div>
            <div class="stat-label">今日新增</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-time">{{ stats.latest_time || '暂无数据' }}</div>
            <div class="stat-label">最新时间</div>
          </div>
        </el-col>
        <el-col :span="6">
          <div class="stat-card">
            <div class="stat-time">{{ stats.earliest_time || '暂无数据' }}</div>
            <div class="stat-label">最早时间</div>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 新闻列表展示区块 -->
    <el-card class="news-list-card">
      <template #header>
        <div class="card-header">
          <span>新闻列表</span>
          <div class="header-controls">
            <el-button
              type="info"
              size="small"
              @click="loadStats"
              :loading="statsLoading"
              icon="Refresh"
            >
              刷新统计
            </el-button>
            <el-button
              type="primary"
              size="small"
              @click="loadNewsList"
              :loading="newsLoading"
              icon="Refresh"
            >
              刷新列表
            </el-button>
          </div>
        </div>
      </template>

      <!-- 数据表格 -->
      <div class="news-table-container">
        <!-- 表格为空时的提示 -->
        <el-empty
          v-if="!newsLoading && newsList.length === 0"
          description="暂无新闻数据"
          :image-size="120"
        />

        <!-- 新闻列表表格 -->
        <el-table
          v-else
          :data="newsList"
          v-loading="newsLoading"
          stripe
          border
          style="width: 100%"
          max-height="600"
          empty-text="暂无新闻数据"
        >
          <!-- 第1列：序号 -->
          <el-table-column type="index" label="序号" width="60" :index="(index) => (pagination.page - 1) * pagination.page_size + index + 1" />
          
          <!-- 第2列：发布时间 -->
          <el-table-column prop="time" label="发布时间" width="180" />
          
          <!-- 第3列：标题 -->
          <el-table-column label="标题" min-width="200">
            <template #default="scope">
              <el-tooltip
                :content="scope.row.title"
                placement="top"
                :show-after="500"
              >
                <div class="title-cell">{{ scope.row.title }}</div>
              </el-tooltip>
            </template>
          </el-table-column>
          
          <!-- 第4列：内容 -->
          <el-table-column label="内容" min-width="250">
            <template #default="scope">
              <el-text
                :line-clamp="3"
                class="content-text"
                :title="scope.row.content"
              >
                {{ scope.row.content }}
              </el-text>
            </template>
          </el-table-column>
          
          <!-- 第5列：AI分析 -->
          <el-table-column label="AI分析" min-width="200">
            <template #default="scope">
              <div class="ai-analysis-cell">
                <el-text
                  :line-clamp="3"
                  class="ai-analysis-text"
                  :title="scope.row.ai_analysis || '暂无分析结果'"
                >
                  {{ scope.row.ai_analysis || '暂无分析结果' }}
                </el-text>
              </div>
            </template>
          </el-table-column>
          
          <!-- 第6列：软硬标记 -->
          <el-table-column label="消息类型" width="100" align="center">
            <template #default="scope">
              <el-tag
                :type="getNewsType(scope.row.ai_analysis).type"
                size="small"
                effect="dark"
              >
                {{ getNewsType(scope.row.ai_analysis).label }}
              </el-tag>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页器 -->
        <div v-if="pagination.total > 0" class="pagination-container">
          <el-pagination
            :current-page="pagination.page"
            :page-size="pagination.page_size"
            :page-sizes="[10, 20, 50, 100]"
            :total="pagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleSizeChange"
            @current-change="handleCurrentChange"
            background
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import request from '@/utils/request'
import { getClsNewsListApi, getClsNewsStatsApi } from '@/api'
import { ElMessage } from 'element-plus'

export default {
  name: 'NewsAnalysis',
  data() {
    return {
      // 新闻列表
      newsList: [],
      newsLoading: false,
      
      // 统计信息
      stats: {
        total: 0,
        today_count: 0,
        latest_time: '',
        earliest_time: ''
      },
      statsLoading: false,
      
      // 分页信息
      pagination: {
        page: 1,
        page_size: 10,
        total: 0,
        total_pages: 0,
        has_prev: false,
        has_next: false
      }
    }
  },
  
  async mounted() {
    await this.loadStats()
    await this.loadNewsList()
  },
  
  methods: {
    // 加载新闻列表
    async loadNewsList() {
      this.newsLoading = true
      try {
        const params = new URLSearchParams({
          page: this.pagination.page,
          page_size: this.pagination.page_size
        })
        
        const response = await request.get(`${getClsNewsListApi}?${params}`)
        
        if (response.code === 0) {
          this.newsList = response.data.news_list || []
          this.pagination = { ...this.pagination, ...response.data.pagination }
          
          if (this.newsList.length > 0) {
            ElMessage.success(`加载成功，共 ${this.pagination.total} 条新闻`)
          }
        } else {
          ElMessage.error(`查询失败: ${response.message}`)
        }
      } catch (error) {
        console.error('查询新闻失败:', error)
        ElMessage.error(`查询新闻失败: ${error.message}`)
      } finally {
        this.newsLoading = false
      }
    },
    
    // 加载统计信息
    async loadStats() {
      this.statsLoading = true
      try {
        const response = await request.get(getClsNewsStatsApi)
        
        if (response.code === 0) {
          this.stats = response.data
        } else {
          console.error('获取统计信息失败:', response.message)
        }
      } catch (error) {
        console.error('获取统计信息失败:', error)
      } finally {
        this.statsLoading = false
      }
    },
    
    // 分页大小变化
    handleSizeChange(newSize) {
      this.pagination.page_size = newSize
      this.pagination.page = 1 // 重置到第一页
      this.loadNewsList()
    },
    
    // 当前页变化
    handleCurrentChange(newPage) {
      this.pagination.page = newPage
      this.loadNewsList()
    },
    
    // 判断消息类型（软消息/硬消息）
    getNewsType(aiAnalysis) {
      if (!aiAnalysis) {
        return { type: 'info', label: '未知' }
      }
      
      // 硬消息关键词（这些通常是重要的、有影响力的消息）
      const hardKeywords = [
        '重大', '突破', '暴涨', '暴跌', '崩盘', '涨停', '跌停',
        '政策', '央行', '降准', '加息', '降息', '监管',
        '并购', '重组', '收购', '上市', '退市',
        '业绩', '财报', '盈利', '亏损', '增长',
        '违规', '处罚', '调查', '停牌', '复牌',
        '合作', '签约', '协议', '投资',
        '创新高', '新低', '突破', '跳水'
      ]
      
      // 软消息关键词（这些通常是一般性的、影响相对较小的消息）
      const softKeywords = [
        '预期', '可能', '或将', '有望', '计划',
        '消息', '传闻', '市场', '分析师', '观点',
        '建议', '推荐', '关注', '提示',
        '一般', '常规', '正常', '稳定',
        '讨论', '会议', '发布会', '活动'
      ]
      
      const analysisText = aiAnalysis.toLowerCase()
      
      // 检查硬消息关键词
      const hasHardKeyword = hardKeywords.some(keyword => 
        analysisText.includes(keyword.toLowerCase())
      )
      
      // 检查软消息关键词
      const hasSoftKeyword = softKeywords.some(keyword => 
        analysisText.includes(keyword.toLowerCase())
      )
      
      // 优先判断为硬消息，如果都没有匹配则默认为软消息
      if (hasHardKeyword) {
        return { type: 'success', label: '硬消息' }
      } else if (hasSoftKeyword) {
        return { type: 'info', label: '软消息' }
      } else {
        // 默认为软消息
        return { type: 'info', label: '软消息' }
      }
    }
  }
}
</script>

<style scoped>
.news-analysis {
  padding: 20px;
}

.header-card,
.news-list-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

.header-controls {
  display: flex;
  gap: 10px;
}

/* 统计信息样式 */
.stats-row {
  margin-bottom: 0;
}

.stat-card {
  text-align: center;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  color: white;
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  margin-bottom: 8px;
}

.stat-value.success {
  color: #67c23a;
}

.stat-label {
  font-size: 14px;
  opacity: 0.9;
}

.stat-time {
  font-size: 13px;
  font-weight: 500;
  opacity: 0.9;
}

/* 表格样式 */
.news-table-container {
  min-height: 400px;
}

.title-cell {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 250px;
}

.content-text {
  color: #606266;
  line-height: 1.6;
  font-size: 14px;
}

/* AI分析列样式 */
.ai-analysis-cell {
  padding: 5px 0;
}

.ai-analysis-text {
  color: #409eff;
  line-height: 1.6;
  font-size: 13px;
  font-weight: 500;
}

/* 消息类型标签样式 */
.el-tag.el-tag--success.el-tag--dark {
  background-color: #67c23a;
  border-color: #67c23a;
  color: white;
  font-weight: 600;
}

.el-tag.el-tag--info.el-tag--dark {
  background-color: #909399;
  border-color: #909399;
  color: white;
  font-weight: 500;
}

/* 分页器样式 */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 30px;
  padding: 20px 0;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .stats-row .el-col {
    margin-bottom: 20px;
  }
}

@media (max-width: 768px) {
  .news-analysis {
    padding: 10px;
  }
  
  .card-header {
    flex-direction: column;
    gap: 10px;
  }
  
  .header-controls {
    justify-content: center;
  }
  
  .stat-card {
    margin-bottom: 15px;
  }
  
  .stat-value {
    font-size: 24px;
  }
}

/* 加载状态动画 */
.el-loading-mask {
  border-radius: 8px;
}

/* 空状态样式 */
.el-empty {
  padding: 40px 20px;
}
</style>
