import axios from 'axios'

// 创建 axios 实例
const request = axios.create({
  baseURL: 'http://localhost:3000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
})

// 请求拦截器
request.interceptors.request.use(
  config => {
    // 可以在这里添加认证 token 等
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
    // 检查响应结构
    const responseData = response.data
    
    // 如果有嵌套的data字段，提取内层数据
    if (responseData && responseData.data && typeof responseData.data === 'object') {
      // 返回内层的业务数据 {code: 0, msg: '', data: Array(85)}
      return responseData.data
    }
    
    // 否则直接返回响应数据
    return responseData
  },
  error => {
    // 统一处理错误响应
    let errorMessage = '请求失败'
    
    if (error.response) {
      // 服务器响应了错误状态码
      errorMessage = `服务器错误: ${error.response.status} - ${error.response.statusText}`
    } else if (error.request) {
      // 请求发出但没有收到响应
      errorMessage = '网络错误: 无法连接到服务器'
    } else {
      // 其他错误
      errorMessage = '请求失败: ' + error.message
    }
    
    // 创建标准化的错误对象
    const standardError = new Error(errorMessage)
    standardError.originalError = error
    
    return Promise.reject(standardError)
  }
)

// 导出 axios 实例
export default request 