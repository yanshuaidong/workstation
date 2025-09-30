<template>
  <div class="news-tracking">
    <el-container>
      <!-- 标题栏 -->
      <el-header height="60px" class="header">
        <h1>新闻消息处理系统</h1>
      </el-header>
      
      <!-- 主内容区 -->
      <el-main>
        <!-- 步骤导航 -->
        <el-steps :active="currentStep" finish-status="success" align-center style="margin-bottom: 30px;">
          <el-step title="标签校验" description="对新闻消息进行标签审核"></el-step>
          <el-step title="后续跟踪" description="定期跟踪新闻市场反应"></el-step>
        </el-steps>
        
        <!-- 第一步：标签校验 -->
        <div v-show="currentStep === 0" class="step-content">
          <el-card class="review-card">
            <template #header>
              <div class="card-header">
                <span>标签校验流程</span>
                <el-tag v-if="unreviewedData.total_unreviewed > 0" type="warning" size="large">
                  剩余校验 {{ unreviewedData.total_unreviewed }} 条
                </el-tag>
                <el-tag v-else type="success" size="large">
                  校验完成
                </el-tag>
              </div>
            </template>
            
            <!-- 当前新闻卡片 -->
            <div v-if="unreviewedData.current_news" class="news-item">
              <div class="news-header">
                <h3>{{ unreviewedData.current_news.title }}</h3>
                <span class="news-time">{{ unreviewedData.current_news.time }}</span>
              </div>
              
              <div class="news-content">
                <p><strong>内容：</strong>{{ unreviewedData.current_news.content }}</p>
                <p v-if="unreviewedData.current_news.ai_analysis">
                  <strong>AI分析：</strong>{{ unreviewedData.current_news.ai_analysis }}
                </p>
                <div class="news-tags">
                  <span v-if="unreviewedData.current_news.message_score">
                    <strong>评分：</strong>{{ unreviewedData.current_news.message_score }}
                  </span>
                  <el-tag v-if="unreviewedData.current_news.message_label" 
                          :type="getLabelType(unreviewedData.current_news.message_label)"
                          style="margin-left: 10px;">
                    {{ getLabelText(unreviewedData.current_news.message_label) }}
                  </el-tag>
                  <span v-if="unreviewedData.current_news.message_type" style="margin-left: 10px;">
                    <strong>类型：</strong>{{ unreviewedData.current_news.message_type }}
                  </span>
                </div>
              </div>
              
              <div class="news-actions">
                <el-button type="primary" @click="openEditDialog(unreviewedData.current_news)">
                  编辑
                </el-button>
                <el-button type="success" @click="markAsReviewed">
                  校验完成
                </el-button>
                <el-button @click="loadUnreviewedNews">
                  刷新
                </el-button>
                <el-button type="info" @click="goToTracking" v-if="unreviewedData.total_unreviewed === 0">
                  进入跟踪流程
                </el-button>
              </div>
            </div>
            
            <!-- 无待校验新闻 -->
            <div v-else class="no-news">
              <el-empty description="没有待校验的新闻">
                <el-button type="primary" @click="goToTracking">进入跟踪流程</el-button>
              </el-empty>
            </div>
          </el-card>
        </div>
        
        <!-- 第二步：后续跟踪 -->
        <div v-show="currentStep === 1" class="step-content">
          <div class="tracking-section">
            <div class="section-header">
              <h2>后续跟踪管理</h2>
              <div>
                <el-button type="warning" @click="initTracking">初始化跟踪</el-button>
                <el-button type="primary" @click="loadTrackingList">刷新列表</el-button>
                <el-button type="info" @click="showDebugInfo" v-if="isDevelopment">调试信息</el-button>
              </div>
            </div>
            
            <!-- 统计信息 -->
            <div class="tracking-summary">
              <el-row :gutter="20">
                <el-col :span="6">
                  <el-statistic title="总待跟踪" :value="trackingSummary.total_pending" />
                </el-col>
                <el-col :span="6">
                  <el-statistic title="3天跟踪" :value="trackingSummary.day3_count" />
                </el-col>
                <el-col :span="6">
                  <el-statistic title="7天跟踪" :value="trackingSummary.day7_count" />
                </el-col>
                <el-col :span="6">
                  <el-statistic title="14天跟踪" :value="trackingSummary.day14_count" />
                </el-col>
              </el-row>
            </div>
            
            <!-- 跟踪列表标签页 -->
            <el-tabs v-model="activeTrackingTab" type="card">
              <el-tab-pane name="day3">
                <template #label>
                  3天跟踪 <el-badge :value="trackingSummary.day3_count" :hidden="trackingSummary.day3_count === 0" type="warning" />
                </template>
                <div v-if="trackingData.day3_list && trackingData.day3_list.length > 0">
                  <el-table :data="trackingData.day3_list" stripe style="width: 100%">
                    <el-table-column prop="time" label="时间" width="180"></el-table-column>
                    <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip></el-table-column>
                    <el-table-column prop="message_label" label="标签" width="80">
                      <template #default="scope">
                        <el-tag :type="getLabelType(scope.row.message_label)" size="small">
                          {{ getLabelText(scope.row.message_label) }}
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="message_score" label="评分" width="80"></el-table-column>
                    <el-table-column prop="market_react" label="市场反应" min-width="150" show-overflow-tooltip>
                      <template #default="scope">
                        <span v-if="scope.row.market_react">{{ scope.row.market_react }}</span>
                        <el-text type="info" v-else>未填写</el-text>
                      </template>
                    </el-table-column>
                    <el-table-column label="操作" width="200">
                      <template #default="scope">
                        <el-button type="primary" size="small" @click="openTrackingEditDialog(scope.row, 'day3')">
                          编辑
                        </el-button>
                        <el-button type="success" size="small" @click="markTrackingDone(scope.row, 'day3')">
                          完成跟踪
                        </el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
                <el-empty v-else description="暂无需要跟踪的消息" :image-size="100" />
              </el-tab-pane>
              
              <el-tab-pane name="day7">
                <template #label>
                  7天跟踪 <el-badge :value="trackingSummary.day7_count" :hidden="trackingSummary.day7_count === 0" type="warning" />
                </template>
                <div v-if="trackingData.day7_list && trackingData.day7_list.length > 0">
                  <el-table :data="trackingData.day7_list" stripe style="width: 100%">
                    <el-table-column prop="time" label="时间" width="180"></el-table-column>
                    <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip></el-table-column>
                    <el-table-column prop="message_label" label="标签" width="80">
                      <template #default="scope">
                        <el-tag :type="getLabelType(scope.row.message_label)" size="small">
                          {{ getLabelText(scope.row.message_label) }}
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="message_score" label="评分" width="80"></el-table-column>
                    <el-table-column prop="market_react" label="市场反应" min-width="150" show-overflow-tooltip>
                      <template #default="scope">
                        <span v-if="scope.row.market_react">{{ scope.row.market_react }}</span>
                        <el-text type="info" v-else>未填写</el-text>
                      </template>
                    </el-table-column>
                    <el-table-column label="操作" width="200">
                      <template #default="scope">
                        <el-button type="primary" size="small" @click="openTrackingEditDialog(scope.row, 'day7')">
                          编辑
                        </el-button>
                        <el-button type="success" size="small" @click="markTrackingDone(scope.row, 'day7')">
                          完成跟踪
                        </el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
                <el-empty v-else description="暂无需要跟踪的消息" :image-size="100" />
              </el-tab-pane>
              
              <el-tab-pane name="day14">
                <template #label>
                  14天跟踪 <el-badge :value="trackingSummary.day14_count" :hidden="trackingSummary.day14_count === 0" type="warning" />
                </template>
                <div v-if="trackingData.day14_list && trackingData.day14_list.length > 0">
                  <el-table :data="trackingData.day14_list" stripe style="width: 100%">
                    <el-table-column prop="time" label="时间" width="180"></el-table-column>
                    <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip></el-table-column>
                    <el-table-column prop="message_label" label="标签" width="80">
                      <template #default="scope">
                        <el-tag :type="getLabelType(scope.row.message_label)" size="small">
                          {{ getLabelText(scope.row.message_label) }}
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="message_score" label="评分" width="80"></el-table-column>
                    <el-table-column prop="market_react" label="市场反应" min-width="150" show-overflow-tooltip>
                      <template #default="scope">
                        <span v-if="scope.row.market_react">{{ scope.row.market_react }}</span>
                        <el-text type="info" v-else>未填写</el-text>
                      </template>
                    </el-table-column>
                    <el-table-column label="操作" width="200">
                      <template #default="scope">
                        <el-button type="primary" size="small" @click="openTrackingEditDialog(scope.row, 'day14')">
                          编辑
                        </el-button>
                        <el-button type="success" size="small" @click="markTrackingDone(scope.row, 'day14')">
                          完成跟踪
                        </el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
                <el-empty v-else description="暂无需要跟踪的消息" :image-size="100" />
              </el-tab-pane>
              
              <el-tab-pane name="day28">
                <template #label>
                  28天跟踪 <el-badge :value="trackingSummary.day28_count" :hidden="trackingSummary.day28_count === 0" type="warning" />
                </template>
                <div v-if="trackingData.day28_list && trackingData.day28_list.length > 0">
                  <el-table :data="trackingData.day28_list" stripe style="width: 100%">
                    <el-table-column prop="time" label="时间" width="180"></el-table-column>
                    <el-table-column prop="title" label="标题" min-width="200" show-overflow-tooltip></el-table-column>
                    <el-table-column prop="message_label" label="标签" width="80">
                      <template #default="scope">
                        <el-tag :type="getLabelType(scope.row.message_label)" size="small">
                          {{ getLabelText(scope.row.message_label) }}
                        </el-tag>
                      </template>
                    </el-table-column>
                    <el-table-column prop="message_score" label="评分" width="80"></el-table-column>
                    <el-table-column prop="market_react" label="市场反应" min-width="150" show-overflow-tooltip>
                      <template #default="scope">
                        <span v-if="scope.row.market_react">{{ scope.row.market_react }}</span>
                        <el-text type="info" v-else>未填写</el-text>
                      </template>
                    </el-table-column>
                    <el-table-column label="操作" width="200">
                      <template #default="scope">
                        <el-button type="primary" size="small" @click="openTrackingEditDialog(scope.row, 'day28')">
                          编辑
                        </el-button>
                        <el-button type="success" size="small" @click="markTrackingDone(scope.row, 'day28')">
                          完成跟踪
                        </el-button>
                      </template>
                    </el-table-column>
                  </el-table>
                </div>
                <el-empty v-else description="暂无需要跟踪的消息" :image-size="100" />
              </el-tab-pane>
            </el-tabs>
          </div>
        </div>
      </el-main>
    </el-container>
    
    <!-- 编辑新闻对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑新闻" width="60%" :before-close="handleEditClose">
      <el-form :model="editForm" label-width="100px" v-loading="editLoading">
        <el-form-item label="标题">
          <el-input v-model="editForm.title" type="textarea" :rows="2"></el-input>
        </el-form-item>
        
        <el-form-item label="内容">
          <el-input v-model="editForm.content" type="textarea" :rows="4"></el-input>
        </el-form-item>
        
        <el-form-item label="AI分析">
          <el-input v-model="editForm.ai_analysis" type="textarea" :rows="3"></el-input>
        </el-form-item>
        
        <el-form-item label="消息评分">
          <el-input-number v-model="editForm.message_score" :min="0" :max="100"></el-input-number>
        </el-form-item>
        
        <el-form-item label="消息标签">
          <el-select v-model="editForm.message_label" placeholder="请选择">
            <el-option label="硬消息" value="hard"></el-option>
            <el-option label="软消息" value="soft"></el-option>
            <el-option label="未知" value="unknown"></el-option>
          </el-select>
        </el-form-item>
        
        <el-form-item label="消息类型">
          <el-input v-model="editForm.message_type" placeholder="如：利好政策、并购落地、减持公告"></el-input>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="editDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveNewsEdit" :loading="editLoading">保存</el-button>
        </span>
      </template>
    </el-dialog>
    
    <!-- 跟踪编辑对话框 -->
    <el-dialog v-model="trackingEditDialogVisible" title="跟踪编辑" width="60%" :before-close="handleTrackingEditClose">
      <el-form :model="trackingEditForm" label-width="100px" v-loading="trackingEditLoading">
        <!-- 只读字段 -->
        <el-form-item label="标题">
          <el-input v-model="trackingEditForm.title" readonly></el-input>
        </el-form-item>
        
        <el-form-item label="内容">
          <el-input v-model="trackingEditForm.content" type="textarea" :rows="3" readonly></el-input>
        </el-form-item>
        
        <el-form-item label="AI分析">
          <el-input v-model="trackingEditForm.ai_analysis" type="textarea" :rows="2" readonly></el-input>
        </el-form-item>
        
        <!-- 可编辑字段 -->
        <el-form-item label="市场反应">
          <el-input v-model="trackingEditForm.market_react" type="textarea" :rows="3" 
                    placeholder="请描述市场反应：大涨/大跌/没反应等"></el-input>
        </el-form-item>
        
        <el-form-item label="截图">
          <div class="screenshot-section">
            <!-- 现有截图展示 -->
            <div v-if="trackingEditForm.screenshots && trackingEditForm.screenshots.length > 0" class="existing-screenshots">
              <h4>现有截图:</h4>
              <div class="screenshot-grid">
                <div v-for="(screenshot, index) in trackingEditForm.screenshots" :key="index" class="screenshot-item">
                  <el-image
                    :src="screenshot.url"
                    :preview-src-list="trackingEditForm.screenshots.map(s => s.url)"
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
            
            <!-- 文件上传区域 -->
            <div class="upload-section">
              <div class="upload-area">
                <el-upload
                  ref="trackingUploadRef"
                  :auto-upload="false"
                  :on-change="handleTrackingFileChange"
                  :on-remove="handleTrackingFileRemove"
                  :before-upload="beforeUpload"
                  list-type="picture-card"
                  :limit="10"
                  accept="image/*"
                  :disabled="uploadLoading"
                >
                  <el-icon><Plus /></el-icon>
                </el-upload>
                <div class="upload-tip">
                  <p>支持jpg、png等格式，最多上传10张图片</p>
                  <p>图片将自动上传到阿里云OSS</p>
                </div>
              </div>
            </div>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="trackingEditDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveTrackingEdit" :loading="trackingEditLoading">保存并完成跟踪</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import request from '@/utils/request'
import { 
  getUnreviewedNewsApi, 
  markNewsReviewedApi, 
  getTrackingListApi, 
  updateTrackingStatusApi,
  updateNewsApi,
  initTrackingApi,
  getOssUploadUrlApi
} from '@/api'
import { Plus } from '@element-plus/icons-vue'


export default {
  name: 'NewsTracking',
  components: {
    Plus
  },
  data() {
    return {
      currentStep: 0,
      activeTrackingTab: 'day3',
      isDevelopment: process.env.NODE_ENV === 'development',
      
      // 待校验数据
      unreviewedData: {
        total_unreviewed: 0,
        current_news: null
      },
      
      // 跟踪数据
      trackingData: {
        day3_list: [],
        day7_list: [],
        day14_list: [],
        day28_list: []
      },
      
      // 跟踪统计信息
      trackingSummary: {
        total_pending: 0,
        day3_count: 0,
        day7_count: 0,
        day14_count: 0,
        day28_count: 0
      },
      
      // 编辑对话框
      editDialogVisible: false,
      editLoading: false,
      editForm: {
        id: null,
        title: '',
        content: '',
        ai_analysis: '',
        message_score: null,
        message_label: 'unknown',
        message_type: ''
      },
      
      // 跟踪编辑对话框
      trackingEditDialogVisible: false,
      trackingEditLoading: false,
      trackingEditForm: {
        id: null, // 新闻ID
        tracking_id: null,
        track_type: '',
        title: '',
        content: '',
        ai_analysis: '',
        market_react: '',
        screenshots: []
      },
      
      // 截图上传相关
      uploadFiles: [],
      uploadLoading: false
    }
  },
  
  mounted() {
    this.loadUnreviewedNews()
    // 如果直接进入跟踪步骤，也加载跟踪数据
    if (this.currentStep === 1) {
      this.loadTrackingList()
    }
  },
  
  watch: {
    // 监听步骤变化，自动加载对应数据
    currentStep: {
      handler(newStep) {
        if (newStep === 1) {
          this.loadTrackingList()
        }
      }
    }
  },
  
  methods: {
    // 加载待校验新闻
    async loadUnreviewedNews() {
      try {
        const response = await request.get(getUnreviewedNewsApi)
        if (response.code === 0) {
          this.unreviewedData = response.data
        } else {
          this.$message.error(response.message)
        }
      } catch (error) {
        this.$message.error('获取待校验新闻失败：' + error.message)
      }
    },
    
    // 标记为已校验
    async markAsReviewed() {
      if (!this.unreviewedData.current_news) {
        this.$message.warning('没有待校验的新闻')
        return
      }
      
      try {
        const response = await request.post(markNewsReviewedApi, {
          tracking_id: this.unreviewedData.current_news.tracking_id
        })
        
        if (response.code === 0) {
          this.$message.success('校验完成')
          await this.loadUnreviewedNews()
        } else {
          this.$message.error(response.message)
        }
      } catch (error) {
        this.$message.error('标记校验失败：' + error.message)
      }
    },
    
    // 打开编辑对话框
    openEditDialog(news) {
      this.editForm = {
        id: news.id,
        title: news.title || '',
        content: news.content || '',
        ai_analysis: news.ai_analysis || '',
        message_score: news.message_score,
        message_label: news.message_label || 'unknown',
        message_type: news.message_type || ''
      }
      this.editDialogVisible = true
    },
    
    // 保存新闻编辑
    async saveNewsEdit() {
      this.editLoading = true
      try {
        const response = await request.put(updateNewsApi + '/' + this.editForm.id, {
          title: this.editForm.title,
          content: this.editForm.content,
          ai_analysis: this.editForm.ai_analysis,
          message_score: this.editForm.message_score,
          message_label: this.editForm.message_label,
          message_type: this.editForm.message_type
        })
        
        if (response.code === 0) {
          this.$message.success('保存成功')
          this.editDialogVisible = false
          await this.loadUnreviewedNews()
        } else {
          this.$message.error(response.message)
        }
      } catch (error) {
        this.$message.error('保存失败：' + error.message)
      } finally {
        this.editLoading = false
      }
    },
    
    // 处理编辑对话框关闭
    handleEditClose(done) {
      this.$confirm('确认取消编辑？')
        .then(() => {
          done()
        })
        .catch(() => {})
    },
    
    // 进入跟踪流程
    async goToTracking() {
      this.currentStep = 1
      await this.loadTrackingList()
    },
    
    // 加载跟踪列表
    async loadTrackingList() {
      try {
        const response = await request.get(getTrackingListApi)
        console.log('跟踪列表接口响应:', response) // 调试信息
        
        if (response.code === 0) {
          this.trackingData = {
            day3_list: response.data.day3_list || [],
            day7_list: response.data.day7_list || [],
            day14_list: response.data.day14_list || [],
            day28_list: response.data.day28_list || []
          }
          
          // 添加统计信息
          if (response.data.summary) {
            this.trackingSummary = response.data.summary
          }
          
          console.log('处理后的跟踪数据:', this.trackingData) // 调试信息
          this.$message.success(`获取跟踪列表成功 - 总计${response.data.summary?.total_pending || 0}条待跟踪`)
        } else {
          this.$message.error(response.message)
        }
      } catch (error) {
        console.error('获取跟踪列表失败:', error) // 调试信息
        this.$message.error('获取跟踪列表失败：' + error.message)
      }
    },
    
    // 打开跟踪编辑对话框
    openTrackingEditDialog(news, trackType) {
      this.trackingEditForm = {
        id: news.id, // 新闻ID
        tracking_id: news.tracking_id,
        track_type: trackType,
        title: news.title || '',
        content: news.content || '',
        ai_analysis: news.ai_analysis || '',
        market_react: news.market_react || '',
        screenshots: news.screenshots || []
      }
      this.trackingEditDialogVisible = true
    },
    
    // 保存跟踪编辑
    async saveTrackingEdit() {
      this.trackingEditLoading = true
      try {
        let screenshotKeys = []
        
        // 上传新文件
        if (this.uploadFiles.length > 0) {
          this.uploadLoading = true
          for (const file of this.uploadFiles) {
            try {
              const objectKey = await this.uploadFileToOss(file, this.trackingEditForm.id)
              screenshotKeys.push(objectKey)
              this.$message.success(`${file.name} 上传成功`)
            } catch (error) {
              this.$message.error(`文件 ${file.name} 上传失败: ${error.message}`)
            }
          }
          this.uploadLoading = false
        }
        
        // 合并现有截图和新上传的截图
        const allScreenshots = [
          ...this.trackingEditForm.screenshots.map(s => s.key),
          ...screenshotKeys
        ]
        
        // 先更新新闻的market_react和screenshots字段
        if (this.trackingEditForm.id) {
          const newsUpdateResponse = await request.put(
            updateNewsApi + '/' + this.trackingEditForm.id, 
            {
              market_react: this.trackingEditForm.market_react,
              screenshots: allScreenshots
            }
          )
          
          if (newsUpdateResponse.code !== 0) {
            this.$message.error('更新新闻失败：' + newsUpdateResponse.message)
            return
          }
        }
        
        // 再更新跟踪状态
        const trackingResponse = await request.post(updateTrackingStatusApi, {
          tracking_id: this.trackingEditForm.tracking_id,
          track_type: this.trackingEditForm.track_type
        })
        
        if (trackingResponse.code === 0) {
          this.$message.success('跟踪完成')
          this.trackingEditDialogVisible = false
          // 清空上传文件列表
          this.uploadFiles = []
          if (this.$refs.trackingUploadRef) {
            this.$refs.trackingUploadRef.clearFiles()
          }
          await this.loadTrackingList()
        } else {
          this.$message.error(trackingResponse.message)
        }
      } catch (error) {
        this.$message.error('保存失败：' + error.message)
      } finally {
        this.trackingEditLoading = false
        this.uploadLoading = false
      }
    },
    
    // 直接完成跟踪（不编辑）
    async markTrackingDone(news, trackType) {
      try {
        this.$confirm(`确认完成${trackType.replace('day', '')}天跟踪吗？`, '提示', {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(async () => {
          const response = await request.post(updateTrackingStatusApi, {
            tracking_id: news.tracking_id,
            track_type: trackType
          })
          
          if (response.code === 0) {
            this.$message.success('跟踪完成')
            await this.loadTrackingList()
          } else {
            this.$message.error(response.message)
          }
        }).catch(() => {
          // 用户取消操作
        })
      } catch (error) {
        this.$message.error('操作失败：' + error.message)
      }
    },
    
    // 处理跟踪编辑对话框关闭
    handleTrackingEditClose(done) {
      this.$confirm('确认取消编辑？')
        .then(() => {
          // 清空上传文件列表
          this.uploadFiles = []
          if (this.$refs.trackingUploadRef) {
            this.$refs.trackingUploadRef.clearFiles()
          }
          done()
        })
        .catch(() => {})
    },
    
    // 获取标签类型
    getLabelType(label) {
      const types = {
        'hard': 'danger',
        'soft': 'warning', 
        'unknown': 'info'
      }
      return types[label] || 'info'
    },
    
    // 获取标签文本
    getLabelText(label) {
      const texts = {
        'hard': '硬消息',
        'soft': '软消息',
        'unknown': '未知'
      }
      return texts[label] || '未知'
    },
    
    // 初始化跟踪记录
    async initTracking() {
      try {
        this.$message.info('正在初始化跟踪记录...')
        const response = await request.post(initTrackingApi)
        
        if (response.code === 0) {
          this.$message.success(response.message)
          await this.loadTrackingList()
        } else {
          this.$message.error(response.message)
        }
      } catch (error) {
        this.$message.error('初始化失败：' + error.message)
      }
    },
    
    // 显示调试信息
    showDebugInfo() {
      console.log('=== 调试信息 ===')
      console.log('当前步骤:', this.currentStep)
      console.log('跟踪数据:', this.trackingData)
      console.log('统计信息:', this.trackingSummary)
      console.log('活跃标签页:', this.activeTrackingTab)
      console.log('=== 调试信息结束 ===')
      
      this.$alert(`
        当前步骤: ${this.currentStep}
        活跃标签页: ${this.activeTrackingTab}
        总待跟踪: ${this.trackingSummary.total_pending}
        3天跟踪: ${this.trackingSummary.day3_count}
        7天跟踪: ${this.trackingSummary.day7_count}
        14天跟踪: ${this.trackingSummary.day14_count}
        28天跟踪: ${this.trackingSummary.day28_count}
      `, '调试信息', {
        confirmButtonText: '确定'
      })
    },
    
    // 截图相关方法
    previewImage(url) {
      // 使用Element Plus的图片预览功能
      this.$alert(`<img src="${url}" style="width: 100%; max-width: 500px;" />`, '截图预览', {
        dangerouslyUseHTMLString: true,
        confirmButtonText: '关闭'
      })
    },
    
    // 移除现有截图
    removeExistingScreenshot(index) {
      this.$confirm('确认删除这张截图吗？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }).then(() => {
        this.trackingEditForm.screenshots.splice(index, 1)
        this.$message.success('截图已删除')
      }).catch(() => {})
    },
    
    // 处理跟踪编辑对话框的文件变化
    handleTrackingFileChange(file, fileList) {
      this.uploadFiles = fileList
    },
    
    // 处理跟踪编辑对话框的文件移除
    handleTrackingFileRemove(file, fileList) {
      this.uploadFiles = fileList
    },
    
    // 上传前检查
    beforeUpload(file) {
      // 检查文件类型
      const isImage = file.type.startsWith('image/')
      if (!isImage) {
        this.$message.error('只能上传图片文件!')
        return false
      }
      
      // 检查文件大小
      const isLt5M = file.size / 1024 / 1024 < 5
      if (!isLt5M) {
        this.$message.error('图片大小不能超过 5MB!')
        return false
      }
      
      return true
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
    }
  }
}
</script>

<style scoped>
.news-tracking {
  min-height: 100vh;
  background-color: #f5f7fa;
}

.header {
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  padding: 0 20px;
}

.header h1 {
  margin: 0;
  font-size: 24px;
  font-weight: 500;
}

.step-content {
  max-width: 1200px;
  margin: 0 auto;
}

.review-card {
  max-width: 800px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.news-item {
  padding: 20px 0;
}

.news-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
  border-bottom: 1px solid #ebeef5;
  padding-bottom: 10px;
}

.news-header h3 {
  margin: 0;
  flex: 1;
  color: #303133;
}

.news-time {
  color: #909399;
  font-size: 14px;
  margin-left: 20px;
}

.news-content {
  margin-bottom: 20px;
}

.news-content p {
  margin: 10px 0;
  line-height: 1.6;
  color: #606266;
}

.news-tags {
  margin-top: 15px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.news-actions {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.no-news {
  padding: 60px 0;
  text-align: center;
}

.tracking-section {
  background: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.section-header > div {
  display: flex;
  gap: 10px;
}

.section-header h2 {
  margin: 0;
  color: #303133;
}

.screenshot-section {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 15px;
  background-color: #fafafa;
}

.screenshot-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 10px;
}

.screenshot-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
  border: 1px solid #e4e7ed;
  border-radius: 4px;
  background: white;
}

.screenshot-preview {
  max-width: 100px;
  max-height: 100px;
  object-fit: cover;
  border-radius: 4px;
}

/* 统计信息样式 */
.tracking-summary {
  background: white;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.tracking-summary .el-statistic {
  text-align: center;
}

.tracking-summary .el-statistic__content {
  color: #409eff;
  font-weight: bold;
}

/* 截图相关样式 */
.screenshot-section {
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  padding: 15px;
  background-color: #fafafa;
}

.existing-screenshots {
  margin-bottom: 20px;
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
  margin-bottom: 15px;
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

.upload-section {
  border-top: 1px solid #ebeef5;
  padding-top: 15px;
}

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

/* 响应式设计 */
@media (max-width: 768px) {
  .news-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .news-time {
    margin-left: 0;
    margin-top: 5px;
  }
  
  .news-actions {
    flex-direction: column;
  }
  
  .news-tags {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>