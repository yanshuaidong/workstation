import { createRouter, createWebHistory } from 'vue-router'
import ApiDataFetcher from '@/components/ApiDataFetcher.vue'
import TechnicalAnalysis from '@/components/TechnicalAnalysis.vue'

const routes = [
  {
    path: '/',
    redirect: '/position-structure'
  },
  {
    path: '/position-structure',
    name: 'PositionStructure',
    component: ApiDataFetcher,
    meta: {
      title: '机构持仓结构'
    }
  },
  {
    path: '/technical-analysis',
    name: 'TechnicalAnalysis',
    component: TechnicalAnalysis,
    meta: {
      title: '技术面分析'
    }
  },
  {
    path: '/news-analysis',
    name: 'NewsAnalysis',
    component: () => import('@/components/NewsAnalysis.vue'),
    meta: {
      title: '消息面分析'
    }
  },
  {
    path: '/prompt-formatter',
    name: 'PromptFormatter',
    component: () => import('@/components/PromptFormatter.vue'),
    meta: {
      title: '提示词格式化'
    }
  }
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router