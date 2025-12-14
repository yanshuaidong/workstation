(function() {
  'use strict';

  console.log('[ChatGPT Helper] Content Script Loaded');

  // ==================== 监听来自 Background 的消息 ====================
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'PING') {
      sendResponse({ success: true, ready: true });
      return false;
    }

    if (request.action === 'EXECUTE_PROMPT') {
      processChatGPTQuestion(request.prompt, request.title, request.task_id)
        .then(result => {
            sendResponse({ success: true, result });
        })
        .catch(error => {
            console.error('[Content] 执行失败:', error);
            sendResponse({ success: false, error: error.message });
        });
      return true;
    }
  });

  // ==================== 核心处理逻辑 ====================
  
  async function processChatGPTQuestion(promptText, title, taskId) {
    const processStartTime = Date.now();
    console.log(`[Content] 🚀 开始处理任务 | ID: ${taskId} | 标题: ${title}`);
    
    // 步骤1: 点击"创建新对话"按钮
    const newChatButton = document.querySelector('a[data-testid="create-new-chat-button"]');
    if (newChatButton) {
      newChatButton.click();
      await new Promise(resolve => setTimeout(resolve, 3000));
    }
    
    // 步骤2: 填入问题
    let inputEditor = document.querySelector('#prompt-textarea[contenteditable="true"]');
    
    if (inputEditor) {
      inputEditor.innerHTML = '';
      const pTag = document.createElement('p');
      pTag.textContent = promptText;
      inputEditor.appendChild(pTag);
      inputEditor.dispatchEvent(new Event('input', { bubbles: true }));
    } else {
      const textarea = document.querySelector('textarea#prompt-textarea, textarea[name="prompt-textarea"]');
      if (textarea) {
        textarea.value = promptText;
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
      } else {
        throw new Error("未找到输入框");
      }
    }
    
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 步骤3: 点击发送
    let sendButton = document.querySelector('button[data-testid="send-button"]') ||
                     document.querySelector('button#composer-submit-button');
    
    if (!sendButton) {
      const allButtons = document.querySelectorAll('button');
      sendButton = Array.from(allButtons).find(
        btn => btn.getAttribute('aria-label')?.includes('发送') || 
               btn.getAttribute('aria-label')?.includes('Send')
      );
    }
    
    if (!sendButton) {
      throw new Error("未找到发送按钮");
    }
    
    if (sendButton.disabled && inputEditor) {
      inputEditor.dispatchEvent(new Event('input', { bubbles: true }));
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    sendButton.click();
    console.log(`[Content] ✅ 问题已发送，等待AI响应...`);
    
    // 步骤4: 等待并获取结果
    const content = await waitForResponse();
    
    // 步骤5: 发送到后端
    const requestData = { title, content };
    if (taskId) {
      requestData.task_id = taskId;
    }
    
    const response = await fetch('http://localhost:1126/save-result', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData)
    });
    
    if (!response.ok) {
      throw new Error(`后端保存失败: HTTP ${response.status}`);
    }
    
    const result = await response.json();
    const totalDuration = Math.round((Date.now() - processStartTime) / 1000);
    
    console.log(`[Content] ✅ 任务完成 | ID: ${taskId} | 耗时: ${totalDuration}秒 | news_id: ${result.news_id}`);
    
    return {
      success: true,
      title: title,
      contentLength: content.length,
      newsId: result.news_id
    };
  }

  // ==================== 辅助函数 ====================

  function extractTextContent(element) {
    let text = '';
    
    function traverse(node) {
      if (node.nodeType === Node.TEXT_NODE) {
        text += node.textContent;
      } else if (node.nodeType === Node.ELEMENT_NODE) {
        if (['BR', 'P', 'DIV', 'LI'].includes(node.tagName)) {
          if (text && !text.endsWith('\n')) {
            text += '\n';
          }
        }
        
        for (const child of node.childNodes) {
          traverse(child);
        }
        
        if (['P', 'DIV', 'LI', 'H1', 'H2', 'H3', 'H4', 'H5', 'H6'].includes(node.tagName)) {
          if (text && !text.endsWith('\n')) {
            text += '\n';
          }
        }
      }
    }
    
    traverse(element);
    return text.replace(/\n{3,}/g, '\n\n').trim();
  }
  
  function isElementVisible(element) {
    if (!element) return false;
    
    const rect = element.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return false;
    
    const style = window.getComputedStyle(element);
    if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
      return false;
    }
    
    if (element.offsetParent === null && style.position !== 'fixed') {
      return false;
    }
    
    return true;
  }
  
  function getVisibleCopyButtonCount() {
    const copyButtons = document.querySelectorAll('button[data-testid="copy-turn-action-button"]');
    let visibleCount = 0;
    copyButtons.forEach(btn => {
      if (isElementVisible(btn)) visibleCount++;
    });
    return visibleCount;
  }
  
  async function waitForResponse() {
    const maxWaitTime = 300000; // 5分钟
    const startTime = Date.now();
    const initialVisibleCount = getVisibleCopyButtonCount();
    console.log(`[Content] 🔍 开始等待响应 | 初始复制按钮数量: ${initialVisibleCount}`);
    
    while (Date.now() - startTime < maxWaitTime) {
      const currentVisibleCount = getVisibleCopyButtonCount();
      
      if (currentVisibleCount > initialVisibleCount) {
        console.log(`[Content] ✅ 检测到复制按钮数量增加: ${initialVisibleCount} → ${currentVisibleCount}`);
        
        // 额外等待确保DOM完全渲染
        console.log(`[Content] ⏳ 等待3秒确保DOM完全渲染...`);
        await new Promise(resolve => setTimeout(resolve, 3000));
        console.log(`[Content] ⏳ 3秒等待完成，开始提取内容`);
        
        // 获取最后一条助手消息
        const allMessages = document.querySelectorAll('[data-message-author-role="assistant"]');
        const validMessages = Array.from(allMessages).filter(msg => {
          const messageId = msg.getAttribute('data-message-id') || '';
          return !messageId.includes('placeholder');
        });
        
        console.log(`[Content] 📊 消息统计 | 全部助手消息: ${allMessages.length} | 有效消息: ${validMessages.length}`);
        
        if (validMessages.length > 0) {
          const lastMessage = validMessages[validMessages.length - 1];
          const messageId = lastMessage.getAttribute('data-message-id') || '无';
          console.log(`[Content] 📝 最后一条消息 | message-id: ${messageId}`);
          
          const contentElement = lastMessage.querySelector('[class*="markdown"]');
          console.log(`[Content] 📝 markdown元素: ${contentElement ? '找到' : '未找到'}`);
          
          const content = contentElement ? extractTextContent(contentElement) : extractTextContent(lastMessage);
          console.log(`[Content] 📝 提取内容长度: ${content ? content.length : 0} | 前100字符: ${content ? content.substring(0, 100) : '空'}`);
          
          if (content && content.length > 0) {
            return content;
          }
        }
        
        // 更详细的错误信息
        const errorDetails = {
          allMessagesCount: allMessages.length,
          validMessagesCount: validMessages.length,
          copyButtonCount: currentVisibleCount
        };
        throw new Error(`未找到助手消息内容 | 详情: ${JSON.stringify(errorDetails)}`);
      }
      
      // 每10秒打印一次等待状态
      const elapsed = Math.round((Date.now() - startTime) / 1000);
      if (elapsed % 10 === 0 && elapsed > 0) {
        console.log(`[Content] ⏳ 等待中... | 已等待: ${elapsed}秒 | 当前复制按钮: ${currentVisibleCount} | 初始: ${initialVisibleCount}`);
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    throw new Error(`等待响应超时 | 已等待: ${Math.round(maxWaitTime/1000)}秒 | 最终复制按钮数量: ${getVisibleCopyButtonCount()} | 初始: ${initialVisibleCount}`);
  }

})();
