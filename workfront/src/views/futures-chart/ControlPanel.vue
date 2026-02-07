<template>
  <el-card class="control-card">
    <template #header>
      <div class="card-header">
        <span>期货K线图</span>
      </div>
    </template>

    <el-row :gutter="20" align="middle">
      <!-- 合约选择 -->
      <el-col :span="6">
        <el-form-item label="选择品种">
          <el-select
            :model-value="selectedContract"
            placeholder="请选择期货品种"
            style="width: 100%"
            @change="handleContractChange"
            filterable
            clearable
          >
            <el-option
              v-for="contract in contractsList"
              :key="contract.symbol"
              :label="`${contract.name} (${contract.symbol})`"
              :value="contract.symbol"
            />
          </el-select>
        </el-form-item>
      </el-col>

      <!-- 日期范围选择 -->
      <el-col :span="8">
        <el-form-item label="日期范围">
          <el-date-picker
            :model-value="dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
            style="width: 100%"
            @update:model-value="handleDateRangeChange"
          />
        </el-form-item>
      </el-col>

      <!-- 查询按钮 -->
      <el-col :span="4">
        <el-form-item label=" ">
          <el-button
            type="primary"
            @click="handleQuery"
            :loading="loading"
            icon="Search"
            style="width: 100%"
          >
            查询
          </el-button>
        </el-form-item>
      </el-col>

      <!-- 快捷日期 -->
      <el-col :span="6">
        <el-form-item label="快捷选择">
          <el-button-group>
            <el-button size="small" @click="handleSetDateRange(30)">近30天</el-button>
            <el-button size="small" @click="handleSetDateRange(60)">近60天</el-button>
            <el-button size="small" @click="handleSetDateRange(90)">近90天</el-button>
          </el-button-group>
        </el-form-item>
      </el-col>
    </el-row>
  </el-card>
</template>

<script>
export default {
  name: 'ControlPanel',
  props: {
    contractsList: {
      type: Array,
      default: () => []
    },
    selectedContract: {
      type: String,
      default: ''
    },
    dateRange: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    }
  },
  emits: ['update:selectedContract', 'update:dateRange', 'contract-change', 'query', 'set-date-range'],
  methods: {
    handleContractChange(symbol) {
      this.$emit('update:selectedContract', symbol)
      this.$emit('contract-change', symbol)
    },
    handleDateRangeChange(range) {
      this.$emit('update:dateRange', range)
    },
    handleQuery() {
      this.$emit('query')
    },
    handleSetDateRange(days) {
      this.$emit('set-date-range', days)
    }
  }
}
</script>

<style scoped>
.control-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
</style>
