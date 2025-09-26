<template>
  <component 
    :is="currentComponent" 
    v-bind="$attrs"
  />
</template>

<script>
import NewsAnalysis from './NewsAnalysis.vue'
import mNewsAnalysis from './mNewsAnalysis.vue'
import { isMobile, onDeviceChange } from '@/utils/deviceDetector'

export default {
  name: 'AdaptiveNewsAnalysis',
  inheritAttrs: false,
  emits: [],
  components: {
    NewsAnalysis,
    mNewsAnalysis
  },
  data() {
    return {
      currentComponent: null,
      deviceChangeCleanup: null
    }
  },
  
  created() {
    // 初始化时选择合适的组件
    this.updateComponent()
    
    // 监听设备变化
    this.deviceChangeCleanup = onDeviceChange(() => {
      this.updateComponent()
    })
  },
  
  beforeUnmount() {
    // 清理设备变化监听器
    if (this.deviceChangeCleanup) {
      this.deviceChangeCleanup()
    }
  },
  
  methods: {
    updateComponent() {
      const isMobileDevice = isMobile()
      
      // 根据设备类型选择组件
      this.currentComponent = isMobileDevice ? 'mNewsAnalysis' : 'NewsAnalysis'
      
      // 输出调试信息
      console.log(`[AdaptiveNewsAnalysis] 设备类型: ${isMobileDevice ? '移动端' : 'PC端'}, 使用组件: ${this.currentComponent}`)
    }
  }
}
</script>

<style scoped>
/* 无需额外样式，完全由子组件控制 */
</style> 