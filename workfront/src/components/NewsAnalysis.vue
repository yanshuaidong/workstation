<template>
  <div class="news-analysis">
    <!-- 标题栏 -->
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span>财联社加红电报新闻爬虫系统</span>
          <el-tag :type="systemStatus.type">{{ systemStatus.text }}</el-tag>
        </div>
      </template>

      <!-- 操作控制区 -->
      <el-row :gutter="20" class="control-row">
        <!-- 爬取操作 -->
        <el-col :span="8">
          <el-card shadow="never" class="operation-card">
            <template #header>数据爬取</template>
            <div class="operation-content">
              <el-button
                type="primary"
                size="large"
                @click="startCrawling"
                :loading="crawlLoading"
                icon="Download"
                style="width: 100%; margin-bottom: 15px;"
              >
                {{ crawlLoading ? '正在爬取新闻...' : '开始爬取新闻' }}
              </el-button>
              <div class="operation-description">
                <p>点击此按钮开始爬取财联社加红电报最新新闻</p>
                <p class="text-muted">• 自动访问财联社网站</p>
                <p class="text-muted">• 模拟点击"加红"按钮</p>
                <p class="text-muted">• 获取并保存最新新闻数据</p>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 查询操作 -->
        <el-col :span="8">
          <el-card shadow="never" class="operation-card">
            <template #header>数据查询</template>
            <div class="operation-content">
              <el-button
                type="success"
                size="large"
                @click="loadNewsList"
                :loading="newsLoading"
                icon="Search"
                style="width: 100%; margin-bottom: 15px;"
              >
                {{ newsLoading ? '正在查询新闻...' : '查询新闻数据' }}
              </el-button>
              <div class="operation-description">
                <p>查询数据库中已存储的新闻数据</p>
                <p class="text-muted">• 分页展示新闻列表</p>
                <p class="text-muted">• 支持跳转到指定页面</p>
                <p class="text-muted">• 显示新闻详细内容</p>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 统计信息 -->
        <el-col :span="8">
          <el-card shadow="never" class="stats-card">
            <template #header>统计信息</template>
            <div class="stats-content">
              <div class="stat-item">
                <div class="stat-label">总新闻数</div>
                <div class="stat-value">{{ stats.total }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">今日新增</div>
                <div class="stat-value success">{{ stats.today_count }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">最新时间</div>
                <div class="stat-time">{{ stats.latest_time || '暂无数据' }}</div>
              </div>
            </div>
          </el-card>
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

      <!-- 新闻列表 -->
      <div class="news-list-container">
        <!-- 列表为空时的提示 -->
        <el-empty
          v-if="!newsLoading && newsList.length === 0"
          description="暂无新闻数据，请先爬取新闻"
          :image-size="120"
        >
          <el-button type="primary" @click="startCrawling">开始爬取</el-button>
        </el-empty>

        <!-- 新闻列表 -->
        <div v-else class="news-items">
          <el-card
            v-for="news in newsList"
            :key="news.id"
            class="news-item"
            shadow="hover"
          >
            <template #header>
              <div class="news-header">
                <div class="news-time">
                  <el-icon><Clock /></el-icon>
                  {{ news.time }}
                </div>
                <div class="news-id">ID: {{ news.id }}</div>
              </div>
            </template>

            <div class="news-content">
              <h3 class="news-title">{{ news.title }}</h3>
              <div class="news-body">
                <el-text
                  :line-clamp="3"
                  class="news-text"
                  :title="news.content"
                >
                  {{ news.content }}
                </el-text>
              </div>
              
              <!-- 展开/收起按钮 -->
              <div class="news-actions">
                <el-button
                  type="text"
                  size="small"
                  @click="toggleNewsExpansion(news.id)"
                >
                  {{ expandedNews.includes(news.id) ? '收起' : '展开全文' }}
                </el-button>
              </div>

              <!-- 完整内容（展开时显示） -->
              <div v-if="expandedNews.includes(news.id)" class="news-full-content">
                <el-divider />
                <div class="full-text">{{ news.content }}</div>
                <div class="news-meta">
                  <span class="meta-item">创建时间: {{ news.created_at }}</span>
                  <span class="meta-item">更新时间: {{ news.updated_at }}</span>
                  <span class="meta-item">时间戳: {{ news.ctime }}</span>
                </div>
              </div>
            </div>
          </el-card>
        </div>

        <!-- 分页器 -->
        <div v-if="pagination.total > 0" class="pagination-container">
          <el-pagination
            v-model:current-page="pagination.page"
            v-model:page-size="pagination.page_size"
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
import { crawlClsNewsApi, getClsNewsListApi, getClsNewsStatsApi } from '@/api'
import { ElMessage } from 'element-plus'
import { Clock } from '@element-plus/icons-vue'

export default {
  name: 'NewsAnalysis',
  components: {
    Clock
  },
  data() {
    return {
      // 系统状态
      systemStatus: {
        type: 'success',
        text: '系统正常'
      },
      
      // 爬取状态
      crawlLoading: false,
      
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
      },
      
      // 展开的新闻ID列表
      expandedNews: []
    }
  },
  
  async mounted() {
    await this.loadStats()
    await this.loadNewsList()
  },
  
  methods: {
    // 开始爬取新闻
    async startCrawling() {
      this.crawlLoading = true
      try {
        const response = await request.post(crawlClsNewsApi)
        
        if (response.code === 0) {
          ElMessage.success(response.message)
          // 等待一段时间后自动刷新统计和列表
          setTimeout(async () => {
            await this.loadStats()
            await this.loadNewsList()
          }, 10000) // 10秒后刷新
        } else {
          ElMessage.error(`爬取失败: ${response.message}`)
        }
      } catch (error) {
        console.error('爬取新闻失败:', error)
        ElMessage.error(`爬取新闻失败: ${error.message}`)
      } finally {
        this.crawlLoading = false
      }
    },
    
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
    
    // 切换新闻展开/收起
    toggleNewsExpansion(newsId) {
      const index = this.expandedNews.indexOf(newsId)
      if (index > -1) {
        // 收起
        this.expandedNews.splice(index, 1)
      } else {
        // 展开
        this.expandedNews.push(newsId)
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

.control-row {
  margin-bottom: 0;
}

.operation-card,
.stats-card {
  height: 280px;
}

.operation-card .el-card__body,
.stats-card .el-card__body {
  padding: 20px;
}

.operation-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.operation-description {
  flex: 1;
  margin-top: 10px;
}

.operation-description p {
  margin: 5px 0;
  font-size: 14px;
  line-height: 1.5;
}

.text-muted {
  color: #909399;
  font-size: 13px;
}

.stats-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  gap: 20px;
}

.stat-item {
  text-align: center;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 6px;
}

.stat-label {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #333;
}

.stat-value.success {
  color: #67c23a;
}

.stat-time {
  font-size: 13px;
  color: #409eff;
  font-weight: 500;
}

.news-list-container {
  min-height: 400px;
}

.news-items {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.news-item {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.news-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.news-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 14px;
}

.news-time {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #409eff;
  font-weight: 500;
}

.news-id {
  color: #909399;
  font-size: 12px;
}

.news-content {
  padding: 10px 0;
}

.news-title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
  margin: 0 0 15px 0;
  line-height: 1.4;
}

.news-body {
  margin-bottom: 15px;
}

.news-text {
  color: #606266;
  line-height: 1.6;
  font-size: 14px;
}

.news-actions {
  text-align: right;
  margin-bottom: 10px;
}

.news-full-content {
  margin-top: 15px;
}

.full-text {
  color: #606266;
  line-height: 1.8;
  font-size: 14px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 6px;
  margin-bottom: 15px;
}

.news-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  padding: 10px;
  background-color: #fafafa;
  border-radius: 4px;
  font-size: 12px;
  color: #909399;
}

.meta-item {
  white-space: nowrap;
}

.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 30px;
  padding: 20px 0;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .control-row .el-col {
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
  
  .news-header {
    flex-direction: column;
    gap: 5px;
    align-items: flex-start;
  }
  
  .news-meta {
    flex-direction: column;
    gap: 5px;
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
