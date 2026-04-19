<template>
  <div class="kline-view">
    <div class="toolbar">
      <el-select
        v-model="selectedVarietyId"
        placeholder="选择品种"
        filterable
        :filter-method="handleVarietyFilter"
        style="width: 160px"
        @change="fetchData"
      >
        <el-option
          v-for="v in filteredVarieties"
          :key="v.id"
          :label="v.name"
          :value="v.id"
        />
      </el-select>
      <el-date-picker
        v-model="dateRange"
        type="daterange"
        range-separator="—"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        value-format="YYYY-MM-DD"
        :clearable="false"
        style="width: 240px"
        @change="fetchData"
      />
    </div>

    <div v-if="!selectedVarietyId" class="empty-hint">请选择品种</div>

    <template v-else>
      <div v-loading="loading">
        <div ref="klineChart" class="chart-kline" />
        <div ref="mainForceChart" class="chart-index" />
        <div ref="retailChart" class="chart-index" />
      </div>
    </template>
  </div>
</template>

<script>
import { markRaw } from 'vue'
import * as echarts from 'echarts'
import request from '@/utils/request'
import { getAssistantVarietyListApi, getAssistantVarietyKlineApi } from '@/api'
import {
  buildAssistantIndexOption,
  buildAssistantKlineOption,
  filterVarietiesByName,
  normalizeAssistantKlineData
} from '@/utils/assistantKlineOptions.mjs'

const DAYS_DEFAULT = 60

function todayStr() {
  return new Date().toISOString().slice(0, 10)
}
function daysAgoStr(n) {
  const d = new Date()
  d.setDate(d.getDate() - n)
  return d.toISOString().slice(0, 10)
}

export default {
  name: 'KlineView',
  data() {
    return {
      varieties: [],
      filteredVarieties: [],
      selectedVarietyId: null,
      dateRange: [daysAgoStr(DAYS_DEFAULT), todayStr()],
      loading: false,
      klineInstance: null,
      mainForceInstance: null,
      retailInstance: null,
      resizeHandler: null,
    }
  },
  mounted() {
    this.resizeHandler = () => this.resizeCharts()
    window.addEventListener('resize', this.resizeHandler)
    this.fetchVarieties()
  },
  beforeUnmount() {
    if (this.resizeHandler) {
      window.removeEventListener('resize', this.resizeHandler)
      this.resizeHandler = null
    }
    this.disposeCharts()
  },
  methods: {
    async fetchVarieties() {
      try {
        const res = await request.get(getAssistantVarietyListApi)
        if (res.code === 0) {
          this.varieties = res.data.varieties
          this.filteredVarieties = [...this.varieties]
        }
      } catch (e) {
        console.error('获取品种列表失败', e)
      }
    },

    handleVarietyFilter(keyword) {
      this.filteredVarieties = filterVarietiesByName(this.varieties, keyword)
    },

    async fetchData() {
      if (!this.selectedVarietyId) return
      this.loading = true
      try {
        const [start_date, end_date] = this.dateRange
        const res = await request.get(getAssistantVarietyKlineApi, {
          params: { variety_id: this.selectedVarietyId, start_date, end_date }
        })
        if (res.code === 0) {
          await this.$nextTick()
          this.renderCharts(res.data)
        }
      } catch (e) {
        console.error('获取K线数据失败', e)
      } finally {
        this.loading = false
      }
    },

    renderCharts(data) {
      const {
        dates,
        ohlcv,
        volumes,
        mainForce,
        retail,
        varietyName
      } = normalizeAssistantKlineData(data)

      if (!dates.length) {
        this.disposeCharts()
        return
      }

      this.renderKline(dates, ohlcv, volumes, varietyName)
      this.renderIndex(this.$refs.mainForceChart, 'mainForceInstance', dates, mainForce, `${varietyName} 主力指数`, '#2f7cff')
      this.renderIndex(this.$refs.retailChart, 'retailInstance', dates, retail, `${varietyName} 散户指数`, '#db7c26')
    },

    renderKline(dates, ohlcv, volumes, title) {
      if (!this.$refs.klineChart) {
        return
      }
      if (!this.klineInstance) {
        this.klineInstance = markRaw(echarts.init(this.$refs.klineChart))
      }
      this.klineInstance.setOption(
        buildAssistantKlineOption({ dates, ohlcv, volumes, title }),
        true
      )
    },

    renderIndex(el, instanceKey, dates, values, title, color) {
      if (!el) {
        return
      }
      if (!this[instanceKey]) {
        this[instanceKey] = markRaw(echarts.init(el))
      }
      this[instanceKey].setOption(
        buildAssistantIndexOption({
          dates,
          values,
          title,
          color
        }),
        true
      )
    },

    resizeCharts() {
      ['klineInstance', 'mainForceInstance', 'retailInstance'].forEach((key) => {
        if (this[key]) {
          this[key].resize()
        }
      })
    },

    disposeCharts() {
      ['klineInstance', 'mainForceInstance', 'retailInstance'].forEach(k => {
        if (this[k]) {
          this[k].dispose()
          this[k] = null
        }
      })
    }
  }
}
</script>

<style scoped>
.kline-view {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.empty-hint {
  padding: 60px 0;
  text-align: center;
  color: #91a1b2;
  font-size: 14px;
}

.chart-kline {
  width: 100%;
  height: 360px;
  border-radius: 12px;
  border: 1px solid #edf2f7;
}

.chart-index {
  width: 100%;
  height: 180px;
  border-radius: 12px;
  border: 1px solid #edf2f7;
  margin-top: 12px;
}
</style>
