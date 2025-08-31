<template>
  <div class="prompt-formatter">
    <el-card class="form-card">
      <template #header>
        <div class="card-header">
          <span>提示词生成器</span>
        </div>
      </template>
      
      <el-form :model="formData" label-width="120px" class="form">
        <el-form-item label="期货品种">
          <el-input 
            v-model="formData.variety" 
            placeholder="请输入期货品种，如：多晶硅2509"
            clearable
          />
        </el-form-item>
        
        <el-form-item label="开始时间">
          <el-date-picker
            v-model="formData.startDate"
            type="date"
            placeholder="选择开始日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledStartDate"
          />
        </el-form-item>
        
        <el-form-item label="结束时间">
          <el-date-picker
            v-model="formData.endDate"
            type="date"
            placeholder="选择结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            :disabled-date="disabledEndDate"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="generatePrompt" :loading="generating">
            生成提示词
          </el-button>
          <el-button @click="resetForm">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card class="result-card" v-if="generatedPrompt">
      <template #header>
        <div class="card-header">
          <span>生成的提示词</span>
          <el-button link @click="copyPrompt" size="small">
            复制
          </el-button>
        </div>
      </template>
      
      <div class="prompt-content">
        <el-input
          v-model="generatedPrompt"
          type="textarea"
          :rows="8"
          readonly
          class="prompt-textarea"
        />
      </div>
    </el-card>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'

export default {
  name: 'PromptFormatter',
  setup() {
    // 获取最近一个月的开始和结束日期
    const getLastMonthRange = () => {
      const now = new Date()
      const endDate = new Date(now)
      const startDate = new Date(now)
      startDate.setMonth(startDate.getMonth() - 1)
      
      const formatDate = (date) => {
        const year = date.getFullYear()
        const month = String(date.getMonth() + 1).padStart(2, '0')
        const day = String(date.getDate()).padStart(2, '0')
        return `${year}-${month}-${day}`
      }
      
      return {
        startDate: formatDate(startDate),
        endDate: formatDate(endDate)
      }
    }
    
    const lastMonthRange = getLastMonthRange()
    
    const formData = reactive({
      variety: '',
      startDate: lastMonthRange.startDate,
      endDate: lastMonthRange.endDate
    })
    
    const generating = ref(false)
    const generatedPrompt = ref('')
    
    // 获取当前日期
    const getCurrentDate = () => {
      const now = new Date()
      const year = now.getFullYear()
      const month = String(now.getMonth() + 1).padStart(2, '0')
      const day = String(now.getDate()).padStart(2, '0')
      return `${year}年${month}月${day}日`
    }
    
    // 格式化日期显示
    const formatDateForDisplay = (dateStr) => {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      return `${year}年${month}月${day}日`
    }
    
    // 禁用开始日期（不能选择今天之后的日期）
    const disabledStartDate = (time) => {
      return time.getTime() > Date.now()
    }
    
    // 禁用结束日期（不能选择开始日期之前的日期）
    const disabledEndDate = (time) => {
      if (!formData.startDate) return false
      return time.getTime() < new Date(formData.startDate).getTime()
    }
    
    // 生成提示词
    const generatePrompt = () => {
      if (!formData.variety.trim()) {
        ElMessage.warning('请输入期货品种')
        return
      }
      
      if (!formData.startDate) {
        ElMessage.warning('请选择开始时间')
        return
      }
      
      if (!formData.endDate) {
        ElMessage.warning('请选择结束时间')
        return
      }
      
      generating.value = true
      
      // 模拟异步操作
      setTimeout(() => {
        const currentDate = getCurrentDate()
        const startDateDisplay = formatDateForDisplay(formData.startDate)
        const endDateDisplay = formatDateForDisplay(formData.endDate)
        
        generatedPrompt.value = `消息面：
目前是【${currentDate}】。请帮我查询【${startDateDisplay}】到【${endDateDisplay}】期货【${formData.variety}】的消息面情况。请注意以下几点：仅限【${startDateDisplay}】到【${endDateDisplay}】的消息面，不要使用事后分析；消息要来自较大的媒体；请以表格形式整理；表格中的"消息来源"请用文本描述，不要使用链接形式。`
        
        generating.value = false
        ElMessage.success('提示词生成成功')
      }, 500)
    }
    
    // 重置表单
    const resetForm = () => {
      formData.variety = ''
      formData.startDate = lastMonthRange.startDate
      formData.endDate = lastMonthRange.endDate
      generatedPrompt.value = ''
    }
    
    // 复制提示词
    const copyPrompt = async () => {
      try {
        await navigator.clipboard.writeText(generatedPrompt.value)
        ElMessage.success('提示词已复制到剪贴板')
      } catch (err) {
        ElMessage.error('复制失败，请手动复制')
      }
    }
    
    return {
      formData,
      generating,
      generatedPrompt,
      disabledStartDate,
      disabledEndDate,
      generatePrompt,
      resetForm,
      copyPrompt
    }
  }
}
</script>

<style scoped>
.prompt-formatter {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.form-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.form {
  margin-top: 20px;
}

.result-card {
  margin-top: 20px;
}

.prompt-content {
  margin-top: 10px;
}

.prompt-textarea {
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.5;
}

:deep(.el-form-item__label) {
  font-weight: 500;
}

:deep(.el-input__wrapper) {
  box-shadow: 0 0 0 1px #dcdfe6 inset;
}

:deep(.el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px #c0c4cc inset;
}

:deep(.el-textarea__inner) {
  font-family: 'Courier New', monospace;
  resize: vertical;
}
</style>