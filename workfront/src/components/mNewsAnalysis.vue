<template>
  <div class="m-news-analysis">
    <!-- 移动端头部 -->
    <div class="m-header">
      <div class="m-title">
        <span>财联社新闻</span>
        <el-tag type="success" size="small">运行中</el-tag>
      </div>
      
      <!-- 移动端统计卡片 -->
      <div class="m-stats">
        <div class="m-stat-item">
          <div class="m-stat-value">{{ stats.total }}</div>
          <div class="m-stat-label">总数</div>
        </div>
        <div class="m-stat-item">
          <div class="m-stat-value success">{{ stats.today_count }}</div>
          <div class="m-stat-label">今日</div>
        </div>
        <div class="m-stat-item">
          <div class="m-stat-time">{{ formatTime(stats.latest_time) }}</div>
          <div class="m-stat-label">最新</div>
        </div>
      </div>
    </div>

    <!-- 移动端搜索区 -->
    <div class="m-search">
      <el-input
        v-model="searchForm.search"
        placeholder="搜索标题或内容..."
        clearable
        @keyup.enter="handleSearch"
        @clear="handleSearch"
        size="small"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      
      <div class="m-filters">
        <el-select
          v-model="searchForm.message_label"
          placeholder="消息类型"
          clearable
          @change="handleSearch"
          size="small"
          style="width: 120px"
        >
          <el-option label="硬消息" value="hard" />
          <el-option label="软消息" value="soft" />
          <el-option label="未知" value="unknown" />
        </el-select>
        
        <el-button type="primary" @click="handleSearch" :loading="newsLoading" size="small">
          搜索
        </el-button>
        <el-button @click="resetSearch" size="small">重置</el-button>
      </div>
    </div>

    <!-- 移动端操作栏 -->
    <div class="m-actions">
      <el-button type="success" @click="showCreateDialog" size="small" icon="Plus">
        新增
      </el-button>
      <el-button type="info" @click="loadStats" :loading="statsLoading" size="small" icon="Refresh">
        刷新
      </el-button>
    </div>

    <!-- 移动端新闻列表 -->
    <div class="m-news-list" v-loading="newsLoading">
      <el-empty
        v-if="!newsLoading && newsList.length === 0"
        description="暂无新闻数据"
        :image-size="80"
      />
      
      <div
        v-else
        v-for="(item, index) in newsList"
        :key="item.id"
        class="m-news-item"
        @click="showEditDialog(item)"
      >
        <!-- 新闻卡片头部 -->
        <div class="m-news-header">
          <span class="m-news-index">{{ (pagination.page - 1) * pagination.page_size + index + 1 }}</span>
          <span class="m-news-time">{{ item.time }}</span>
          <div class="m-news-actions" @click.stop>
            <el-button
              type="danger"
              size="small"
              @click="confirmDelete(item)"
              icon="Delete"
              circle
            />
          </div>
        </div>
        
        <!-- 新闻标题 -->
        <div class="m-news-title">{{ item.title }}</div>
        
        <!-- 新闻标签和评分 -->
        <div class="m-news-meta">
          <el-tag
            :type="getLabelType(item.message_label)"
            size="small"
            @click.stop="showLabelSelector(item)"
          >
            {{ getLabelText(item.message_label) }}
          </el-tag>
          
          <div class="m-score-container" @click.stop>
            <span class="m-score-label">分数:</span>
            <el-input-number
              v-model="item.message_score"
              :min="0"
              :max="100"
              size="small"
              @change="updateMessageScore(item)"
              style="width: 80px"
            />
          </div>
          
          <el-tag v-if="item.message_type" type="primary" size="small">
            {{ item.message_type }}
          </el-tag>
        </div>
        
        <!-- 市场反应 -->
        <div v-if="item.market_react" class="m-news-react">
          <span class="m-react-label">市场反应:</span>
          <span class="m-react-text">{{ item.market_react }}</span>
        </div>
        
        <!-- 截图数量 -->
        <div v-if="item.screenshots && item.screenshots.length > 0" class="m-screenshots">
          <el-icon><Picture /></el-icon>
          <span>{{ item.screenshots.length }}张截图</span>
        </div>
      </div>
    </div>

    <!-- 移动端分页 -->
    <div v-if="pagination.total > 0" class="m-pagination">
      <el-pagination
        :current-page="pagination.page"
        :page-size="pagination.page_size"
        :total="pagination.total"
        layout="prev, pager, next"
        @current-change="handleCurrentChange"
        background
        size="small"
      />
    </div>

    <!-- 标签选择器弹出层 -->
    <el-dialog
      v-model="labelDialogVisible"
      title="选择消息类型"
      width="300px"
      :show-close="false"
    >
      <div class="m-label-options">
        <el-radio-group v-model="tempLabel" @change="updateTempLabel">
          <el-radio-button value="hard">
            <el-tag type="success" size="small">硬消息</el-tag>
          </el-radio-button>
          <el-radio-button value="soft">
            <el-tag type="info" size="small">软消息</el-tag>
          </el-radio-button>
          <el-radio-button value="unknown">
            <el-tag type="warning" size="small">未知</el-tag>
          </el-radio-button>
        </el-radio-group>
      </div>
      <template #footer>
        <el-button @click="labelDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="confirmLabelUpdate">确定</el-button>
      </template>
    </el-dialog>

    <!-- 新增/编辑对话框 - 简化移动端版本 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogMode === 'create' ? '新增消息' : '编辑消息'"
      width="95%"
      :before-close="handleCloseDialog"
      :show-close="false"
    >
      <el-form
        ref="newsFormRef"
        :model="newsForm"
        :rules="newsFormRules"
        label-position="top"
      >
        <el-form-item label="标题" prop="title">
          <el-input
            v-model="newsForm.title"
            placeholder="请输入新闻标题"
            maxlength="500"
            show-word-limit
            type="textarea"
            :rows="2"
          />
        </el-form-item>

        <el-form-item label="内容" prop="content">
          <el-input
            v-model="newsForm.content"
            type="textarea"
            :rows="4"
            placeholder="请输入新闻内容"
            maxlength="10000"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="AI分析/备注">
          <el-input
            v-model="newsForm.ai_analysis"
            type="textarea"
            :rows="3"
            placeholder="请输入AI分析结果或备注信息..."
            maxlength="5000"
            show-word-limit
          />
        </el-form-item>

        <div class="m-form-row">
          <el-form-item label="消息分数" style="flex: 1;">
            <el-slider
              v-model="newsForm.message_score"
              :min="0"
              :max="100"
              show-input
              input-size="small"
            />
          </el-form-item>
        </div>

        <div class="m-form-row">
          <el-form-item label="消息标签" style="flex: 1;">
            <el-radio-group v-model="newsForm.message_label">
              <el-radio-button value="hard">硬消息</el-radio-button>
              <el-radio-button value="soft">软消息</el-radio-button>
              <el-radio-button value="unknown">未知</el-radio-button>
            </el-radio-group>
          </el-form-item>
        </div>

        <el-form-item label="消息类型">
          <el-select
            v-model="newsForm.message_type"
            placeholder="选择或输入类型"
            filterable
            allow-create
            clearable
            style="width: 100%"
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

        <el-form-item label="市场反应">
          <el-input
            v-model="newsForm.market_react"
            placeholder="请输入市场反应情况"
            maxlength="255"
            show-word-limit
          />
        </el-form-item>

        <!-- 简化的图片上传 -->
        <el-form-item label="截图上传">
          <el-upload
            ref="uploadRef"
            :auto-upload="false"
            :on-change="handleFileChange"
            :on-remove="handleFileRemove"
            list-type="picture-card"
            :limit="5"
            accept="image/*"
          >
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div class="m-upload-tip">
            最多上传5张图片
          </div>
          
          <!-- 现有截图预览 -->
          <div v-if="existingScreenshots.length > 0" class="m-existing-screenshots">
            <h4>现有截图:</h4>
            <div class="m-screenshot-grid">
              <div
                v-for="(screenshot, index) in existingScreenshots"
                :key="index"
                class="m-screenshot-item"
              >
                <el-image
                  :src="screenshot.url"
                  :preview-src-list="existingScreenshots.map(s => s.url)"
                  :initial-index="index"
                  fit="cover"
                  class="m-screenshot-image"
                  lazy
                />
                <div class="m-screenshot-actions">
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
      </el-form>

      <template #footer>
        <div class="m-dialog-footer">
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
  name: 'mNewsAnalysis',
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
        message_label: ''
      },

      // 对话框相关
      dialogVisible: false,
      dialogMode: 'create',
      submitLoading: false,
      currentEditId: null,

      // 标签选择器
      labelDialogVisible: false,
      tempLabel: '',
      currentLabelItem: null,

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
      existingScreenshots: []
    }
  },
  
  async mounted() {
    await this.loadStats()
    await this.loadNewsList()
  },
  
  methods: {
    // 格式化时间显示
    formatTime(timeStr) {
      if (!timeStr) return '暂无'
      // 只显示时分
      return timeStr.split(' ')[1]?.substring(0, 5) || timeStr
    },

    // 获取标签类型
    getLabelType(label) {
      const typeMap = {
        'hard': 'success',
        'soft': 'info', 
        'unknown': 'warning'
      }
      return typeMap[label] || 'warning'
    },

    // 获取标签文本
    getLabelText(label) {
      const textMap = {
        'hard': '硬消息',
        'soft': '软消息',
        'unknown': '未知'
      }
      return textMap[label] || '未知'
    },

    // 显示标签选择器
    showLabelSelector(item) {
      this.currentLabelItem = item
      this.tempLabel = item.message_label
      this.labelDialogVisible = true
    },

    // 更新临时标签
    updateTempLabel(value) {
      this.tempLabel = value
    },

    // 确认标签更新
    async confirmLabelUpdate() {
      if (this.currentLabelItem) {
        this.currentLabelItem.message_label = this.tempLabel
        await this.updateMessageLabel(this.currentLabelItem)
      }
      this.labelDialogVisible = false
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
    
    // 当前页变化
    handleCurrentChange(newPage) {
      this.pagination.page = newPage
      this.loadNewsList()
    },

    // 搜索处理
    handleSearch() {
      this.pagination.page = 1
      this.loadNewsList()
    },

    // 重置搜索
    resetSearch() {
      this.searchForm = {
        search: '',
        message_label: ''
      }
      this.handleSearch()
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
      this.resetForm()
      this.dialogVisible = true
    },

    // 显示编辑对话框
    async showEditDialog(row) {
      this.dialogMode = 'edit'
      this.currentEditId = row.id
      
      try {
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
      
      this.$nextTick(() => {
        if (this.$refs.newsFormRef) {
          this.$refs.newsFormRef.clearValidate()
        }
      })
    },

    // 关闭对话框
    handleCloseDialog() {
      this.dialogVisible = false
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
        const uploadResponse = await request.post(getOssUploadUrlApi, {
          news_id: newsId,
          filename: file.name,
          content_type: file.raw.type
        })

        if (uploadResponse.code !== 0) {
          throw new Error(uploadResponse.message)
        }

        const { upload_url, object_key } = uploadResponse.data

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
        await this.$refs.newsFormRef.validate()
        
        this.submitLoading = true
        
        let newsId = this.currentEditId
        let screenshotKeys = []

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

        const allScreenshots = [
          ...this.existingScreenshots.map(s => s.key),
          ...screenshotKeys
        ]

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
    }
  }
}
</script>

<style scoped>
.m-news-analysis {
  padding: 10px;
  background-color: #f5f5f5;
  min-height: 100vh;
}

/* 移动端头部 */
.m-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  padding: 20px 15px;
  margin-bottom: 12px;
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.15);
  position: relative;
  overflow: hidden;
}

.m-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(45deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.05) 100%);
  pointer-events: none;
}

.m-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 600;
  font-size: 18px;
  margin-bottom: 20px;
  color: white;
  position: relative;
  z-index: 1;
}

.m-title span {
  text-shadow: 0 2px 4px rgba(0,0,0,0.1);
  letter-spacing: 0.5px;
}

.m-stats {
  display: flex;
  justify-content: space-around;
  position: relative;
  z-index: 1;
}

.m-stat-item {
  text-align: center;
  padding: 8px 12px;
  background: rgba(255,255,255,0.15);
  border-radius: 8px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255,255,255,0.2);
  min-width: 70px;
}

.m-stat-value {
  font-size: 24px;
  font-weight: 700;
  color: white;
  margin-bottom: 4px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.2);
}

.m-stat-value.success {
  color: #a8f5a8;
}

.m-stat-time {
  font-size: 14px;
  font-weight: 600;
  color: white;
  margin-bottom: 4px;
  text-shadow: 0 1px 2px rgba(0,0,0,0.2);
}

.m-stat-label {
  font-size: 12px;
  color: rgba(255,255,255,0.9);
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

/* 移动端搜索区 */
.m-search {
  background: white;
  border-radius: 12px;
  padding: 18px 16px;
  margin-bottom: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  border: 1px solid rgba(102, 126, 234, 0.1);
  transition: all 0.3s ease;
}

.m-search:hover {
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.12);
  transform: translateY(-1px);
}

.m-search .el-input {
  border-radius: 8px;
}

.m-search .el-input__wrapper {
  border-radius: 8px;
  border: 1px solid #e1e7f5;
  transition: all 0.3s ease;
}

.m-search .el-input__wrapper:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

.m-search .el-input__wrapper.is-focus {
  border-color: #667eea;
  box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
}

.m-filters {
  display: flex;
  gap: 12px;
  margin-top: 15px;
  align-items: center;
  flex-wrap: wrap;
}

.m-filters .el-select {
  border-radius: 8px;
}

.m-filters .el-select .el-input__wrapper {
  border-radius: 8px;
  border: 1px solid #e1e7f5;
  transition: all 0.3s ease;
}

.m-filters .el-select .el-input__wrapper:hover {
  border-color: #667eea;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.1);
}

.m-filters .el-button {
  border-radius: 8px;
  font-weight: 500;
  padding: 8px 16px;
  transition: all 0.3s ease;
  border: none;
}

.m-filters .el-button--primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
}

.m-filters .el-button--primary:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
}

.m-filters .el-button--primary:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.m-filters .el-button:not(.el-button--primary) {
  background: #f8f9ff;
  color: #667eea;
  border: 1px solid #e1e7f5;
}

.m-filters .el-button:not(.el-button--primary):hover {
  background: #667eea;
  color: white;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

/* 移动端操作栏 */
.m-actions {
  background: white;
  border-radius: 12px;
  padding: 15px;
  margin-bottom: 12px;
  display: flex;
  gap: 12px;
  box-shadow: 0 4px 12px rgba(0,0,0,0.08);
  border: 1px solid rgba(102, 126, 234, 0.1);
  transition: all 0.3s ease;
}

.m-actions:hover {
  box-shadow: 0 6px 16px rgba(102, 126, 234, 0.12);
  transform: translateY(-1px);
}

.m-actions .el-button {
  border-radius: 8px;
  font-weight: 500;
  padding: 10px 16px;
  transition: all 0.3s ease;
  border: none;
}

.m-actions .el-button--success {
  background: linear-gradient(135deg, #67c23a 0%, #85ce61 100%);
  box-shadow: 0 4px 12px rgba(103, 194, 58, 0.3);
}

.m-actions .el-button--success:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(103, 194, 58, 0.4);
}

.m-actions .el-button--info {
  background: linear-gradient(135deg, #909399 0%, #b1b3b8 100%);
  box-shadow: 0 4px 12px rgba(144, 147, 153, 0.3);
}

.m-actions .el-button--info:hover {
  transform: translateY(-1px);
  box-shadow: 0 6px 16px rgba(144, 147, 153, 0.4);
}

/* 移动端新闻列表 */
.m-news-list {
  min-height: 400px;
}

.m-news-item {
  background: white;
  border-radius: 8px;
  padding: 15px;
  margin-bottom: 10px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  cursor: pointer;
  transition: transform 0.2s ease;
}

.m-news-item:active {
  transform: scale(0.98);
}

.m-news-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 12px;
  color: #999;
}

.m-news-index {
  background: #409eff;
  color: white;
  border-radius: 50%;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 10px;
}

.m-news-time {
  flex: 1;
  text-align: center;
}

.m-news-actions {
  display: flex;
  gap: 5px;
}

.m-news-actions .el-button.is-circle {
  width: 28px !important;
  height: 28px !important;
  min-height: 28px !important;
  padding: 0 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  border-radius: 50% !important;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: all 0.3s ease;
}

.m-news-actions .el-button.is-circle:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.m-news-actions .el-button.is-circle:active {
  transform: scale(0.95);
  box-shadow: 0 1px 2px rgba(0,0,0,0.1);
}

.m-news-actions .el-button.is-circle .el-icon {
  font-size: 12px !important;
  width: 12px !important;
  height: 12px !important;
}

.m-news-title {
  font-size: 14px;
  font-weight: bold;
  line-height: 1.4;
  margin-bottom: 10px;
  color: #333;
}

.m-news-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 8px;
}

.m-score-container {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
}

.m-score-label {
  color: #666;
}

.m-news-react {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  margin-bottom: 5px;
}

.m-react-label {
  color: #666;
}

.m-react-text {
  color: #333;
}

.m-screenshots {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #409eff;
}

/* 移动端分页 */
.m-pagination {
  display: flex;
  justify-content: center;
  margin-top: 20px;
  padding: 20px 0;
}

/* 标签选择器 */
.m-label-options {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* 移动端表单 */
.m-form-row {
  display: flex;
  gap: 15px;
}

.m-upload-tip {
  font-size: 12px;
  color: #999;
  margin-top: 5px;
}

.m-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* 移动端现有截图样式 */
.m-existing-screenshots {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
}

.m-existing-screenshots h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
  font-weight: 500;
}

.m-screenshot-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.m-screenshot-item {
  position: relative;
  width: 80px;
  height: 80px;
  border-radius: 6px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.m-screenshot-image {
  width: 100%;
  height: 100%;
  border-radius: 6px;
}

.m-screenshot-actions {
  position: absolute;
  top: 4px;
  right: 4px;
}

.m-screenshot-actions .el-button.is-circle {
  width: 20px !important;
  height: 20px !important;
  min-height: 20px !important;
  padding: 0 !important;
  background: rgba(245, 108, 108, 0.9) !important;
  border: none !important;
}

.m-screenshot-actions .el-button.is-circle .el-icon {
  font-size: 10px !important;
  width: 10px !important;
  height: 10px !important;
}

/* 响应式调整 */
@media (max-width: 320px) {
  .m-news-analysis {
    padding: 5px;
  }
  
  .m-header,
  .m-search,
  .m-actions,
  .m-news-item {
    padding: 10px;
  }
  
  .m-stat-value {
    font-size: 20px;
  }
  
  .m-filters {
    flex-direction: column;
    gap: 8px;
  }
}

/* 空状态优化 */
.el-empty {
  padding: 40px 20px;
}

/* 加载状态 */
.el-loading-mask {
  border-radius: 8px;
}
</style>
