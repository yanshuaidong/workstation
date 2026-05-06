<template>
  <div class="trading-page">
    <div class="toolbar toolbar-spread">
      <span class="toolbar-hint">激活品种 {{ activeCount }} / {{ pool.length }}</span>
      <el-button :loading="loading" @click="fetchPool">刷新</el-button>
    </div>

    <div class="section-title">品种池</div>
    <el-table v-loading="loading" :data="pool" stripe class="data-table">
      <el-table-column label="品种" prop="variety_name" min-width="120" />
      <el-table-column label="板块" min-width="200">
        <template #default="{ row }">
          <el-select
            v-model="row.sector"
            class="sector-select"
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
            class="pool-switch"
            :model-value="row.is_active === 1"
            :loading="row._updating"
            @change="(val) => toggleActive(row, val)"
          />
        </template>
      </el-table-column>
    </el-table>

    <div v-if="!loading && !pool.length" class="empty-hint">暂无池内品种</div>
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
.trading-page {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
}

.toolbar-spread {
  justify-content: space-between;
}

.toolbar-hint {
  color: #8a8a8a;
  font-size: 13px;
}

.section-title {
  color: #1a1a1a;
  font-size: 14px;
  font-weight: 600;
}

.data-table {
  width: 100%;
}

.sector-select {
  width: 100%;
}

/* 与交易页主色一致，避免默认主题蓝 */
.pool-switch {
  --el-switch-on-color: #1a1a1a;
  --el-switch-off-color: #d0d0d0;
}

.empty-hint {
  padding: 20px 0;
  color: #8a8a8a;
  font-size: 13px;
}
</style>
