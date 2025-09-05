const { defineConfig } = require('@vue/cli-service')

module.exports = defineConfig({
  transpileDependencies: true,

  // 生产环境优化配置
  configureWebpack: {
    optimization: {
      splitChunks: {
        chunks: 'all',
        cacheGroups: {
          vendor: {
            test: /[\\/]node_modules[\\/]/,
            name: 'vendors',
            chunks: 'all',
          }
        }
      }
    }
  },

  chainWebpack: config => {
    // 定义全局变量
    config.plugin('define').tap(definitions => {
      Object.assign(definitions[0], {
        __VUE_OPTIONS_API__: JSON.stringify(true),
        __VUE_PROD_DEVTOOLS__: JSON.stringify(false),
        __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: JSON.stringify(false)
      })
      return definitions
    })

    // 生产环境优化
    if (process.env.NODE_ENV === 'production') {
      // 移除 console.log
      config.optimization.minimizer('terser').tap(args => {
        args[0].terserOptions.compress.drop_console = true
        return args
      })
      
      // 禁用 source map 以减少构建时间和内存使用
      config.devtool(false)
    }
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
