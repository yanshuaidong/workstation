import { createRouter, createWebHistory } from 'vue-router'
import AdaptiveNewsAnalysis from '@/components/AdaptiveNewsAnalysis.vue'
import NewsTracking from '@/components/NewsTracking.vue'
import FuturesPositions from '@/components/FuturesPositions.vue'
// import FuturesChart from '@/components/FuturesChart.vue'
import FuturesChart from '@/views/futures-chart/index.vue'
import TradingLayout from '@/views/trading/index.vue'
import TradingSignalsView from '@/views/trading/SignalsView.vue'
import TradingOperationsView from '@/views/trading/OperationsView.vue'
import TradingPositionsView from '@/views/trading/PositionsView.vue'
import TradingCurveView from '@/views/trading/CurveView.vue'
import TradingKlineView from '@/views/trading/KlineView.vue'
import TradingPoolView from '@/views/trading/PoolView.vue'


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
    path: '/trading',
    component: TradingLayout,
    meta: { title: '量化策略' },
    redirect: '/trading/signals',
    children: [
      {
        path: 'signals',
        name: 'TradingSignals',
        component: TradingSignalsView,
        meta: { title: '信号面板' }
      },
      {
        path: 'operations',
        name: 'TradingOperations',
        component: TradingOperationsView,
        meta: { title: '操作建议' }
      },
      {
        path: 'positions',
        name: 'TradingPositions',
        component: TradingPositionsView,
        meta: { title: '持仓盈亏' }
      },
      {
        path: 'curve',
        name: 'TradingCurve',
        component: TradingCurveView,
        meta: { title: '资金曲线' }
      },
      {
        path: 'kline',
        name: 'TradingKline',
        component: TradingKlineView,
        meta: { title: 'K线展示' }
      },
      {
        path: 'pool',
        name: 'TradingPool',
        component: TradingPoolView,
        meta: { title: '池子管理' }
      }
    ]
  },
]

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes
})

export default router
