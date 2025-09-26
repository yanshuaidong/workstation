/**
 * 设备检测工具
 */

// 移动设备检测
export function isMobile() {
  // 检测用户代理字符串
  const userAgent = navigator.userAgent.toLowerCase()
  
  // 移动设备关键词
  const mobileKeywords = [
    'mobile', 'android', 'iphone', 'ipad', 'ipod', 
    'blackberry', 'windows phone', 'opera mini', 
    'iemobile', 'webos', 'palm'
  ]
  
  // 检查用户代理中是否包含移动设备关键词
  const hasMobileKeyword = mobileKeywords.some(keyword => 
    userAgent.includes(keyword)
  )
  
  // 检查屏幕宽度（移动设备通常屏幕较窄）
  const isNarrowScreen = window.innerWidth <= 768
  
  // 检测触摸设备
  const hasTouchScreen = 'ontouchstart' in window || 
    navigator.maxTouchPoints > 0 || 
    navigator.msMaxTouchPoints > 0
  
  // 综合判断：如果包含移动关键词，或者（屏幕较窄且支持触摸）
  return hasMobileKeyword || (isNarrowScreen && hasTouchScreen)
}

// 平板设备检测
export function isTablet() {
  const userAgent = navigator.userAgent.toLowerCase()
  const tabletKeywords = ['ipad', 'tablet', 'kindle', 'playbook', 'silk']
  
  const hasTabletKeyword = tabletKeywords.some(keyword => 
    userAgent.includes(keyword)
  )
  
  // 检查屏幕尺寸是否在平板范围
  const isTabletSize = window.innerWidth > 768 && window.innerWidth <= 1024
  
  return hasTabletKeyword || isTabletSize
}

// 桌面设备检测
export function isDesktop() {
  return !isMobile() && !isTablet()
}

// 获取设备类型
export function getDeviceType() {
  if (isMobile()) return 'mobile'
  if (isTablet()) return 'tablet'
  return 'desktop'
}

// 监听设备方向或窗口大小变化
export function onDeviceChange(callback) {
  const handleResize = () => {
    callback(getDeviceType())
  }
  
  window.addEventListener('resize', handleResize)
  window.addEventListener('orientationchange', handleResize)
  
  // 返回清理函数
  return () => {
    window.removeEventListener('resize', handleResize)
    window.removeEventListener('orientationchange', handleResize)
  }
}

// 设置viewport meta标签（移动端优化）
export function setMobileViewport() {
  if (isMobile()) {
    let viewport = document.querySelector('meta[name="viewport"]')
    if (!viewport) {
      viewport = document.createElement('meta')
      viewport.name = 'viewport'
      document.head.appendChild(viewport)
    }
    viewport.content = 'width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no'
  }
}

export default {
  isMobile,
  isTablet,
  isDesktop,
  getDeviceType,
  onDeviceChange,
  setMobileViewport
} 