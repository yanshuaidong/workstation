<template>
  <el-dialog
    :model-value="visible"
    :title="localForm.id ? '编辑事件' : '添加事件'"
    width="600px"
    destroy-on-close
    @update:model-value="handleVisibleChange"
  >
    <el-form 
      ref="eventFormRef"
      :model="localForm" 
      :rules="eventFormRules"
      label-width="100px"
    >
      <el-form-item label="品种" prop="symbol">
        <el-input :value="selectedContractName + ' (' + selectedContract + ')'" disabled />
      </el-form-item>

      <el-form-item label="事件日期" prop="event_date">
        <el-date-picker
          v-model="localForm.event_date"
          type="date"
          placeholder="选择日期"
          format="YYYY-MM-DD"
          value-format="YYYY-MM-DD"
          style="width: 100%"
        />
      </el-form-item>

      <el-form-item label="标题" prop="title">
        <el-input 
          v-model="localForm.title" 
          placeholder="如：美联储降息25个基点"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="内容" prop="content">
        <el-input
          v-model="localForm.content"
          type="textarea"
          :rows="4"
          placeholder="详细描述事件内容..."
        />
      </el-form-item>

      <el-row :gutter="20">
        <el-col :span="12">
          <el-form-item label="方向判断" prop="outlook">
            <el-select v-model="localForm.outlook" placeholder="选择方向" clearable style="width: 100%">
              <el-option label="看多 (Bullish)" value="bullish">
                <span style="color: #ef5350; display: flex; align-items: center; gap: 8px;">
                  <span style="display: inline-block; width: 8px; height: 8px; background: #ef5350; border-radius: 2px;"></span>
                  看多 (Bullish)
                </span>
              </el-option>
              <el-option label="看空 (Bearish)" value="bearish">
                <span style="color: #26a69a; display: flex; align-items: center; gap: 8px;">
                  <span style="display: inline-block; width: 8px; height: 8px; background: #26a69a; border-radius: 2px;"></span>
                  看空 (Bearish)
                </span>
              </el-option>
              <el-option label="震荡 (Ranging)" value="ranging">
                <span style="color: #ff9800; display: flex; align-items: center; gap: 8px;">
                  <span style="display: inline-block; width: 8px; height: 8px; background: #ff9800; border-radius: 2px; transform: rotate(45deg);"></span>
                  震荡 (Ranging)
                </span>
              </el-option>
              <el-option label="不确定 (Uncertain)" value="uncertain">
                <span style="color: #78909c; display: flex; align-items: center; gap: 8px;">
                  <span style="display: inline-block; width: 8px; height: 8px; background: #78909c; border-radius: 50%;"></span>
                  不确定 (Uncertain)
                </span>
              </el-option>
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="判断强度" prop="strength">
            <el-slider 
              v-model="localForm.strength" 
              :min="1" 
              :max="10" 
              :step="1"
              show-stops
              :marks="strengthMarks"
            />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>

    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button 
        type="primary" 
        @click="handleSubmit"
        :loading="submitting"
      >
        {{ localForm.id ? '保存修改' : '确认添加' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script>
export default {
  name: 'EventDialog',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    eventForm: {
      type: Object,
      default: () => ({
        id: null,
        symbol: '',
        event_date: '',
        title: '',
        content: '',
        outlook: '',
        strength: 5
      })
    },
    selectedContract: {
      type: String,
      default: ''
    },
    selectedContractName: {
      type: String,
      default: ''
    },
    submitting: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      localForm: {
        id: null,
        symbol: '',
        event_date: '',
        title: '',
        content: '',
        outlook: '',
        strength: 5
      },
      eventFormRules: {
        event_date: [
          { required: true, message: '请选择事件日期', trigger: 'change' }
        ],
        title: [
          { required: true, message: '请输入事件标题', trigger: 'blur' }
        ]
      },
      strengthMarks: {
        1: '弱',
        5: '中',
        10: '强'
      }
    }
  },
  emits: ['update:visible', 'submit', 'cancel'],
  watch: {
    eventForm: {
      handler(newVal) {
        // 当 prop 变化时，更新本地副本
        this.localForm = { ...newVal }
      },
      deep: true,
      immediate: true
    }
  },
  methods: {
    handleVisibleChange(val) {
      this.$emit('update:visible', val)
    },
    async handleSubmit() {
      const formRef = this.$refs.eventFormRef
      if (!formRef) return
      
      const valid = await formRef.validate().catch(() => false)
      if (!valid) return
      
      this.$emit('submit', this.localForm)
    },
    handleCancel() {
      this.$emit('cancel')
      this.handleVisibleChange(false)
    }
  }
}
</script>

<style scoped>
/* 可以根据需要添加自定义样式 */
</style>
