import { createRouter, createWebHistory } from 'vue-router'
import AdaptiveNewsAnalysis from '@/components/AdaptiveNewsAnalysis.vue'
import NewsTracking from '@/components/NewsTracking.vue'
import FuturesPositions from '@/components/FuturesPositions.vue'
import FuturesChart from '@/components/FuturesChart.vue'

const routes = [
  {
    path: '/',
    redirect: '/news-analysis'
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