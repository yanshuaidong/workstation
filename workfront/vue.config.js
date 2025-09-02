const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,

  chainWebpack: config => {
    config.plugin('define').tap(definitions => {
      Object.assign(definitions[0], {
        __VUE_OPTIONS_API__: JSON.stringify(true),
        __VUE_PROD_DEVTOOLS__: JSON.stringify(false),
        __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: JSON.stringify(false)
      })
      return definitions
    })
  },

  devServer: {
    host: '0.0.0.0',
    port: 8080,
    // 代理配置 - 将 /api-a/ 转发到本地7001端口
    proxy: {
      '/api-a': {
        target: 'http://localhost:7001',
        changeOrigin: true,
        pathRewrite: {
          '^/api-a': '/api'  // 将 /api-a 重写为 /api
        }
      }
    },
    headers: { 'Access-Control-Allow-Origin': '*' }
  }
})
