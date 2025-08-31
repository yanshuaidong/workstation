<template>
  <div class="news-analysis">
    <el-card class="analysis-card">
      <template #header>
        <div class="card-header">
          <span class="card-title">消息面分析</span>
        </div>
      </template>
      
      <div class="content-area">
        <!-- 查询控制面板 -->
        <div class="query-panel">
          <el-form :model="queryForm" label-width="100px" inline>
            <el-form-item label="新闻提供商">
              <el-select 
                v-model="queryForm.provider" 
                placeholder="请选择新闻提供商"
                @change="onProviderChange"
                :loading="loadingProviders"
                :disabled="loadingProviders"
                style="width: 250px"
              >
                <el-option
                  v-for="provider in providers"
                  :key="provider.id"
                  :label="provider.name"
                  :value="provider.id"
                  :disabled="!provider.enabled"
                >
                  <span>{{ provider.name }}</span>
                  <span style="color: #8492a6; font-size: 13px">{{ provider.description }}</span>
                </el-option>
              </el-select>
            </el-form-item>
            
            <el-form-item label="期货品种">
              <el-select 
                v-model="queryForm.variety" 
                placeholder="请选择期货品种"
                :disabled="!queryForm.provider || loadingVarieties"
                :loading="loadingVarieties"
                filterable
                clearable
                style="width: 250px"
              >
                <el-option
                  v-for="variety in varieties"
                  :key="variety.name"
                  :label="variety.name"
                  :value="variety.name"
                />
              </el-select>
            </el-form-item>
            
            <el-form-item label="关键词">
              <el-input 
                v-model="queryForm.keyword" 
                placeholder="可选，过滤关键词"
                style="width: 250px"
                :disabled="loadingNews"
              />
            </el-form-item>
            
            <el-form-item label="等待时间">
              <el-select v-model="queryForm.waitTime" placeholder="选择等待时间" :disabled="loadingNews" style="width: 250px">
                <el-option label="30秒" :value="30000" />
                <el-option label="1分钟" :value="60000" />
                <el-option label="2分钟" :value="120000" />
                <el-option label="3分钟" :value="180000" />
              </el-select>
            </el-form-item>
            
            <el-form-item>
              <el-button 
                type="primary" 
                @click="fetchNews"
                :loading="loadingNews"
                :disabled="!queryForm.provider || !queryForm.variety || loadingNews"
              >
                查询新闻
              </el-button>
            </el-form-item>
          </el-form>
        </div>

        <!-- 新闻列表 -->
        <div class="news-list">
          <el-alert
            v-if="loadingNews"
            title="正在抓取新闻数据，请耐心等待..."
            type="info"
            :closable="false"
            show-icon
          />
          
          <div v-if="newsList.length > 0" class="news-results">
            <div class="results-header">
              <span class="results-count">共找到 {{ newsList.length }} 条新闻</span>
              <div class="header-controls">
                <el-checkbox 
                  v-model="showActions" 
                  size="small"
                >
                  显示操作列
                </el-checkbox>
                <span class="update-time">更新时间: {{ lastUpdateTime }}</span>
              </div>
            </div>
            
            <el-table :data="newsList" style="width: 100%" stripe v-loading="loadingNews">
              <el-table-column prop="title" label="新闻标题" min-width="400">
                <template #default="scope">
                  <span class="news-title">{{ scope.row.title }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="time" label="发布时间" width="180" />
              <el-table-column v-if="showActions" label="操作" width="120">
                <template #header>
                  <div style="display: flex; align-items: center; gap: 8px;">
                    <span>操作</span>
                    <el-checkbox 
                      v-model="showActions" 
                      size="small"
                      style="margin-left: 8px;"
                    >
                      显示
                    </el-checkbox>
                  </div>
                </template>
                <template #default="scope">
                  <el-button 
                    link 
                    size="small"
                    @click="openNewsLink(scope.row.link)"
                  >
                    查看
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </div>
          
          <el-empty 
            v-else-if="!loadingNews && hasSearched" 
            description="未找到相关新闻" 
          />
          
          <el-empty 
            v-else-if="!loadingNews && !hasSearched" 
            description="请选择新闻提供商和期货品种，然后点击查询按钮" 
          />
        </div>
      </div>
    </el-card>
  </div>
</template>

<script>
import { requestWithPort } from '../utils/request'

export default {
  name: 'NewsAnalysis',
  data() {
    return {
      queryForm: {
        provider: '',
        variety: '',
        keyword: '',
        waitTime: 60000 // 默认1分钟
      },
      providers: [],
      varieties: [],
      newsList: [],
      loadingProviders: false,
      loadingVarieties: false,
      loadingNews: false,
      hasSearched: false,
      lastUpdateTime: '',
      // 添加组件状态管理
      isComponentMounted: false,
      currentRequestId: 0,
      showActions: true // 默认显示操作按钮
    }
  },
  mounted() {
    this.isComponentMounted = true
    this.loadProviders()
  },
  beforeUnmount() {
    // 组件销毁时设置标志
    this.isComponentMounted = false
  },
  methods: {
    // 检查组件是否仍然挂载
    isComponentAlive() {
      return this.isComponentMounted && this.$el && this.$el.parentNode
    },

    // 安全的数据更新方法
    safeUpdate(callback) {
      if (this.isComponentAlive()) {
        this.$nextTick(() => {
          if (this.isComponentAlive()) {
            callback()
          }
        })
      }
    },

    // 加载新闻提供商列表
    async loadProviders() {
      if (!this.isComponentAlive()) return
      
      this.loadingProviders = true
      const requestId = ++this.currentRequestId
      
      try {
        const response = await requestWithPort('/api/get-news-providers', {}, 'post', 3000)
        
        // 检查请求是否仍然有效
        if (requestId === this.currentRequestId && this.isComponentAlive()) {
          this.safeUpdate(() => {
            this.providers = response || []
            // 默认选择第一个启用的提供商
            if (this.providers.length > 0) {
              const firstEnabledProvider = this.providers.find(provider => provider.enabled)
              if (firstEnabledProvider) {
                this.queryForm.provider = firstEnabledProvider.id
                // 自动加载对应的品种列表
                this.onProviderChange()
              }
            }
          })
        }
      } catch (error) {
        if (this.isComponentAlive()) {
          this.$message.error('获取新闻提供商列表失败: ' + (error.message || '未知错误'))
        }
      } finally {
        if (requestId === this.currentRequestId && this.isComponentAlive()) {
          this.safeUpdate(() => {
            this.loadingProviders = false
          })
        }
      }
    },

    // 提供商变更时加载对应的品种列表
    async onProviderChange() {
      if (!this.isComponentAlive()) return
      
      this.safeUpdate(() => {
        this.queryForm.variety = ''
        this.varieties = []
      })
      
      if (!this.queryForm.provider) {
        return
      }

      this.loadingVarieties = true
      const requestId = ++this.currentRequestId
      
      try {
        const response = await requestWithPort('/api/get-varieties-by-provider', {
          provider: this.queryForm.provider
        }, 'post', 3000)
        
        if (requestId === this.currentRequestId && this.isComponentAlive()) {
          this.safeUpdate(() => {
            this.varieties = response || []
          })
        }
      } catch (error) {
        if (this.isComponentAlive()) {
          this.$message.error('获取品种列表失败: ' + (error.message || '未知错误'))
        }
      } finally {
        if (requestId === this.currentRequestId && this.isComponentAlive()) {
          this.safeUpdate(() => {
            this.loadingVarieties = false
          })
        }
      }
    },

    // 获取新闻数据
    async fetchNews() {
      if (!this.isComponentAlive()) return
      
      if (!this.queryForm.provider || !this.queryForm.variety) {
        this.$message.warning('请选择新闻提供商和期货品种')
        return
      }

      this.loadingNews = true
      this.hasSearched = true
      const requestId = ++this.currentRequestId
      
      try {
        const requestData = {
          provider: this.queryForm.provider,
          variety: this.queryForm.variety,
          keyword: this.queryForm.keyword || '',
          waitTime: this.queryForm.waitTime
        }

        const response = await requestWithPort('/api/get-futures-news', requestData, 'post', 3000, this.queryForm.waitTime + 5000) // 额外增加5秒缓冲时间
        
        if (requestId === this.currentRequestId && this.isComponentAlive()) {
          this.safeUpdate(() => {
            this.newsList = response || []
            this.lastUpdateTime = new Date().toLocaleString()
          })
          
          if (this.newsList.length === 0) {
            this.$message.info('未找到相关新闻')
          } else {
            this.$message.success(`成功获取 ${this.newsList.length} 条新闻`)
          }
        }
      } catch (error) {
        if (this.isComponentAlive()) {
          this.$message.error('获取新闻失败: ' + (error.message || '未知错误'))
          this.safeUpdate(() => {
            this.newsList = []
          })
        }
      } finally {
        if (requestId === this.currentRequestId && this.isComponentAlive()) {
          this.safeUpdate(() => {
            this.loadingNews = false
          })
        }
      }
    },

    // 打开新闻链接
    openNewsLink(link) {
      if (!this.isComponentAlive()) return
      
      if (link) {
        try {
          window.open(link, '_blank')
        } catch (error) {
          this.$message.error('无法打开链接: ' + (error.message || '未知错误'))
        }
      } else {
        this.$message.warning('新闻链接无效')
      }
    }
  }
}
</script>

<style scoped>
.news-analysis {
  width: 100%;
}

.analysis-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #2c3e50;
}

.content-area {
  min-height: 400px;
}

.query-panel {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
  margin-bottom: 20px;
}

.news-list {
  margin-top: 20px;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding: 10px;
  background: #f0f2f5;
  border-radius: 4px;
}

.results-count {
  font-weight: 600;
  color: #2c3e50;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 15px;
}

.update-time {
  color: #666;
  font-size: 14px;
}

.news-title {
  color: #2c3e50;
  font-weight: 500;
}

.news-link {
  color: #409eff;
  text-decoration: none;
}

.news-link:hover {
  color: #66b1ff;
  text-decoration: underline;
}

.news-results {
  margin-top: 15px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .query-panel .el-form {
    display: block;
  }
  
  .query-panel .el-form-item {
    display: block;
    margin-bottom: 15px;
  }
  
  .results-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  
  .header-controls {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
}
</style> 