import axios from 'axios'

// 创建默认的 axios 实例，使用相对路径，通过Vue代理转发
const request = axios.create({
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    console.log('发送请求:', config.url)
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  response => {
    const responseData = response.data
    
    // 直接返回完整的响应数据
    return responseData
  },
  error => {
    let errorMessage = '请求失败'
    
    if (error.response) {
      errorMessage = `服务器错误: ${error.response.status} - ${error.response.statusText}`
    } else if (error.request) {
      errorMessage = `网络错误: 无法连接到服务器`
    } else {
      errorMessage = '请求失败: ' + error.message
    }
    
    const standardError = new Error(errorMessage)
    standardError.originalError = error
    
    return Promise.reject(standardError)
  }
)

// 导出默认实例
export default request 