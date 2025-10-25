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
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ stats.total }}</div>
              <div class="stat-label">总新闻数</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-value success">{{ stats.today_count }}</div>
              <div class="stat-label">今日新增</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ stats.latest_time || '暂无数据' }}</div>
              <div class="stat-label">最新时间</div>
            </div>
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card shadow="hover" class="stat-card">
            <div class="stat-content">
              <div class="stat-value">{{ stats.earliest_time || '暂无数据' }}</div>
              <div class="stat-label">最早时间</div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </el-card>

    <!-- 搜索和筛选区域 -->
    <el-card class="filter-card">
      <!-- 第一行：时间范围选择 -->
      <el-row :gutter="20" class="filter-row">
        <el-col :span="8">
          <el-date-picker
            v-model="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            @change="handleDateRangeChange"
            style="width: 100%"
          />
        </el-col>
        <el-col :span="6">
          <el-select
            v-model="quickDateRange"
            placeholder="快捷选择"
            @change="handleQuickDateRange"
          >
            <el-option label="今天" value="today" />
            <el-option label="最近3天" value="three_days" />
            <el-option label="最近7天" value="week" />
            <el-option label="最近1个月" value="month" />
            <el-option label="全部" value="all" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-select
            v-model="searchForm.message_label"
            placeholder="选择消息软硬度"
            clearable
            @change="handleSearch"
          >
            <el-option label="硬消息" value="hard" />
            <el-option label="软消息" value="soft" />
            <el-option label="未知" value="unknown" />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-button type="success" @click="showCreateDialog" icon="Plus">
            新增消息
          </el-button>
        </el-col>
      </el-row>

      <!-- 第二行：关键词搜索 -->
      <el-row :gutter="20" class="filter-row">
        <el-col :span="6">
          <el-select
            v-model="searchForm.search_field"
            placeholder="选择搜索字段"
          >
            <el-option label="标题" value="title" />
            <el-option label="内容" value="content" />
            <el-option label="消息类型" value="message_type" />
            <el-option label="市场反应" value="market_react" />
          </el-select>
        </el-col>
        <el-col :span="10">
          <el-input
            v-model="searchForm.search"
            :placeholder="getSearchPlaceholder()"
            clearable
            @keyup.enter="handleSearch"
            @clear="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="8">
          <el-button type="primary" @click="handleSearch" :loading="newsLoading">
            <el-icon><Search /></el-icon>
            搜索
          </el-button>
          <el-button @click="resetSearch">重置</el-button>
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
              type="warning"
              size="small"
              @click="copyCurrentPage"
              :loading="copyLoading"
              icon="DocumentCopy"
            >
              <!-- 注意：这里使用 icon="DocumentCopy" 属性，不需要在 components 中注册 DocumentCopy 组件 -->
              复制当前页
            </el-button>
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
          
          <!-- 第2列：精准时间 -->
          <el-table-column label="精准时间" width="130">
            <template #default="scope">
              {{ formatPreciseTime(scope.row.time) }}
            </template>
          </el-table-column>
          
          <!-- 第3列：模糊时间 -->
          <el-table-column label="模糊时间" width="100">
            <template #default="scope">
              {{ formatVagueTime(scope.row.time) }}
            </template>
          </el-table-column>
          
          <!-- 第4列：标题 -->
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
          
          <!-- 第4列：消息软硬度标签 -->
          <el-table-column label="消息软硬度" width="160" align="center">
            <template #default="scope">
              <el-select
                v-model="scope.row.message_label"
                size="small"
                @change="updateMessageLabel(scope.row)"
                style="width: 100px"
              >
                <el-option label="硬消息" value="hard">
                  <el-tag type="success" size="small">硬消息</el-tag>
                </el-option>
                <el-option label="软消息" value="soft">
                  <el-tag type="info" size="small">软消息</el-tag>
                </el-option>
                <el-option label="未知" value="unknown">
                  <el-tag type="warning" size="small">未知</el-tag>
                </el-option>
              </el-select>
            </template>
          </el-table-column>
          
          <!-- 第5列：消息分数 -->
          <el-table-column label="分数" width="120" align="center">
            <template #default="scope">
              <el-input-number
                v-model="scope.row.message_score"
                :min="0"
                :max="10"
                size="small"
                @change="updateMessageScore(scope.row)"
                style="width: 80px"
              />
            </template>
          </el-table-column>
          
          <!-- 第6列：消息类型 -->
          <el-table-column label="消息类型" width="140">
            <template #default="scope">
              <el-tag v-if="scope.row.message_type" type="primary" size="small">
                {{ scope.row.message_type }}
              </el-tag>
              <span v-else class="text-gray">未分类</span>
            </template>
          </el-table-column>
          
          <!-- 第7列：市场反应 -->
          <el-table-column label="市场反应" width="120">
            <template #default="scope">
              <el-text
                v-if="scope.row.market_react"
                :line-clamp="1"
                class="market-react-text"
                :title="scope.row.market_react"
              >
                {{ scope.row.market_react }}
              </el-text>
              <span v-else class="text-gray">-</span>
            </template>
          </el-table-column>
          
          <!-- 第8列：截图 -->
          <el-table-column label="截图" width="80" align="center">
            <template #default="scope">
              <el-badge
                v-if="scope.row.screenshots && scope.row.screenshots.length > 0"
                :value="scope.row.screenshots.length"
                type="primary"
              >
                <el-icon size="20" color="#409eff">
                  <Picture />
                </el-icon>
              </el-badge>
              <span v-else class="text-gray">-</span>
            </template>
          </el-table-column>
          
          <!-- 第9列：操作 -->
          <el-table-column label="操作" width="150" align="center" fixed="right">
            <template #default="scope">
              <el-button
                type="primary"
                size="small"
                @click="showEditDialog(scope.row, scope.$index)"
                icon="Edit"
              >
                编辑
              </el-button>
              <!-- <el-button
                type="danger"
                size="small"
                @click="confirmDelete(scope.row)"
                icon="Delete"
              >
                删除
              </el-button> -->
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

    <!-- 新增/编辑新闻对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新增消息' : '编辑消息'"
      width="80%"
      :before-close="handleCloseDialog"
    >
      <!-- 编辑模式下的导航栏 -->
      <div v-if="dialogMode === 'edit'" class="edit-navigation">
        <div class="nav-info">
          <span class="nav-position">第 {{ currentEditIndex + 1 }} 条，共 {{ newsList.length }} 条</span>
          <span class="nav-tips">切换时未保存的修改将丢失</span>
        </div>
        <div class="nav-controls">
          <el-button
            size="small"
            :disabled="currentEditIndex <= 0"
            @click="navigateToItem(currentEditIndex - 1)"
            icon="ArrowLeft"
          >
            上一条
          </el-button>
          <el-button
            size="small"
            :disabled="currentEditIndex >= newsList.length - 1"
            @click="navigateToItem(currentEditIndex + 1)"
            icon="ArrowRight"
          >
            下一条
          </el-button>
        </div>
      </div>

      <el-form
        ref="newsFormRef"
        :model="newsForm"
        :rules="newsFormRules"
        label-width="120px"
      >
        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="标题" prop="title">
              <el-input
                v-model="newsForm.title"
                placeholder="请输入新闻标题"
                maxlength="500"
                show-word-limit
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="内容" prop="content">
              <div class="content-with-copy">
                <el-input
                  v-model="newsForm.content"
                  type="textarea"
                  :rows="10"
                  placeholder="请输入新闻内容"
                  maxlength="10000"
                  show-word-limit
                />
                <el-button
                  type="primary"
                  size="small"
                  @click="copySingleContent"
                  icon="DocumentCopy"
                  style="margin-top: 8px; align-self: flex-start;"
                >
                  <!-- 注意：这里使用 icon="DocumentCopy" 属性，不需要在 components 中注册 DocumentCopy 组件 -->
                  复制内容
                </el-button>
              </div>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="AI分析/备注">
              <el-input
                v-model="newsForm.ai_analysis"
                type="textarea"
                :rows="4"
                placeholder="请输入AI分析结果或备注信息..."
                maxlength="5000"
                show-word-limit
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="消息分数">
              <el-slider
                v-model="newsForm.message_score"
                :min="0"
                :max="10"
                show-input
                input-size="small"
              />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="消息标签">
              <el-radio-group v-model="newsForm.message_label">
                <el-radio-button label="hard">
                  <el-tag type="success" size="small">硬消息</el-tag>
                </el-radio-button>
                <el-radio-button label="soft">
                  <el-tag type="info" size="small">软消息</el-tag>
                </el-radio-button>
                <el-radio-button label="unknown">
                  <el-tag type="warning" size="small">未知</el-tag>
                </el-radio-button>
              </el-radio-group>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="消息类型">
              <el-select
                v-model="newsForm.message_type"
                placeholder="选择或输入类型"
                filterable
                allow-create
                clearable
              >
                <el-option label="利好政策" value="利好政策" />
                <el-option label="并购落地" value="并购落地" />
                <el-option label="减持公告" value="减持公告" />
                <el-option label="业绩预告" value="业绩预告" />
                <el-option label="重组消息" value="重组消息" />
                <el-option label="监管动态" value="监管动态" />
                <el-option label="行业消息" value="行业消息" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="市场反应">
              <el-input
                v-model="newsForm.market_react"
                placeholder="请输入市场反应情况，如：大涨、大跌、没反应等"
                maxlength="255"
                show-word-limit
              />
            </el-form-item>
          </el-col>
        </el-row>

        <el-row :gutter="20">
          <el-col :span="24">
            <el-form-item label="截图上传">
              <div class="upload-area">
                <el-upload
                  ref="uploadRef"
                  :auto-upload="false"
                  :on-change="handleFileChange"
                  :on-remove="handleFileRemove"
                  list-type="picture-card"
                  :limit="10"
                  accept="image/*"
                >
                  <el-icon><Plus /></el-icon>
                </el-upload>
                <div class="upload-tip">
                  <p>支持jpg、png等格式，最多上传10张图片</p>
                  <p>图片将自动上传到阿里云OSS</p>
                </div>
              </div>
              
              <!-- 已有截图预览 -->
              <div v-if="existingScreenshots.length > 0" class="existing-screenshots">
                <h4>现有截图:</h4>
                <div class="screenshot-grid">
                  <div
                    v-for="(screenshot, index) in existingScreenshots"
                    :key="index"
                    class="screenshot-item"
                  >
                    <el-image
                      :src="screenshot.url"
                      :preview-src-list="existingScreenshots.map(s => s.url)"
                      :initial-index="index"
                      fit="cover"
                      class="screenshot-image"
                      lazy
                    />
                    <div class="screenshot-actions">
                      <el-button
                        type="danger"
                        size="small"
                        icon="Delete"
                        circle
                        @click="removeExistingScreenshot(index)"
                      />
                    </div>
                  </div>
                </div>
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleCloseDialog">取消</el-button>
          <el-button
            type="primary"
            @click="handleSubmit"
            :loading="submitLoading"
          >
            {{ dialogMode === 'create' ? '创建' : '保存' }}
          </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import request from '@/utils/request'
import { 
  getClsNewsListApi, 
  getClsNewsStatsApi, 
  createNewsApi, 
  getNewsDetailApi, 
  updateNewsApi, 
  deleteNewsApi,
  getOssUploadUrlApi 
} from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Plus, Picture } from '@element-plus/icons-vue'

export default {
  name: 'NewsAnalysis',
  components: {
    Search,
    Plus,
    Picture
  },
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
      
      // 复制状态
      copyLoading: false,
      
      // 分页信息
      pagination: {
        page: 1,
        page_size: 10,
        total: 0,
        total_pages: 0,
        has_prev: false,
        has_next: false
      },

      // 搜索表单
      searchForm: {
        search: '',
        search_field: 'title',
        message_label: '',
        start_date: '',
        end_date: ''
      },

      // 日期范围选择
      dateRange: [],
      quickDateRange: 'month',

      // 对话框相关
      dialogVisible: false,
      dialogMode: 'create', // 'create' 或 'edit'
      submitLoading: false,
      currentEditId: null,
      currentEditIndex: -1, // 当前编辑项在列表中的索引

      // 新闻表单
      newsForm: {
        title: '',
        content: '',
        ai_analysis: '',
        message_score: 50,
        message_label: 'unknown',
        message_type: '',
        market_react: '',
        screenshots: []
      },

      // 表单验证规则
      newsFormRules: {
        title: [
          { required: true, message: '请输入新闻标题', trigger: 'blur' },
          { min: 5, max: 500, message: '标题长度应在5-500字符之间', trigger: 'blur' }
        ],
        content: [
          { required: true, message: '请输入新闻内容', trigger: 'blur' },
          { min: 10, message: '内容至少需要10个字符', trigger: 'blur' }
        ]
      },

      // 文件上传相关
      uploadFiles: [],
      existingScreenshots: [],
      
    }
  },
  
  async mounted() {
    // 初始化日期范围为最近1个月
    this.initDefaultDateRange()
    await this.loadStats()
    await this.loadNewsList()
  },
  
  methods: {
    // 格式化精准时间：10月25日06:30
    formatPreciseTime(timeString) {
      if (!timeString) return '-'
      
      try {
        const date = new Date(timeString)
        const month = date.getMonth() + 1
        const day = date.getDate()
        const hours = date.getHours().toString().padStart(2, '0')
        const minutes = date.getMinutes().toString().padStart(2, '0')
        
        return `${month}月${day}日${hours}:${minutes}`
      } catch (error) {
        console.error('精准时间格式化失败:', error)
        return timeString
      }
    },
    
    // 格式化模糊时间：周六上午
    formatVagueTime(timeString) {
      if (!timeString) return '-'
      
      try {
        const date = new Date(timeString)
        
        // 获取星期
        const weekDays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
        const weekDay = weekDays[date.getDay()]
        
        // 获取小时
        const hours = date.getHours()
        
        // 判断时间段
        let timePeriod = ''
        if (hours >= 0 && hours < 6) {
          timePeriod = '凌晨'
        } else if (hours >= 6 && hours < 12) {
          timePeriod = '上午'
        } else if (hours >= 12 && hours < 14) {
          timePeriod = '中午'
        } else if (hours >= 14 && hours < 18) {
          timePeriod = '下午'
        } else if (hours >= 18 && hours < 19) {
          timePeriod = '傍晚'
        } else {
          timePeriod = '晚上'
        }
        
        return `${weekDay}${timePeriod}`
      } catch (error) {
        console.error('模糊时间格式化失败:', error)
        return timeString
      }
    },
    
    // 加载新闻列表
    async loadNewsList() {
      this.newsLoading = true
      try {
        const params = new URLSearchParams({
          page: this.pagination.page,
          page_size: this.pagination.page_size,
          ...this.searchForm
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

    // 搜索处理
    handleSearch() {
      this.pagination.page = 1 // 重置到第一页
      this.loadNewsList()
    },

    // 重置搜索
    resetSearch() {
      this.searchForm = {
        search: '',
        search_field: 'title',
        message_label: '',
        start_date: '',
        end_date: ''
      }
      this.quickDateRange = 'month'
      this.initDefaultDateRange()
      this.handleSearch()
    },

    // 初始化默认日期范围（最近1个月）
    initDefaultDateRange() {
      const today = new Date()
      const oneMonthAgo = new Date()
      oneMonthAgo.setMonth(today.getMonth() - 1)
      
      this.dateRange = [
        oneMonthAgo.toISOString().split('T')[0],
        today.toISOString().split('T')[0]
      ]
      
      this.searchForm.start_date = this.dateRange[0]
      this.searchForm.end_date = this.dateRange[1]
    },

    // 处理日期范围变化
    handleDateRangeChange(dateRange) {
      if (dateRange && dateRange.length === 2) {
        this.searchForm.start_date = dateRange[0]
        this.searchForm.end_date = dateRange[1]
      } else {
        this.searchForm.start_date = ''
        this.searchForm.end_date = ''
      }
      this.quickDateRange = '' // 清空快捷选择
      this.handleSearch()
    },

    // 处理快捷日期范围选择
    handleQuickDateRange(value) {
      const today = new Date()
      let startDate = new Date()
      
      switch (value) {
        case 'today':
          startDate = new Date(today)
          break
        case 'three_days':
          startDate.setDate(today.getDate() - 3)
          break
        case 'week':
          startDate.setDate(today.getDate() - 7)
          break
        case 'month':
          startDate.setMonth(today.getMonth() - 1)
          break
        case 'all':
          this.dateRange = []
          this.searchForm.start_date = ''
          this.searchForm.end_date = ''
          this.handleSearch()
          return
      }
      
      this.dateRange = [
        startDate.toISOString().split('T')[0],
        today.toISOString().split('T')[0]
      ]
      
      this.searchForm.start_date = this.dateRange[0]
      this.searchForm.end_date = this.dateRange[1]
      this.handleSearch()
    },

    // 获取搜索占位符文本
    getSearchPlaceholder() {
      const placeholderMap = {
        'title': '搜索新闻标题...',
        'content': '搜索新闻内容...',
        'message_type': '搜索消息类型...',
        'market_react': '搜索市场反应...'
      }
      return placeholderMap[this.searchForm.search_field] || '搜索...'
    },

    // 快速更新消息标签
    async updateMessageLabel(row) {
      try {
        const response = await request.put(`${updateNewsApi}/${row.id}`, {
          message_label: row.message_label
        })
        
        if (response.code === 0) {
          ElMessage.success('消息标签已更新')
        } else {
          ElMessage.error('更新失败: ' + response.message)
          // 恢复原值
          this.loadNewsList()
        }
      } catch (error) {
        ElMessage.error('更新失败: ' + error.message)
        this.loadNewsList()
      }
    },

    // 快速更新消息分数
    async updateMessageScore(row) {
      try {
        const response = await request.put(`${updateNewsApi}/${row.id}`, {
          message_score: row.message_score
        })
        
        if (response.code === 0) {
          ElMessage.success('消息分数已更新')
        } else {
          ElMessage.error('更新失败: ' + response.message)
          this.loadNewsList()
        }
      } catch (error) {
        ElMessage.error('更新失败: ' + error.message)
        this.loadNewsList()
      }
    },

    // 显示新增对话框
    showCreateDialog() {
      this.dialogMode = 'create'
      this.currentEditId = null
      this.currentEditIndex = -1 // 重置编辑索引
      this.resetForm()
      this.dialogVisible = true
    },

    // 显示编辑对话框
    async showEditDialog(row, index = null) {
      this.dialogMode = 'edit'
      this.currentEditId = row.id
      
      // 设置当前编辑索引
      if (index !== null) {
        this.currentEditIndex = index
      } else {
        // 如果没有传递索引，则查找
        const findIndex = this.newsList.findIndex(item => item.id === row.id)
        this.currentEditIndex = findIndex !== -1 ? findIndex : this.currentEditIndex
      }
      
      try {
        // 获取详细信息
        const response = await request.get(`${getNewsDetailApi}/${row.id}`)
        
        if (response.code === 0) {
          const data = response.data
          this.newsForm = {
            title: data.title,
            content: data.content,
            ai_analysis: data.ai_analysis || '',
            message_score: data.message_score || 50,
            message_label: data.message_label || 'unknown',
            message_type: data.message_type || '',
            market_react: data.market_react || '',
            screenshots: []
          }
          
          // 设置现有截图
          this.existingScreenshots = data.screenshots || []
          
          this.dialogVisible = true
        } else {
          ElMessage.error('获取新闻详情失败: ' + response.message)
        }
      } catch (error) {
        ElMessage.error('获取新闻详情失败: ' + error.message)
      }
    },

    // 确认删除
    confirmDelete(row) {
      ElMessageBox.confirm(
        `确定要删除新闻"${row.title}"吗？删除后无法恢复！`,
        '确认删除',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning',
        }
      ).then(async () => {
        await this.deleteNews(row.id)
      })
    },

    // 删除新闻
    async deleteNews(newsId) {
      try {
        const response = await request.delete(`${deleteNewsApi}/${newsId}`)
        
        if (response.code === 0) {
          ElMessage.success('删除成功')
          await this.loadNewsList()
          await this.loadStats()
        } else {
          ElMessage.error('删除失败: ' + response.message)
        }
      } catch (error) {
        ElMessage.error('删除失败: ' + error.message)
      }
    },

    // 重置表单
    resetForm() {
      this.newsForm = {
        title: '',
        content: '',
        ai_analysis: '',
        message_score: 50,
        message_label: 'unknown',
        message_type: '',
        market_react: '',
        screenshots: []
      }
      this.uploadFiles = []
      this.existingScreenshots = []
      
      // 清空表单验证
      this.$nextTick(() => {
        if (this.$refs.newsFormRef) {
          this.$refs.newsFormRef.clearValidate()
        }
        // 清除上传组件中的文件列表
        if (this.$refs.uploadRef) {
          this.$refs.uploadRef.clearFiles()
        }
      })
    },

    // 关闭对话框
    handleCloseDialog() {
      this.dialogVisible = false
      this.currentEditIndex = -1
      this.resetForm()
    },

    // 文件变化处理
    handleFileChange(file, fileList) {
      this.uploadFiles = fileList
    },

    // 文件移除处理
    handleFileRemove(file, fileList) {
      this.uploadFiles = fileList
    },

    // 移除现有截图
    removeExistingScreenshot(index) {
      this.existingScreenshots.splice(index, 1)
    },

    // 上传文件到OSS
    async uploadFileToOss(file, newsId) {
      try {
        // 获取上传签名URL
        const uploadResponse = await request.post(getOssUploadUrlApi, {
          news_id: newsId,
          filename: file.name,
          content_type: file.raw.type
        })

        if (uploadResponse.code !== 0) {
          throw new Error(uploadResponse.message)
        }

        const { upload_url, object_key } = uploadResponse.data

        // 上传文件到OSS
        const formData = new FormData()
        formData.append('file', file.raw)

        await fetch(upload_url, {
          method: 'PUT',
          body: file.raw,
          headers: {
            'Content-Type': file.raw.type
          }
        })

        return object_key
      } catch (error) {
        console.error('文件上传失败:', error)
        throw error
      }
    },

    // 提交表单
    async handleSubmit() {
      try {
        // 表单验证
        await this.$refs.newsFormRef.validate()
        
        this.submitLoading = true
        
        let newsId = this.currentEditId
        let screenshotKeys = []

        // 如果是新增，先创建新闻获取ID
        if (this.dialogMode === 'create') {
          const createResponse = await request.post(createNewsApi, {
            title: this.newsForm.title,
            content: this.newsForm.content,
            ai_analysis: this.newsForm.ai_analysis,
            message_score: this.newsForm.message_score,
            message_label: this.newsForm.message_label,
            message_type: this.newsForm.message_type,
            market_react: this.newsForm.market_react
          })

          if (createResponse.code !== 0) {
            throw new Error(createResponse.message)
          }

          newsId = createResponse.data.id
        }

        // 上传新文件
        if (this.uploadFiles.length > 0) {
          for (const file of this.uploadFiles) {
            try {
              const objectKey = await this.uploadFileToOss(file, newsId)
              screenshotKeys.push(objectKey)
            } catch (error) {
              ElMessage.error(`文件 ${file.name} 上传失败: ${error.message}`)
            }
          }
        }

        // 合并现有截图和新上传的截图
        const allScreenshots = [
          ...this.existingScreenshots.map(s => s.key),
          ...screenshotKeys
        ]

        // 更新新闻信息（包括截图）
        const updateData = {
          ...this.newsForm,
          screenshots: allScreenshots
        }

        const updateResponse = await request.put(`${updateNewsApi}/${newsId}`, updateData)

        if (updateResponse.code !== 0) {
          throw new Error(updateResponse.message)
        }

        ElMessage.success(this.dialogMode === 'create' ? '创建成功' : '更新成功')
        this.handleCloseDialog()
        await this.loadNewsList()
        await this.loadStats()

      } catch (error) {
        if (error.message) {
          ElMessage.error(error.message)
        } else {
          ElMessage.error('提交失败，请检查表单数据')
        }
      } finally {
        this.submitLoading = false
      }
    },

    // 导航到指定索引的新闻
    navigateToItem(index) {
      this.currentEditIndex = index
      this.showEditDialog(this.newsList[index])
    },

    // 通用复制方法（兼容HTTP和HTTPS）
    async copyToClipboard(text) {
      try {
        // 优先使用现代 Clipboard API（仅在 HTTPS 或 localhost 下可用）
        if (navigator.clipboard && window.isSecureContext) {
          await navigator.clipboard.writeText(text)
          return true
        } else {
          // 降级方案：使用传统的 execCommand 方法
          return this.fallbackCopyTextToClipboard(text)
        }
      } catch (error) {
        console.error('复制失败:', error)
        // 如果现代API失败，尝试降级方案
        return this.fallbackCopyTextToClipboard(text)
      }
    },

    // 降级复制方案
    fallbackCopyTextToClipboard(text) {
      try {
        // 创建一个临时的 textarea 元素
        const textArea = document.createElement('textarea')
        textArea.value = text
        
        // 设置样式使其不可见
        textArea.style.position = 'fixed'
        textArea.style.top = '0'
        textArea.style.left = '0'
        textArea.style.width = '2em'
        textArea.style.height = '2em'
        textArea.style.padding = '0'
        textArea.style.border = 'none'
        textArea.style.outline = 'none'
        textArea.style.boxShadow = 'none'
        textArea.style.background = 'transparent'
        textArea.style.opacity = '0'
        
        document.body.appendChild(textArea)
        textArea.focus()
        textArea.select()
        
        // 尝试复制
        const successful = document.execCommand('copy')
        document.body.removeChild(textArea)
        
        return successful
      } catch (error) {
        console.error('降级复制方案也失败了:', error)
        return false
      }
    },

    // 复制当前页新闻内容
    async copyCurrentPage() {
      if (!this.newsList.length) {
        ElMessage.warning('当前页面没有新闻数据可复制')
        return
      }

      this.copyLoading = true
      try {
        // 构建复制内容
        const copyContent = this.newsList
          .map((item, index) => `${index + 1}、${item.content}`)
          .join('\n\n')
        
        const success = await this.copyToClipboard(copyContent)
        
        if (success) {
          ElMessage.success(`成功复制当前页 ${this.newsList.length} 条新闻内容`)
        } else {
          ElMessage.error('复制失败，请手动复制内容')
          console.log('复制的内容:', copyContent)
        }
      } catch (error) {
        console.error('复制失败:', error)
        ElMessage.error('复制失败')
      } finally {
        this.copyLoading = false
      }
    },

    // 复制单条新闻内容
    async copySingleContent() {
      if (!this.newsForm.content) {
        ElMessage.warning('当前内容为空，无法复制')
        return
      }

      try {
        const success = await this.copyToClipboard(this.newsForm.content)
        
        if (success) {
          ElMessage.success('新闻内容已复制到剪贴板')
        } else {
          ElMessage.error('复制失败，请手动复制内容')
          console.log('复制的内容:', this.newsForm.content)
        }
      } catch (error) {
        console.error('复制失败:', error)
        ElMessage.error('复制失败')
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
.filter-card,
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
  height: 100%;
  transition: all 0.3s ease;
}

.stat-card :deep(.el-card__body) {
  padding: 20px;
}

.stat-content {
  text-align: center;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
  line-height: 1.2;
}

.stat-value.success {
  color: var(--el-color-success);
}

.stat-label {
  font-size: 14px;
  color: var(--el-text-color-secondary);
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

.market-react-text {
  color: #606266;
  line-height: 1.6;
  font-size: 14px;
}

.text-gray {
  color: #909399;
  font-style: italic;
}

/* 分页器样式 */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: 30px;
  padding: 20px 0;
}

/* 对话框样式 */
.dialog-footer {
  text-align: right;
}

/* 新增/编辑对话框导航栏样式 */
.edit-navigation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 10px 20px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.nav-info {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #606266;
  font-size: 14px;
}

.nav-position {
  font-weight: bold;
  color: #303133;
}

.nav-tips {
  font-size: 12px;
  color: #909399;
}

.nav-controls {
  display: flex;
  gap: 10px;
}

/* 上传区域样式 */
.upload-area {
  display: flex;
  align-items: flex-start;
  gap: 20px;
}

.upload-tip {
  color: #909399;
  font-size: 12px;
  line-height: 1.5;
}

.upload-tip p {
  margin: 0;
}

/* 现有截图样式 */
.existing-screenshots {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #ebeef5;
}

.existing-screenshots h4 {
  margin: 0 0 15px 0;
  font-size: 14px;
  color: #606266;
}

.screenshot-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.screenshot-item {
  position: relative;
  width: 100px;
  height: 100px;
}

.screenshot-image {
  width: 100%;
  height: 100%;
  border-radius: 6px;
}

.screenshot-actions {
  position: absolute;
  top: 5px;
  right: 5px;
}

/* 筛选区域样式 */
.filter-row {
  margin-bottom: 15px;
}

.filter-row:last-child {
  margin-bottom: 0;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .stats-row .el-col {
    margin-bottom: 20px;
  }
  
  .filter-row .el-col {
    margin-bottom: 10px;
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
    font-size: 20px;
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

/* 内容复制区域样式 */
:deep(.content-with-copy) {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;
}

:deep(.content-with-copy .el-textarea) {
  width: 100%;
}

:deep(.content-with-copy .el-textarea__inner) {
  width: 100%;
}
</style>