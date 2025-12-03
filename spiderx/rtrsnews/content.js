/**
 * Content Script - ISOLATED World（扩展前端层）
 * 职责：
 * 1. DOM 操作和数据提取
 * 2. 页面状态监测
 * 3. 用户交互反馈（可选UI）
 */

// ==================== 数据提取模块 ====================

/**
 * 提取文章内容的核心函数
 */
function extractArticleContent() {
  try {
    // 查找 ArticleBody 容器
    const articleBody = document.querySelector('[data-testid="ArticleBody"]');
    
    if (!articleBody) {
      return {
        success: false,
        error: '未找到 ArticleBody 元素，请确保在路透社文章页面'
      };
    }
    
    // 查找所有 paragraph 元素
    const paragraphElements = articleBody.querySelectorAll('[data-testid^="paragraph-"]');
    
    if (paragraphElements.length === 0) {
      return {
        success: false,
        error: '未找到任何段落元素，页面可能尚未完全加载'
      };
    }
    
    // 提取段落文本
    const paragraphs = [];
    const details = [];
    
    paragraphElements.forEach((element, index) => {
      const text = element.textContent.trim();
      if (text) {
        paragraphs.push(text);
        details.push({
          index: index + 1,
          testId: element.getAttribute('data-testid'),
          text: text,
          length: text.length
        });
      }
    });
    
    console.log(`✓ 成功提取 ${paragraphs.length} 个段落`);
    
    return {
      success: true,
      data: {
        paragraphs: paragraphs,
        count: paragraphs.length,
        details: details,
        totalChars: paragraphs.join('').length
      }
    };
  } catch (error) {
    console.error('✗ 提取内容时出错:', error);
    return {
      success: false,
      error: error.message || '提取失败'
    };
  }
}

/**
 * 检查页面是否是有效的文章页面
 */
function checkPageValidity() {
  const articleBody = document.querySelector('[data-testid="ArticleBody"]');
  return {
    isValid: !!articleBody,
    hasContent: articleBody ? articleBody.querySelectorAll('[data-testid^="paragraph-"]').length > 0 : false
  };
}

// ==================== 消息处理模块 ====================

/**
 * 监听来自 background 的消息
 */
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  console.log('Content Script 收到消息:', request.action);
  
  switch (request.action) {
    case 'doExtractContent':
      // 执行内容提取
      const result = extractArticleContent();
      sendResponse(result);
      
      // 显示反馈UI（可选）
      if (result.success) {
        showSuccessFeedback(result.data.count);
      } else {
        showErrorFeedback(result.error);
      }
      break;
      
    case 'checkValidity':
      // 检查页面有效性
      const validity = checkPageValidity();
      sendResponse({ success: true, ...validity });
      break;
      
    default:
      sendResponse({ success: false, error: '未知操作' });
  }
  
  return true; // 异步响应
});

// ==================== UI 反馈模块（可选）====================

/**
 * 显示成功反馈
 */
function showSuccessFeedback(count) {
  const toast = createToast(`✓ 已提取 ${count} 个段落`, 'success');
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 2000);
}

/**
 * 显示错误反馈
 */
function showErrorFeedback(message) {
  const toast = createToast(`✗ ${message}`, 'error');
  document.body.appendChild(toast);
  
  setTimeout(() => {
    toast.style.opacity = '0';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

/**
 * 创建提示框元素
 */
function createToast(message, type) {
  const toast = document.createElement('div');
  toast.className = 'reuters-scraper-toast';
  toast.textContent = message;
  
  // 样式
  Object.assign(toast.style, {
    position: 'fixed',
    top: '20px',
    right: '20px',
    padding: '12px 20px',
    borderRadius: '6px',
    backgroundColor: type === 'success' ? '#4CAF50' : '#f44336',
    color: 'white',
    fontSize: '14px',
    fontFamily: 'Arial, sans-serif',
    boxShadow: '0 4px 12px rgba(0,0,0,0.2)',
    zIndex: '999999',
    transition: 'opacity 0.3s ease',
    opacity: '1'
  });
  
  return toast;
}

// ==================== 初始化 ====================

console.log('Reuters News Scraper Content Script 已加载');

// 页面加载完成后检查有效性
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', () => {
    const validity = checkPageValidity();
    console.log('页面有效性检查:', validity);
  });
} else {
  const validity = checkPageValidity();
  console.log('页面有效性检查:', validity);
}

