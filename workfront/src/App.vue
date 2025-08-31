<template>
  <div id="app">
    <el-container class="app-container">
      <!-- 固定顶部 -->
      <el-header class="app-header">
        <div class="header-content">
          <h1 class="header-title">量化分析平台</h1>
          <div class="header-actions">
            <el-button link icon="Setting" size="small">设置</el-button>
            <el-button link icon="User" size="small">用户</el-button>
          </div>
        </div>
      </el-header>
      
      <el-container class="main-container">
        <!-- 固定左侧菜单 -->
        <el-aside width="250px" class="app-aside">
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
            <el-menu-item index="/technical-analysis" class="menu-item">
              <el-icon class="menu-icon"><TrendCharts /></el-icon>
              <span class="menu-text">技术面分析</span>
            </el-menu-item>
            <el-menu-item index="/position-structure" class="menu-item">
              <el-icon class="menu-icon"><DataBoard /></el-icon>
              <span class="menu-text">资金面分析</span>
            </el-menu-item>
            <el-menu-item index="/prompt-formatter" class="menu-item">
              <el-icon class="menu-icon"><Edit /></el-icon>
              <span class="menu-text">提示词格式化</span>
            </el-menu-item>
            <el-menu-item index="/futures-update" class="menu-item">
              <el-icon class="menu-icon"><Refresh /></el-icon>
              <span class="menu-text">期货数据更新</span>
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
  </div>
</template>

<script>
import { DataBoard, TrendCharts, ChatDotRound, Edit } from '@element-plus/icons-vue'
import { markRaw } from 'vue'

export default {
  name: 'App',
  data() {
    return {
      DataBoard: markRaw(DataBoard),
      TrendCharts: markRaw(TrendCharts),
      ChatDotRound: markRaw(ChatDotRound),
      Edit: markRaw(Edit)
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
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 24px;
}

.header-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: white;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.header-actions .el-button {
  color: white;
  font-size: 14px;
}

.header-actions .el-button:hover {
  color: #f0f0f0;
  background-color: rgba(255, 255, 255, 0.1);
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

/* 响应式设计 */
@media (max-width: 768px) {
  .app-aside {
    width: 200px !important;
  }
  
  .header-content {
    padding: 0 16px;
  }
  
  .header-title {
    font-size: 18px;
  }
  
  .content-wrapper {
    padding: 16px;
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
