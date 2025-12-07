<template>
  <div class="futures-positions">
    <!-- 标题栏 -->
    <el-card class="header-card">
      <template #header>
        <div class="card-header">
          <span>我的持仓</span>
          <el-button type="primary" @click="showCreateDialog" icon="Plus">
            新增持仓
          </el-button>
        </div>
      </template>

      <!-- 统计信息 -->
      <el-row :gutter="20" class="stats-row">
        <el-col :span="4">
          <div class="stat-item">
            <div class="stat-label">总持仓</div>
            <div class="stat-value">{{ stats.total }}</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item">
            <div class="stat-label">有仓</div>
            <div class="stat-value hold">{{ stats.hold_count }}</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item">
            <div class="stat-label">空仓</div>
            <div class="stat-value flat">{{ stats.flat_count }}</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item">
            <div class="stat-label">多头持仓</div>
            <div class="stat-value long">{{ stats.long_count }}</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item">
            <div class="stat-label">空头持仓</div>
            <div class="stat-value short">{{ stats.short_count }}</div>
          </div>
        </el-col>
        <el-col :span="4">
          <div class="stat-item">
            <el-button @click="loadStats" icon="Refresh" text>刷新统计</el-button>
          </div>
        </el-col>
      </el-row>
    </el-card>

    <!-- 持仓列表 -->
    <el-card class="positions-card">
      <template #header>
        <div class="card-header">
          <span>持仓列表</span>
        </div>
      </template>

      <!-- 筛选区域 -->
      <div class="filter-section">
        <el-row :gutter="20">
          <el-col :span="6">
            <el-input
              v-model="filters.symbol"
              placeholder="搜索品种"
              clearable
              @clear="loadPositions"
              @keyup.enter="loadPositions"
            >
              <template #prefix>
                <el-icon><Search /></el-icon>
              </template>
            </el-input>
          </el-col>
          <el-col :span="5">
            <el-select
              v-model="filters.status"
              placeholder="持仓状态"
              clearable
              @change="loadPositions"
              style="width: 100%"
            >
              <el-option label="有仓" value="1" />
              <el-option label="空仓" value="0" />
            </el-select>
          </el-col>
          <el-col :span="5">
            <el-select
              v-model="filters.direction"
              placeholder="持仓方向"
              clearable
              @change="loadPositions"
              style="width: 100%"
            >
              <el-option label="多 (LONG)" value="LONG" />
              <el-option label="空 (SHORT)" value="SHORT" />
              <el-option label="多" value="多" />
              <el-option label="空" value="空" />
            </el-select>
          </el-col>
          <el-col :span="4">
            <el-button type="primary" @click="loadPositions" icon="Search">
              查询
            </el-button>
          </el-col>
          <el-col :span="4">
            <el-button @click="resetFilters" icon="RefreshLeft">
              重置
            </el-button>
          </el-col>
        </el-row>
      </div>

      <!-- 持仓表格 -->
      <el-table
        :data="positions"
        v-loading="loading"
        stripe
        border
        style="width: 100%"
        empty-text="暂无持仓记录"
      >
        <el-table-column type="index" label="序号" width="60" :index="(index) => index + 1" />
        <el-table-column prop="symbol" label="品种" width="120">
          <template #default="scope">
            <span class="symbol-text">{{ scope.row.symbol }}</span>
          </template>
        </el-table-column>
        <el-table-column label="方向" width="120">
          <template #default="scope">
            <el-tag 
              :type="getDirectionType(scope.row.direction)"
              size="default"
            >
              {{ scope.row.direction }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="持仓状态" width="120">
          <template #default="scope">
            <el-tag 
              :type="scope.row.status === 1 ? 'success' : 'info'"
              size="default"
              @click="toggleStatus(scope.row)"
              style="cursor: pointer;"
            >
              {{ scope.row.status_text }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column prop="updated_at" label="更新时间" width="180" />
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="scope">
            <el-button
              type="primary"
              size="small"
              @click="showEditDialog(scope.row)"
              icon="Edit"
            >
              编辑
            </el-button>
            <el-button
              :type="scope.row.status === 1 ? 'warning' : 'success'"
              size="small"
              @click="toggleStatus(scope.row)"
            >
              {{ scope.row.status === 1 ? '平仓' : '开仓' }}
            </el-button>
            <el-popconfirm
              title="确定要删除这条持仓记录吗？"
              @confirm="deletePosition(scope.row)"
            >
              <template #reference>
                <el-button type="danger" size="small" icon="Delete">
                  删除
                </el-button>
              </template>
            </el-popconfirm>
          </template>
        </el-table-column>
      </el-table>

      <!-- 底部信息 -->
      <div class="table-footer">
        <span>共 {{ positions.length }} 条记录</span>
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑持仓' : '新增持仓'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form
        ref="formRef"
        :model="form"
        :rules="formRules"
        label-width="100px"
        label-position="right"
      >
        <el-form-item label="品种" prop="symbol">
          <el-input
            v-model="form.symbol"
            placeholder="请输入品种代码或名称，如：CU / 铜 / SC / 石油"
            clearable
          />
        </el-form-item>
        <el-form-item label="方向" prop="direction">
          <el-select v-model="form.direction" placeholder="请选择方向" style="width: 100%">
            <el-option label="多 (LONG)" value="LONG" />
            <el-option label="空 (SHORT)" value="SHORT" />
            <el-option label="多" value="多" />
            <el-option label="空" value="空" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio :label="1">有仓 (HOLD)</el-radio>
            <el-radio :label="0">空仓 (FLAT)</el-radio>
          </el-radio-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm" :loading="submitting">
            {{ isEdit ? '保存' : '创建' }}
          </el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import request from '@/utils/request'
import {
  getPositionsListApi,
  createPositionApi,
  updatePositionApi,
  deletePositionApi,
  getPositionsStatsApi,
  togglePositionStatusApi
} from '@/api'

export default {
  name: 'FuturesPositions',
  data() {
    return {
      // 统计数据
      stats: {
        total: 0,
        hold_count: 0,
        flat_count: 0,
        long_count: 0,
        short_count: 0
      },
      
      // 持仓列表
      positions: [],
      loading: false,
      
      // 筛选条件
      filters: {
        symbol: '',
        status: '',
        direction: ''
      },
      
      // 对话框
      dialogVisible: false,
      isEdit: false,
      editingId: null,
      submitting: false,
      
      // 表单数据
      form: {
        symbol: '',
        direction: '',
        status: 1
      },
      
      // 表单验证规则
      formRules: {
        symbol: [
          { required: true, message: '请输入品种', trigger: 'blur' }
        ],
        direction: [
          { required: true, message: '请选择方向', trigger: 'change' }
        ]
      }
    }
  },
  
  async mounted() {
    await this.loadStats()
    await this.loadPositions()
  },
  
  methods: {
    // 加载统计数据
    async loadStats() {
      try {
        const response = await request.get(getPositionsStatsApi)
        if (response.code === 0) {
          this.stats = response.data
        }
      } catch (error) {
        console.error('加载统计数据失败:', error)
      }
    },
    
    // 加载持仓列表
    async loadPositions() {
      this.loading = true
      try {
        const params = new URLSearchParams()
        if (this.filters.symbol) {
          params.append('symbol', this.filters.symbol)
        }
        if (this.filters.status !== '') {
          params.append('status', this.filters.status)
        }
        if (this.filters.direction) {
          params.append('direction', this.filters.direction)
        }
        
        const url = params.toString() 
          ? `${getPositionsListApi}?${params}` 
          : getPositionsListApi
        
        const response = await request.get(url)
        if (response.code === 0) {
          this.positions = response.data.positions || []
        } else {
          this.$message.error(`加载失败: ${response.message}`)
        }
      } catch (error) {
        console.error('加载持仓列表失败:', error)
        this.$message.error(`加载失败: ${error.message}`)
      } finally {
        this.loading = false
      }
    },
    
    // 重置筛选
    resetFilters() {
      this.filters = {
        symbol: '',
        status: '',
        direction: ''
      }
      this.loadPositions()
    },
    
    // 获取方向标签类型
    getDirectionType(direction) {
      const longValues = ['LONG', '多']
      const shortValues = ['SHORT', '空']
      
      if (longValues.includes(direction)) {
        return 'success'
      } else if (shortValues.includes(direction)) {
        return 'danger'
      }
      return 'info'
    },
    
    // 显示新增对话框
    showCreateDialog() {
      this.isEdit = false
      this.editingId = null
      this.form = {
        symbol: '',
        direction: '',
        status: 1
      }
      this.dialogVisible = true
    },
    
    // 显示编辑对话框
    showEditDialog(row) {
      this.isEdit = true
      this.editingId = row.id
      this.form = {
        symbol: row.symbol,
        direction: row.direction,
        status: row.status
      }
      this.dialogVisible = true
    },
    
    // 提交表单
    async submitForm() {
      try {
        await this.$refs.formRef.validate()
      } catch {
        return
      }
      
      this.submitting = true
      try {
        let response
        if (this.isEdit) {
          response = await request.put(`${updatePositionApi}/${this.editingId}`, this.form)
        } else {
          response = await request.post(createPositionApi, this.form)
        }
        
        if (response.code === 0) {
          this.$message.success(this.isEdit ? '更新成功' : '创建成功')
          this.dialogVisible = false
          await this.loadPositions()
          await this.loadStats()
        } else {
          this.$message.error(response.message)
        }
      } catch (error) {
        console.error('提交失败:', error)
        this.$message.error(`提交失败: ${error.message}`)
      } finally {
        this.submitting = false
      }
    },
    
    // 切换持仓状态
    async toggleStatus(row) {
      try {
        const response = await request.post(`${togglePositionStatusApi}/${row.id}`)
        if (response.code === 0) {
          this.$message.success(response.message)
          await this.loadPositions()
          await this.loadStats()
        } else {
          this.$message.error(response.message)
        }
      } catch (error) {
        console.error('切换状态失败:', error)
        this.$message.error(`切换失败: ${error.message}`)
      }
    },
    
    // 删除持仓
    async deletePosition(row) {
      try {
        const response = await request.delete(`${deletePositionApi}/${row.id}`)
        if (response.code === 0) {
          this.$message.success('删除成功')
          await this.loadPositions()
          await this.loadStats()
        } else {
          this.$message.error(response.message)
        }
      } catch (error) {
        console.error('删除失败:', error)
        this.$message.error(`删除失败: ${error.message}`)
      }
    }
  }
}
</script>

<style scoped>
.futures-positions {
  padding: 20px;
}

.header-card,
.positions-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}

/* 统计信息样式 */
.stats-row {
  margin-top: 10px;
}

.stat-item {
  text-align: center;
  padding: 15px;
  background: linear-gradient(135deg, #f8f9fa 0%, #fff 100%);
  border-radius: 8px;
  border: 1px solid #ebeef5;
  transition: all 0.3s ease;
}

.stat-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.stat-label {
  font-size: 13px;
  color: #909399;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-value.hold {
  color: #67c23a;
}

.stat-value.flat {
  color: #909399;
}

.stat-value.long {
  color: #e6a23c;
}

.stat-value.short {
  color: #f56c6c;
}

/* 筛选区域 */
.filter-section {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 6px;
}

/* 品种文本样式 */
.symbol-text {
  font-weight: 600;
  color: #409eff;
}

/* 表格底部 */
.table-footer {
  margin-top: 15px;
  text-align: right;
  color: #909399;
  font-size: 14px;
}

/* 对话框表单 */
.el-form {
  padding: 10px 20px;
}

/* 响应式布局 */
@media (max-width: 1200px) {
  .stats-row .el-col {
    margin-bottom: 15px;
  }
}

@media (max-width: 768px) {
  .futures-positions {
    padding: 10px;
  }
  
  .stat-value {
    font-size: 22px;
  }
  
  .filter-section .el-col {
    margin-bottom: 10px;
  }
}
</style>

