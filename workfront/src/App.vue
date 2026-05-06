<template>
  <div id="app">
    <el-container class="app-container">
      <!-- 固定顶部 -->
      <el-header class="app-header">
        <div class="header-content">
          <el-button 
            v-if="isMobileDevice"
            class="mobile-menu-toggle"
            @click="toggleMobileMenu"
            icon="Menu"
            text
            size="large"
          />
          
          <h1 class="header-title">我爱学习</h1>
        </div>
      </el-header>
      
      <!-- 移动端折叠菜单面板 -->
      <el-collapse-transition>
        <div v-if="isMobileDevice && mobileMenuVisible" class="mobile-menu-panel">
          <el-menu
            :default-active="activeMenuPath"
            router
            class="mobile-menu"
            @select="handleMobileMenuSelect"
          >
            <el-menu-item index="/news-analysis" class="mobile-menu-item">
              <el-icon class="menu-icon"><ChatDotRound /></el-icon>
              <span class="menu-text">消息面分析</span>
            </el-menu-item>
            <el-menu-item index="/news-tracking" class="mobile-menu-item">
              <el-icon class="menu-icon"><TrendCharts /></el-icon>
              <span class="menu-text">消息跟踪</span>
            </el-menu-item>
            <el-menu-item index="/positions" class="mobile-menu-item">
              <el-icon class="menu-icon"><Wallet /></el-icon>
              <span class="menu-text">我的持仓</span>
            </el-menu-item>
            <el-menu-item index="/futures-chart" class="mobile-menu-item">
              <el-icon class="menu-icon"><DataLine /></el-icon>
              <span class="menu-text">期货K线图</span>
            </el-menu-item>
            <el-menu-item index="/trading/signals" class="mobile-menu-item">
              <el-icon class="menu-icon"><TrendCharts /></el-icon>
              <span class="menu-text">量化策略</span>
            </el-menu-item>
          </el-menu>
        </div>
      </el-collapse-transition>
      
      <el-container class="main-container">
        <!-- PC端固定左侧菜单 -->
        <el-aside 
          v-if="!isMobileDevice" 
          width="232px" 
          class="app-aside"
        >
          <el-menu
            :default-active="activeMenuPath"
            router
            class="side-menu"
          >
            <el-menu-item index="/news-analysis" class="menu-item">
              <el-icon class="menu-icon"><ChatDotRound /></el-icon>
              <span class="menu-text">消息分析</span>
            </el-menu-item>
            <el-menu-item index="/news-tracking" class="menu-item">
              <el-icon class="menu-icon"><TrendCharts /></el-icon>
              <span class="menu-text">消息跟踪</span>
            </el-menu-item>
            <el-menu-item index="/positions" class="menu-item">
              <el-icon class="menu-icon"><Wallet /></el-icon>
              <span class="menu-text">我的持仓</span>
            </el-menu-item>
            <el-menu-item index="/futures-chart" class="menu-item">
              <el-icon class="menu-icon"><DataLine /></el-icon>
              <span class="menu-text">期货K线</span>
            </el-menu-item>
            <el-menu-item index="/trading/signals" class="menu-item">
              <el-icon class="menu-icon"><TrendCharts /></el-icon>
              <span class="menu-text">量化策略</span>
            </el-menu-item>
          </el-menu>
        </el-aside>
        
        <!-- 可滚动的内容区域 -->
        <el-main class="app-main">
          <div class="content-wrapper">
            <router-view />
          </div>
        </el-main>
      </el-container>
    </el-container>
    
    <!-- 移动端菜单遮罩层 -->
    <div 
      v-if="isMobileDevice && mobileMenuVisible" 
      class="mobile-menu-overlay"
      @click="closeMobileMenu"
    ></div>
  </div>
</template>

<script>
import { DataBoard, TrendCharts, ChatDotRound, Edit, Wallet, DataLine } from '@element-plus/icons-vue'
import { markRaw } from 'vue'
import { isMobile, onDeviceChange } from '@/utils/deviceDetector'

export default {
  name: 'App',
  data() {
    return {
      DataBoard: markRaw(DataBoard),
      TrendCharts: markRaw(TrendCharts),
      ChatDotRound: markRaw(ChatDotRound),
      Edit: markRaw(Edit),
      Wallet: markRaw(Wallet),
      DataLine: markRaw(DataLine),
      
      // 设备检测
      isMobileDevice: false,
      deviceChangeCleanup: null,
      
      // 移动端菜单状态
      mobileMenuVisible: false
    }
  },
  computed: {
    activeMenuPath() {
      return this.$route.path
    }
  },
  
  mounted() {
    // 初始化设备检测
    this.updateDeviceType()
    
    // 监听设备变化
    this.deviceChangeCleanup = onDeviceChange(() => {
      this.updateDeviceType()
    })
  },
  
  beforeUnmount() {
    // 清理设备变化监听器
    if (this.deviceChangeCleanup) {
      this.deviceChangeCleanup()
    }
  },
  
  watch: {
    // 监听路由变化，移动端路由切换时关闭菜单
    '$route'() {
      if (this.isMobileDevice && this.mobileMenuVisible) {
        this.mobileMenuVisible = false
      }
    }
  },
  
  methods: {
    // 更新设备类型
    updateDeviceType() {
      const wasMobile = this.isMobileDevice
      this.isMobileDevice = isMobile()
      
      // 如果从移动端切换到PC端，关闭移动菜单
      if (wasMobile && !this.isMobileDevice) {
        this.mobileMenuVisible = false
      }
      
      console.log(`[App] 设备类型: ${this.isMobileDevice ? '移动端' : 'PC端'}`)
    },
    
    // 切换移动端菜单
    toggleMobileMenu() {
      this.mobileMenuVisible = !this.mobileMenuVisible
      
      // 移动端菜单打开时，禁止页面滚动
      if (this.isMobileDevice) {
        if (this.mobileMenuVisible) {
          document.body.style.overflow = 'hidden'
        } else {
          document.body.style.overflow = ''
        }
      }
    },
    
    // 关闭移动端菜单
    closeMobileMenu() {
      this.mobileMenuVisible = false
      // 恢复页面滚动
      document.body.style.overflow = ''
    },
    
    // 移动端菜单选择处理
    handleMobileMenuSelect() {
      // 选择菜单项后自动关闭菜单
      this.closeMobileMenu()
    }
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family:
    ui-sans-serif,
    system-ui,
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    'PingFang SC',
    'Hiragino Sans GB',
    'Microsoft YaHei',
    'Helvetica Neue',
    Helvetica,
    Arial,
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #1a1a1a;
  height: 100vh;
  overflow: hidden;
}

.app-container {
  height: 100vh;
}

/* 固定顶部样式 — 灰阶极简 */
.app-header {
  background: #ffffff;
  color: #1a1a1a;
  height: 56px !important;
  padding: 0;
  border-bottom: 1px solid #e0e0e0;
  position: relative;
  z-index: 1000;
}

.header-content {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  height: 100%;
  padding: 0 24px;
}

.header-title {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
  color: #1a1a1a;
  letter-spacing: -0.02em;
  margin-left: 8px;
}

/* 主容器 */
.main-container {
  height: calc(100vh - 56px);
  overflow: hidden;
}

/* 左侧边栏 — 浅灰背景 */
.app-aside {
  background-color: #f5f5f5;
  border-right: 1px solid #e0e0e0;
  overflow: hidden;
  position: relative;
  z-index: 999;
  padding: 10px 10px 14px;
  display: flex;
  flex-direction: column;
}

.side-menu {
  flex: 1;
  min-height: 0;
  border-right: none;
  background-color: transparent !important;
  overflow: hidden auto;
  padding-right: 2px;
}

/* 隐藏左侧菜单的滚动条 */
.side-menu::-webkit-scrollbar {
  display: none;
}

.side-menu {
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
}

.app-aside .side-menu .menu-item {
  height: 42px;
  line-height: 42px;
  margin: 2px 0;
  border-radius: 8px;
  color: #1a1a1a !important;
  transition: background-color 0.15s ease, color 0.15s ease;
}

.app-aside .side-menu .menu-item:hover {
  background-color: #ebebeb !important;
  color: #1a1a1a !important;
}

.app-aside .side-menu .menu-item.is-active {
  background-color: #e8e8e8 !important;
  color: #1a1a1a !important;
  font-weight: 600;
}

.app-aside .side-menu .menu-item .el-icon {
  color: #5c5c5c;
}

.app-aside .side-menu .menu-item.is-active .el-icon {
  color: #1a1a1a;
}

.menu-icon {
  margin-right: 10px;
  font-size: 17px;
}

.menu-text {
  font-size: 13px;
  font-weight: 500;
}

/* 可滚动的内容区域 */
.app-main {
  padding: 0;
  background-color: #ffffff;
  overflow: hidden;
}

.content-wrapper {
  height: 100%;
  padding: 28px 32px;
  overflow-y: auto;
  overflow-x: hidden;
  background-color: #ffffff;
}

/* 自定义滚动条 */
.content-wrapper::-webkit-scrollbar {
  width: 6px;
}

.content-wrapper::-webkit-scrollbar-track {
  background: #f1f1f1;
  border-radius: 3px;
}

.content-wrapper::-webkit-scrollbar-thumb {
  background: #c1c1c1;
  border-radius: 3px;
}

.content-wrapper::-webkit-scrollbar-thumb:hover {
  background: #a8a8a8;
}

/* 移动端菜单切换按钮 */
.mobile-menu-toggle {
  color: #1a1a1a !important;
  margin-right: 15px;
  padding: 8px !important;
}

.mobile-menu-toggle:hover {
  background-color: #f0f0f0 !important;
}

/* 移动端折叠菜单面板 */
.mobile-menu-panel {
  background: #f5f5f5;
  border-bottom: 1px solid #e0e0e0;
  box-shadow: none;
  position: relative;
  z-index: 998;
  overflow: hidden;
  animation: slideDown 0.3s ease-out;
  min-height: auto;
  padding-bottom: 12px;
}

@keyframes slideDown {
  from {
    max-height: 0;
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    max-height: 400px;
    opacity: 1;
    transform: translateY(0);
  }
}

.mobile-menu {
  border-bottom: none;
  background: transparent;
  padding: 8px 0;
}

.mobile-menu-item {
  height: 48px;
  line-height: 48px;
  padding: 0 18px !important;
  margin: 4px 12px;
  border-radius: 8px;
  transition: background-color 0.15s ease, color 0.15s ease;
  background: #ffffff;
  border: 1px solid #e0e0e0;
  color: #1a1a1a !important;
}

.mobile-menu-item:hover {
  background: #ebebeb !important;
  color: #1a1a1a !important;
}

.mobile-menu-item.is-active {
  background: #e8e8e8 !important;
  color: #1a1a1a !important;
  border-color: #d0d0d0;
  font-weight: 600;
}

.mobile-menu-item .menu-icon {
  margin-right: 12px;
  font-size: 17px;
  color: #5c5c5c;
}

.mobile-menu-item.is-active .menu-icon {
  color: #1a1a1a;
}

.mobile-menu-item .menu-text {
  font-size: 14px;
  font-weight: 500;
}

/* 移动端菜单遮罩层 */
.mobile-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(26, 26, 26, 0.25);
  z-index: 997;
  transition: opacity 0.3s ease;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .app-aside {
    display: none; /* 移动端隐藏左侧边栏 */
  }
  
  .header-content {
    padding: 0 16px;
    justify-content: center;
  }
  
  .header-title {
    font-size: 18px;
    text-align: center;
    margin-left: 0;
  }
  
  .content-wrapper {
    padding: 16px 10px;
  }
  
  /* 移动端主容器：仅占顶栏下方剩余高度 */
  .main-container {
    height: calc(100vh - 56px);
  }
  
  /* 移动端菜单按钮优化 */
  .mobile-menu-toggle {
    position: absolute;
    left: 16px;
  }
  
  .mobile-menu-toggle .el-icon {
    font-size: 20px;
  }
}

/* 极小屏幕适配 */
@media (max-width: 375px) {
  .header-content {
    padding: 0 12px;
  }
  
  .header-title {
    font-size: 16px;
  }
  
  .mobile-menu-toggle {
    left: 12px;
  }
  
  .content-wrapper {
    padding: 12px 8px;
  }
  
  .mobile-menu-item {
    margin: 6px 12px;
    padding: 0 20px !important;
  }
}

/* Element Plus：去掉菜单默认右边框（避免与 aside 分界线叠成双线） */
#app .el-menu.side-menu,
#app .el-menu.mobile-menu {
  border-right: none !important;
  border-right-width: 0 !important;
  box-shadow: none;
}

/* 变量写法（部分版本的主题用 border-color 绘制） */
#app .app-aside .el-menu.side-menu {
  --el-menu-border-color: transparent;
}

#app .mobile-menu-panel .el-menu.mobile-menu {
  --el-menu-border-color: transparent;
}

/* Element Plus：仅侧边栏内菜单继承灰阶语义 */
.el-menu {
  border-right: none;
}

.app-aside .side-menu.el-menu .el-menu-item {
  padding-left: 14px !important;
}

.app-aside .side-menu.el-menu--vertical:not(.el-menu--collapse):not(.el-menu--popup-container) .el-menu-item {
  padding-left: 14px !important;
}

/* 确保侧栏菜单在窄宽度下不出现横向滚动条 */
.app-aside .el-menu--vertical {
  overflow-x: hidden;
}

/* 内容区域卡片样式 — 细边框、浅阴影 */
.content-wrapper .el-card {
  border-radius: 8px;
  border: 1px solid #e0e0e0;
  box-shadow: none;
  margin-bottom: 16px;
}

.content-wrapper .el-card__header {
  background-color: #fafafa;
  border-bottom: 1px solid #e0e0e0;
  padding: 14px 20px;
}

.content-wrapper .el-card__body {
  padding: 20px;
}
</style>
