<template>
  <div class="pool-view">
    <div class="pool-header">
      <span class="pool-hint">激活品种 {{ activeCount }} / {{ pool.length }}</span>
      <el-button size="small" :loading="loading" @click="fetchPool">刷新</el-button>
    </div>

    <el-table v-loading="loading" :data="pool" stripe class="pool-table">
      <el-table-column label="品种" prop="variety_name" width="140" />
      <el-table-column label="板块" width="200">
        <template #default="{ row }">
          <el-select
            v-model="row.sector"
            size="small"
            filterable
            allow-create
            default-first-option
            placeholder="选择/输入板块"
            :loading="row._updating"
            @change="(val) => updateSector(row, val)"
          >
            <el-option v-for="s in sectors" :key="s" :label="s" :value="s" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100" align="center">
        <template #default="{ row }">
          <el-switch
            :model-value="row.is_active === 1"
            :loading="row._updating"
            @change="(val) => toggleActive(row, val)"
          />
        </template>
      </el-table-column>
    </el-table>
  </div>
</template>

<script>
import request from '@/utils/request'
import { getTradingPoolApi, patchTradingPoolApi } from '@/api'
import { ElMessage } from 'element-plus'

export default {
  name: 'PoolView',
  data() {
    return {
      pool: [],
      sectors: [],
      loading: false,
    }
  },
  computed: {
    activeCount() {
      return this.pool.filter(r => r.is_active === 1).length
    }
  },
  mounted() {
    this.fetchPool()
  },
  methods: {
    async fetchPool() {
      this.loading = true
      try {
        const res = await request.get(getTradingPoolApi)
        if (res.code === 0) {
          this.pool = (res.data.pool || []).map(r => ({ ...r, _updating: false }))
          this.sectors = res.data.sectors || []
        }
      } finally {
        this.loading = false
      }
    },
    async patchRow(row, payload, successMsg) {
      row._updating = true
      try {
        const res = await request.patch(patchTradingPoolApi(row.variety_id), payload)
        if (res.code === 0) {
          if (payload.is_active !== undefined) row.is_active = res.data.is_active
          if (payload.sector !== undefined) row.sector = res.data.sector
          if (payload.sector && !this.sectors.includes(res.data.sector)) {
            this.sectors = [...this.sectors, res.data.sector].sort()
          }
          ElMessage.success(successMsg)
          return true
        }
        ElMessage.error(res.message || '操作失败')
        return false
      } catch {
        ElMessage.error('请求失败')
        return false
      } finally {
        row._updating = false
      }
    },
    async toggleActive(row, val) {
      const target = val ? 1 : 0
      if (target === 1 && !row.sector) {
        ElMessage.warning('请先选择板块再激活')
        return
      }
      await this.patchRow(row, { is_active: target }, `${row.variety_name} 已${val ? '激活' : '停用'}`)
    },
    async updateSector(row, val) {
      const sector = (val || '').trim()
      await this.patchRow(row, { sector }, `${row.variety_name} 板块已更新为 ${sector || '空'}`)
    }
  }
}
</script>

<style scoped>
.pool-view { padding: 4px 0; }
.pool-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.pool-hint { color: #5a7896; font-size: 13px; }
.pool-table { width: 100%; }
</style>
