import { createRouter, createWebHistory } from 'vue-router'
// import ApiDataFetcher from '@/components/ApiDataFetcher.vue'
// import TechnicalAnalysis from '@/components/TechnicalAnalysis.vue'
import FuturesUpdate from '@/components/FuturesUpdate.vue'
import NewsAnalysis from '@/components/NewsAnalysis.vue'

const routes = [
  {
    path: '/',
    redirect: '/futures-update'
  },
  {
    path: '/news-analysis',
    name: 'NewsAnalysis',
    component: NewsAnalysis,
    meta: {
      title: '消息面分析'
    }
  },
  // {
  //   path: '/position-structure',
  //   name: 'PositionStructure',
  //   component: ApiDataFetcher,
  //   meta: {
  //     title: '机构持仓结构'
  //   }
  // },
  // {
  //   path: '/technical-analysis',
  //   name: 'TechnicalAnalysis',
  //   component: TechnicalAnalysis,
  //   meta: {
  //     title: '技术面分析'
  //   }
  // },
  // {
  //   path: '/news-analysis',
  //   name: 'NewsAnalysis',
  //   component: () => import('@/components/NewsAnalysis.vue'),
  //   meta: {
  //     title: '消息面分析'
  //   }
  // },
  // {
  //   path: '/prompt-formatter',
  //   name: 'PromptFormatter',
  //   component: () => import('@/components/PromptFormatter.vue'),
  //   meta: {
  //     title: '提示词格式化'
  //   }
  // },
  {
    path: '/futures-update',
    name: 'FuturesUpdate',  
    component: FuturesUpdate,
    meta: {
      title: '期货数据更新'
    }
  },
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router