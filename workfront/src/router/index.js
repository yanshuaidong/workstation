import { createRouter, createWebHistory } from 'vue-router'
import AdaptiveNewsAnalysis from '@/components/AdaptiveNewsAnalysis.vue'
import NewsTracking from '@/components/NewsTracking.vue'
import FuturesPositions from '@/components/FuturesPositions.vue'
// import FuturesChart from '@/components/FuturesChart.vue'
import FuturesChart from '@/views/futures-chart/index.vue'
import AssistantLayout from '@/views/assistant/index.vue'
import AssistantSignalsView from '@/views/assistant/SignalsView.vue'
import AssistantOperationsView from '@/views/assistant/OperationsView.vue'
import AssistantPositionsView from '@/views/assistant/PositionsView.vue'
import AssistantCurveView from '@/views/assistant/CurveView.vue'
import AssistantKlineView from '@/views/assistant/KlineView.vue'


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
  {
    path: '/assistant',
    component: AssistantLayout,
    meta: {
      title: '辅助决策'
    },
    redirect: '/assistant/signals',
    children: [
      {
        path: 'signals',
        name: 'AssistantSignals',
        component: AssistantSignalsView,
        meta: {
          title: '信号面板'
        }
      },
      {
        path: 'operations',
        name: 'AssistantOperations',
        component: AssistantOperationsView,
        meta: {
          title: '操作建议'
        }
      },
      {
        path: 'positions',
        name: 'AssistantPositions',
        component: AssistantPositionsView,
        meta: {
          title: '持仓与盈亏'
        }
      },
      {
        path: 'curve',
        name: 'AssistantCurve',
        component: AssistantCurveView,
        meta: {
          title: '资金曲线'
        }
      },
      {
        path: 'kline',
        name: 'AssistantKline',
        component: AssistantKlineView,
        meta: {
          title: 'K线展示'
        }
      }
    ]
  },
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
