import axios from 'axios'

// 创建默认的 axios 实例 (3000端口)
const request = axios.create({
  baseURL: 'http://localhost:3000',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// 创建7001端口的 axios 实例
const request7001 = axios.create({
  baseURL: 'http://localhost:7001',
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// 创建7002端口的 axios 实例 (期货数据更新系统)
const request7002 = axios.create({
  baseURL: 'http://localhost:7002',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// 通用拦截器配置函数
const setupInterceptors = (instance, port) => {
  // 请求拦截器
  instance.interceptors.request.use(
    config => {
      console.log(`发送请求到${port}端口:`, config.url)
      return config
    },
    error => {
      return Promise.reject(error)
    }
  )

  // 响应拦截器
  instance.interceptors.response.use(
    response => {
      const responseData = response.data
      
      // 对于7002端口，直接返回完整的响应数据
      if (port === 7002) {
        return responseData
      }
      
      // 如果有嵌套的data字段，提取内层数据
      if (responseData && responseData.data && typeof responseData.data === 'object') {
        return responseData.data
      }
      
      return responseData
    },
    error => {
      let errorMessage = '请求失败'
      
      if (error.response) {
        errorMessage = `服务器错误: ${error.response.status} - ${error.response.statusText}`
      } else if (error.request) {
        errorMessage = `网络错误: 无法连接到${port}端口服务器`
      } else {
        errorMessage = '请求失败: ' + error.message
      }
      
      const standardError = new Error(errorMessage)
      standardError.originalError = error
      
      return Promise.reject(standardError)
    }
  )
}

// 为所有实例配置拦截器
setupInterceptors(request, 3000)
setupInterceptors(request7001, 7001)
setupInterceptors(request7002, 7002)

// 动态请求方法 - 可以指定不同的端口和超时时间
export const dynamicRequest = (port = 3000, timeout = 10000) => {
  return axios.create({
    baseURL: `http://localhost:${port}`,
    timeout: timeout,
    headers: {
      'Content-Type': 'application/json',
    }
  })
}

// 便捷方法：直接调用不同端口的接口，支持自定义超时时间
export const requestWithPort = async (url, data = {}, method = 'post', port = 3000, timeout = 10000) => {
  const instance = dynamicRequest(port, timeout)
  setupInterceptors(instance, port)
  
  const response = await instance[method](url, data)
  return response
}

// 导出所有实例
export default request
export { request7001, request7002 } 