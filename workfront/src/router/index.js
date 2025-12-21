import { createRouter, createWebHistory } from 'vue-router'
// import ApiDataFetcher from '@/components/ApiDataFetcher.vue'
// import TechnicalAnalysis from '@/components/TechnicalAnalysis.vue'
import FuturesUpdate from '@/components/FuturesUpdate.vue'
import AdaptiveNewsAnalysis from '@/components/AdaptiveNewsAnalysis.vue'
// workfront/src/components/NewsTracking.vue
import NewsTracking from '@/components/NewsTracking.vue'
import FuturesPositions from '@/components/FuturesPositions.vue'
import FuturesChart from '@/components/FuturesChart.vue'

const routes = [
  {
    path: '/',
    redirect: '/futures-update'
  },
  {
    path: '/news-analysis',
    name: 'NewsAnalysis',
    component: AdaptiveNewsAnalysis,
    meta: {
      title: '消息面分析'
    }
  },
  {
    path: '/news-tracking',
    name: 'NewsTracking',
    component: NewsTracking,
    meta: {
      title: '消息跟踪'
    }
  },
  {
    path: '/futures-update',
    name: 'FuturesUpdate',  
    component: FuturesUpdate,
    meta: {
      title: '期货数据更新'
    }
  },
  {
    path: '/positions',
    name: 'FuturesPositions',
    component: FuturesPositions,
    meta: {
      title: '我的持仓'
    }
  },
  {
    path: '/futures-chart',
    name: 'FuturesChart',
    component: FuturesChart,
    meta: {
      title: '期货K线图'
    }
  },
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router