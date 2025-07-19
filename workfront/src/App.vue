<template>
  <div id="app">
    <el-container>
      <el-header>
        <h1>API数据获取示例应用</h1>
      </el-header>
      <el-main>
        <!-- 使用新的API数据获取组件 -->
        <ApiDataFetcher />
      </el-main>
      <el-footer>
        <p>&copy; 2024 - 使用 Vue 3 + Element Plus 构建</p>
      </el-footer>
    </el-container>
  </div>
</template>

<script>
import ApiDataFetcher from './components/ApiDataFetcher.vue'

export default {
  name: 'App',
  components: {
    ApiDataFetcher
  }
}
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  color: #2c3e50;
  min-height: 100vh;
}

.el-header {
  background-color: #409EFF;
  color: white;
  text-align: center;
  line-height: 60px;
  padding: 0;
}

.el-header h1 {
  margin: 0;
  font-size: 24px;
}

.el-main {
  padding: 20px;
  min-height: calc(100vh - 120px);
}

.el-footer {
  background-color: #f5f7fa;
  color: #606266;
  text-align: center;
  line-height: 60px;
  padding: 0;
}

.el-footer p {
  margin: 0;
}
</style>
