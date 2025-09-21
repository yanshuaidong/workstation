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
        <el-col :span="6">
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

        <!-- AI 分析操作 -->
        <el-col :span="6">
          <el-card shadow="never" class="operation-card">
            <template #header>AI 分析</template>
            <div class="operation-content">
              <el-input-number
                v-model="analysisCount"
                :min="1"
                :max="100"
                size="large"
                style="width: 100%; margin-bottom: 10px;"
                placeholder="分析数量"
              />
              <el-button
                type="warning"
                size="large"
                @click="startBatchAnalysis"
                :loading="analysisLoading"
                icon="BrainIcon"
                style="width: 100%; margin-bottom: 15px;"
              >
                {{ analysisLoading ? '正在AI分析...' : '批量AI分析' }}
              </el-button>
              <div class="operation-description">
                <p>对最新的未分析新闻进行AI分析</p>
                <p class="text-muted">• 判断硬消息/软消息</p>
                <p class="text-muted">• 自动保存分析结果</p>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 查询操作 -->
        <el-col :span="6">
          <el-card shadow="never" class="operation-card">
            <template #header>数据查询</template>
            <div class="operation-content">
              <el-button
                type="success"
                size="large"
                @click="loadAnalysisResults"
                :loading="analysisResultsLoading"
                icon="Search"
                style="width: 100%; margin-bottom: 15px;"
              >
                {{ analysisResultsLoading ? '正在查询...' : '查询分析结果' }}
              </el-button>
              <div class="operation-description">
                <p>查询数据库中已分析的新闻数据</p>
                <p class="text-muted">• 分页展示分析结果</p>
                <p class="text-muted">• 支持单独分析操作</p>
                <p class="text-muted">• 显示AI分析内容</p>
              </div>
            </div>
          </el-card>
        </el-col>

        <!-- 统计信息 -->
        <el-col :span="6">
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

      <!-- 提示词管理区块 -->
      <el-row :gutter="20" class="control-row" style="margin-top: 20px;">
        <el-col :span="24">
          <el-card shadow="never" class="prompt-card">
            <template #header>AI 分析提示词管理</template>
            <div class="prompt-content">
              <el-input
                v-model="aiPrompt"
                type="textarea"
                :rows="3"
                placeholder="请输入AI分析提示词，例如：请分析这条财经新闻是硬消息还是软消息，并简要说明原因。"
                style="width: 100%; margin-bottom: 15px;"
              />
              <el-button
                type="primary"
                @click="savePrompt"
                icon="DocumentAdd"
                style="margin-right: 10px;"
              >
                保存提示词
              </el-button>
              <el-button
                type="info"
                @click="resetPrompt"
                icon="RefreshRight"
              >
                重置为默认
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- AI 分析结果展示区块 -->
    <el-card class="news-list-card">
      <template #header>
        <div class="card-header">
          <span>AI 分析结果</span>
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
              @click="loadAnalysisResults"
              :loading="analysisResultsLoading"
              icon="Refresh"
            >
              刷新结果
            </el-button>
          </div>
        </div>
      </template>

      <!-- 数据表格 -->
      <div class="analysis-table-container">
        <!-- 表格为空时的提示 -->
        <el-empty
          v-if="!analysisResultsLoading && analysisResults.length === 0"
          description="暂无AI分析结果，请先进行AI分析"
          :image-size="120"
        >
          <el-button type="warning" @click="startBatchAnalysis">开始AI分析</el-button>
        </el-empty>

        <!-- 分析结果表格 -->
        <el-table
          v-else
          :data="analysisResults"
          v-loading="analysisResultsLoading"
          stripe
          border
          style="width: 100%"
          max-height="600"
          empty-text="暂无分析结果"
        >
          <el-table-column type="index" label="序号" width="60" :index="(index) => index + 1" />
          
          <el-table-column prop="time" label="时间" width="180" />
          
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
          
          <el-table-column label="AI 分析结果" min-width="300">
            <template #default="scope">
              <div class="analysis-result">
                <el-text
                  :line-clamp="2"
                  class="analysis-text"
                  :title="scope.row.ai_analysis"
                >
                  {{ scope.row.ai_analysis || '暂无分析结果' }}
                </el-text>
                <div class="analysis-actions" style="margin-top: 8px;">
                  <el-button
                    size="small"
                    type="text"
                    @click="toggleAnalysisExpansion(scope.row.id)"
                  >
                    {{ expandedAnalysis.includes(scope.row.id) ? '收起' : '展开' }}
                  </el-button>
                  <el-button
                    size="small"
                    type="primary"
                    @click="analyzeSingleNews(scope.row)"
                    :loading="scope.row.analyzing"
                  >
                    单独分析
                  </el-button>
                </div>
                
                <!-- 展开的完整分析内容 -->
                <div v-if="expandedAnalysis.includes(scope.row.id)" class="full-analysis">
                  <el-divider />
                  <div class="full-analysis-text">{{ scope.row.ai_analysis }}</div>
                  <div class="news-meta">
                    <p><strong>完整标题:</strong> {{ scope.row.title }}</p>
                    <p><strong>新闻内容:</strong> {{ scope.row.content }}</p>
                    <p><strong>创建时间:</strong> {{ scope.row.created_at }}</p>
                    <p><strong>更新时间:</strong> {{ scope.row.updated_at }}</p>
                  </div>
                </div>
              </div>
            </template>
          </el-table-column>
        </el-table>

        <!-- 分页器 -->
        <div v-if="analysisPagination.total > 0" class="pagination-container">
          <el-pagination
            v-model:current-page="analysisPagination.page"
            v-model:page-size="analysisPagination.page_size"
            :page-sizes="[10, 20, 50, 100]"
            :total="analysisPagination.total"
            layout="total, sizes, prev, pager, next, jumper"
            @size-change="handleAnalysisSizeChange"
            @current-change="handleAnalysisCurrentChange"
            background
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import request from '@/utils/request'
import { crawlClsNewsApi, getClsNewsListApi, getClsNewsStatsApi, analyzeBatchNewsApi, analyzeSingleNewsApi, getNewsListWithAnalysisApi } from '@/api'
import { ElMessage } from 'element-plus'

export default {
  name: 'NewsAnalysis',
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
      
      // AI 分析相关
      analysisCount: 5, // 默认分析5条
      analysisLoading: false,
      aiPrompt: '', // AI 分析提示词
      
      // AI 分析结果
      analysisResults: [],
      analysisResultsLoading: false,
      
      // 统计信息
      stats: {
        total: 0,
        today_count: 0,
        latest_time: '',
        earliest_time: ''
      },
      statsLoading: false,
      
      // 分页信息（原有新闻列表）
      pagination: {
        page: 1,
        page_size: 10,
        total: 0,
        total_pages: 0,
        has_prev: false,
        has_next: false
      },
      
      // AI 分析结果分页信息
      analysisPagination: {
        page: 1,
        page_size: 10,
        total: 0,
        total_pages: 0,
        has_prev: false,
        has_next: false
      },
      
      // 展开的新闻ID列表
      expandedNews: [],
      
      // 展开的分析结果ID列表
      expandedAnalysis: []
    }
  },
  
  async mounted() {
    await this.loadStats()
    await this.loadNewsList()
    await this.loadAnalysisResults()
    this.initializeAiPrompt()
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
    },
    
    // === AI 分析相关方法 ===
    
    // 初始化AI提示词
    initializeAiPrompt() {
      const savedPrompt = localStorage.getItem('ai_analysis_prompt')
      if (savedPrompt) {
        this.aiPrompt = savedPrompt
      } else {
        this.aiPrompt = '请分析这条财经新闻是硬消息还是软消息，并简要说明原因。'
      }
    },
    
    // 保存提示词
    savePrompt() {
      if (!this.aiPrompt.trim()) {
        ElMessage.warning('提示词不能为空')
        return
      }
      
      localStorage.setItem('ai_analysis_prompt', this.aiPrompt.trim())
      ElMessage.success('提示词已保存')
    },
    
    // 重置提示词为默认值
    resetPrompt() {
      this.aiPrompt = '请分析这条财经新闻是硬消息还是软消息，并简要说明原因。'
      localStorage.setItem('ai_analysis_prompt', this.aiPrompt)
      ElMessage.success('提示词已重置为默认值')
    },
    
    // 开始批量AI分析
    async startBatchAnalysis() {
      if (!this.aiPrompt.trim()) {
        ElMessage.warning('请先设置AI分析提示词')
        return
      }
      
      this.analysisLoading = true
      try {
        const response = await request.post(analyzeBatchNewsApi, {
          prompt: this.aiPrompt.trim(),
          count: this.analysisCount
        })
        
        if (response.code === 0) {
          ElMessage.success(response.message)
          // 等待一段时间后自动刷新分析结果
          setTimeout(async () => {
            await this.loadAnalysisResults()
          }, 15000) // 15秒后刷新
        } else {
          ElMessage.error(`分析失败: ${response.message}`)
        }
      } catch (error) {
        console.error('批量AI分析失败:', error)
        ElMessage.error(`批量AI分析失败: ${error.message}`)
      } finally {
        this.analysisLoading = false
      }
    },
    
    // 单条新闻分析
    async analyzeSingleNews(newsItem) {
      if (!this.aiPrompt.trim()) {
        ElMessage.warning('请先设置AI分析提示词')
        return
      }
      
      // 设置该条新闻的加载状态
      newsItem.analyzing = true
      
      try {
        const response = await request.post(analyzeSingleNewsApi, {
          prompt: this.aiPrompt.trim(),
          news_id: newsItem.id
        })
        
        if (response.code === 0) {
          ElMessage.success(response.message)
          // 等待一段时间后自动刷新这条新闻的分析结果
          setTimeout(async () => {
            await this.loadAnalysisResults()
          }, 10000) // 10秒后刷新
        } else {
          ElMessage.error(`分析失败: ${response.message}`)
        }
      } catch (error) {
        console.error('单条AI分析失败:', error)
        ElMessage.error(`单条AI分析失败: ${error.message}`)
      } finally {
        newsItem.analyzing = false
      }
    },
    
    // 加载AI分析结果
    async loadAnalysisResults() {
      this.analysisResultsLoading = true
      try {
        const params = new URLSearchParams({
          page: this.analysisPagination.page,
          page_size: this.analysisPagination.page_size
        })
        
        const response = await request.get(`${getNewsListWithAnalysisApi}?${params}`)
        
        if (response.code === 0) {
          this.analysisResults = response.data.news_list || []
          this.analysisPagination = { ...this.analysisPagination, ...response.data.pagination }
          
          if (this.analysisResults.length > 0) {
            ElMessage.success(`加载成功，共 ${this.analysisPagination.total} 条分析结果`)
          }
        } else {
          ElMessage.error(`查询失败: ${response.message}`)
        }
      } catch (error) {
        console.error('查询分析结果失败:', error)
        ElMessage.error(`查询分析结果失败: ${error.message}`)
      } finally {
        this.analysisResultsLoading = false
      }
    },
    
    // 切换分析结果展开/收起
    toggleAnalysisExpansion(newsId) {
      const index = this.expandedAnalysis.indexOf(newsId)
      if (index > -1) {
        // 收起
        this.expandedAnalysis.splice(index, 1)
      } else {
        // 展开
        this.expandedAnalysis.push(newsId)
      }
    },
    
    // AI 分析结果分页大小变化
    handleAnalysisSizeChange(newSize) {
      this.analysisPagination.page_size = newSize
      this.analysisPagination.page = 1 // 重置到第一页
      this.loadAnalysisResults()
    },
    
    // AI 分析结果当前页变化
    handleAnalysisCurrentChange(newPage) {
      this.analysisPagination.page = newPage
      this.loadAnalysisResults()
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

/* AI 分析相关样式 */
.prompt-card {
  margin-bottom: 20px;
}

.prompt-content {
  padding: 10px 0;
}

.analysis-table-container {
  min-height: 400px;
}

.title-cell {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 200px;
}

.analysis-result {
  padding: 5px 0;
}

.analysis-text {
  color: #606266;
  line-height: 1.6;
  font-size: 14px;
}

.analysis-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.full-analysis {
  margin-top: 15px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 6px;
}

.full-analysis-text {
  color: #303133;
  line-height: 1.8;
  font-size: 14px;
  margin-bottom: 15px;
  padding: 10px;
  background-color: #fff;
  border-radius: 4px;
  border-left: 4px solid #409eff;
}

.news-meta p {
  margin: 8px 0;
  color: #606266;
  font-size: 13px;
  line-height: 1.5;
}

.news-meta strong {
  color: #303133;
  font-weight: 600;
}
</style>
