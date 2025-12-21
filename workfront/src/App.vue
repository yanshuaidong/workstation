<template>
  <div id="app">
    <el-container class="app-container">
      <!-- 固定顶部 -->
      <el-header class="app-header">
        <div class="header-content">
          <!-- 移动端菜单切换按钮 -->
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
            :default-active="$route.path"
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
          </el-menu>
        </div>
      </el-collapse-transition>
      
      <el-container class="main-container">
        <!-- PC端固定左侧菜单 -->
        <el-aside 
          v-if="!isMobileDevice" 
          width="250px" 
          class="app-aside"
        >
          <el-menu
            :default-active="$route.path"
            router
            class="side-menu"
            background-color="#001529"
            text-color="#fff"
            active-text-color="#1890ff"
          >
            <el-menu-item index="/news-analysis" class="menu-item">
              <el-icon class="menu-icon"><ChatDotRound /></el-icon>
              <span class="menu-text">消息面分析</span>
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
              <span class="menu-text">期货K线图</span>
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
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  height: 100vh;
  overflow: hidden;
}

.app-container {
  height: 100vh;
}

/* 固定顶部样式 */
.app-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  height: 60px !important;
  padding: 0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
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
  font-size: 20px;
  font-weight: 600;
  color: white;
  margin-left: 8px;
}

/* 主容器 */
.main-container {
  height: calc(100vh - 60px);
  overflow: hidden;
}

/* 固定左侧菜单 */
.app-aside {
  background-color: #001529;
  border-right: 1px solid #e8e8e8;
  overflow: hidden;
  position: relative;
  z-index: 999;
}

.side-menu {
  height: 100%;
  border-right: none;
  background-color: #001529;
  overflow: hidden;
}

/* 隐藏左侧菜单的滚动条 */
.side-menu::-webkit-scrollbar {
  display: none;
}

.side-menu {
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
}

.menu-item {
  height: 50px;
  line-height: 50px;
  margin: 4px 0;
  border-radius: 0;
  transition: all 0.3s ease;
}

.menu-item:hover {
  background-color: #1890ff !important;
  color: white !important;
}

.menu-item.is-active {
  background-color: #1890ff !important;
  color: white !important;
  border-right: 3px solid #52c41a;
  position: relative;
}

.menu-item.is-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background-color: #52c41a;
}

.menu-icon {
  margin-right: 12px;
  font-size: 16px;
}

.menu-text {
  font-size: 14px;
  font-weight: 500;
}

/* 可滚动的内容区域 */
.app-main {
  padding: 0;
  background-color: #f0f2f5;
  overflow: hidden;
}

.content-wrapper {
  height: 100%;
  padding: 24px;
  overflow-y: auto;
  overflow-x: hidden;
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
  color: white !important;
  margin-right: 15px;
  padding: 8px !important;
}

.mobile-menu-toggle:hover {
  background-color: rgba(255, 255, 255, 0.1) !important;
}

/* 移动端折叠菜单面板 */
.mobile-menu-panel {
  background: linear-gradient(135deg, #f8f9ff 0%, #ffffff 100%);
  border-bottom: 1px solid #e8e8e8;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  position: relative;
  z-index: 998;
  overflow: hidden;
  animation: slideDown 0.3s ease-out;
  backdrop-filter: blur(10px);
  min-height: auto;
  padding-bottom: 16px;
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
  height: 56px;
  line-height: 56px;
  padding: 0 24px !important;
  margin: 8px 16px;
  border-radius: 12px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(24, 144, 255, 0.1);
  backdrop-filter: blur(8px);
}

.mobile-menu-item:hover {
  background: linear-gradient(135deg, #e6f7ff 0%, #f0f9ff 100%) !important;
  color: #1890ff !important;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(24, 144, 255, 0.2);
  border-color: rgba(24, 144, 255, 0.3);
}

.mobile-menu-item.is-active {
  background: linear-gradient(135deg, #1890ff 0%, #40a9ff 100%) !important;
  color: white !important;
  border: none;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.4);
  transform: translateY(-1px);
}

.mobile-menu-item .menu-icon {
  margin-right: 16px;
  font-size: 18px;
  transition: transform 0.3s ease;
}

.mobile-menu-item:hover .menu-icon {
  transform: scale(1.1);
}

.mobile-menu-item.is-active .menu-icon {
  color: white;
}

.mobile-menu-item .menu-text {
  font-size: 15px;
  font-weight: 500;
  letter-spacing: 0.5px;
}

/* 移动端菜单遮罩层 */
.mobile-menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.3);
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
  
  /* 移动端主容器调整 */
  .main-container {
    height: calc(100vh - 200px);
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

/* Element Plus 组件样式优化 */
.el-menu {
  border-right: none;
  overflow: hidden;
}

.el-menu-item {
  padding-left: 24px !important;
}

.el-menu-item:hover {
  background-color: #1890ff !important;
}

.el-menu-item.is-active {
  background-color: #1890ff !important;
}

/* 确保菜单容器不会产生滚动条 */
.el-menu--vertical,
.el-menu--horizontal {
  overflow: hidden;
}

/* 添加一些动画效果 */
.menu-item {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.menu-item:hover {
  transform: translateX(4px);
}

/* 内容区域卡片样式 */
.content-wrapper .el-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  margin-bottom: 16px;
}

.content-wrapper .el-card__header {
  background-color: #fafafa;
  border-bottom: 1px solid #f0f0f0;
  padding: 16px 20px;
}

.content-wrapper .el-card__body {
  padding: 20px;
}
</style>
