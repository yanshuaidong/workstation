(function() {
  'use strict';

  console.log('[Gemini Helper] Content Script Loaded');

  // ==================== 监听来自 Background 的消息 ====================
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('[Content] 收到消息:', request.action);

    // PING 消息用于检查 Content Script 是否已加载
    if (request.action === 'PING') {
      sendResponse({ success: true, ready: true });
      return false;
    }

    if (request.action === 'EXECUTE_PROMPT') {
      processGeminiQuestion(request.prompt, request.title, request.task_id)
        .then(result => {
            console.log('[Content] 执行成功:', result);
            sendResponse({ success: true, result });
        })
        .catch(error => {
            console.error('[Content] 执行失败:', error);
            sendResponse({ success: false, error: error.message });
        });
      return true; // 保持消息通道开启以进行异步响应
    }
  });

  // ==================== 核心处理逻辑 ====================
  
  async function processGeminiQuestion(promptText, title, taskId) {
    console.log("[Content] 开始执行 - 标题:", title);
    console.log("[Content] Prompt 长度:", promptText.length);
    console.log("[Content] 任务ID:", taskId);
    
    // 步骤1: 点击"发起新对话"
    console.log("[Content] 步骤1: 发起新对话");
    const allButtons = document.querySelectorAll('button');
    const newChatButton = Array.from(allButtons).find(
      btn => btn.getAttribute('aria-label') === '发起新对话'
    );
    
    if (newChatButton) {
      newChatButton.click();
      await new Promise(resolve => setTimeout(resolve, 3000));
    }
    
    // 步骤2: 填入问题
    console.log("[Content] 步骤2: 填入问题");
    const inputEditor = document.querySelector('.ql-editor');
    
    if (!inputEditor) {
      throw new Error("未找到输入框");
    }
    
    inputEditor.textContent = '';
    const pTag = document.createElement('p');
    pTag.textContent = promptText;
    inputEditor.appendChild(pTag);
    inputEditor.dispatchEvent(new Event('input', { bubbles: true }));
    
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 步骤3: 点击发送
    console.log("[Content] 步骤3: 发送问题");
    const sendButton = document.querySelector('button[aria-label="发送"]');
    
    if (!sendButton) {
      throw new Error("未找到发送按钮");
    }
    
    if (sendButton.getAttribute('aria-disabled') === 'true' || sendButton.disabled) {
      inputEditor.dispatchEvent(new Event('input', { bubbles: true }));
      await new Promise(resolve => setTimeout(resolve, 200));
    }
    
    sendButton.click();
    console.log("[Content] 问题已发送");
    
    // 步骤4: 等待并获取结果
    const content = await waitForResponse();
    
    // 步骤5: 发送到后端
    console.log("[Content] 步骤4: 保存到后端");
    const requestData = { 
      title: title, 
      content: content 
    };
    
    // 如果有任务ID，一起发送
    if (taskId) {
      requestData.task_id = taskId;
    }
    
    const response = await fetch('http://localhost:1124/save-result', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestData)
    });
    
    if (!response.ok) {
      throw new Error(`后端保存失败: HTTP ${response.status}`);
    }
    
    const result = await response.json();
    console.log("[Content] ✓ 保存成功:", result);
    
    return {
      success: true,
      title: title,
      contentLength: content.length,
      newsId: result.news_id
    };
  }

  // ==================== 辅助函数 ====================

  // 提取文本内容
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
  
  // 等待响应
  async function waitForResponse() {
    console.log("[Content] 等待 AI 响应...");
    
    const maxWaitTime = 480000; // 8分钟
    const globalStartTime = Date.now();
    
    // 阶段1: 等待响应开始
    while (Date.now() - globalStartTime < maxWaitTime) {
      const messageActions = document.querySelector('message-actions');
      
      if (messageActions) {
        const elapsedTime = Math.floor((Date.now() - globalStartTime) / 1000);
        console.log(`[Content] ✓ 响应开始 (${elapsedTime}秒)`);
        break;
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    if (Date.now() - globalStartTime >= maxWaitTime) {
      throw new Error("等待响应超时");
    }
    
    // 阶段2: 等待内容稳定
    console.log("[Content] 等待内容加载完成...");
    
    let lastContentLength = 0;
    let stableCount = 0;
    
    while (Date.now() - globalStartTime < maxWaitTime) {
      const messageContents = document.querySelectorAll('message-content');
      
      if (messageContents.length > 0) {
        const lastMessageContent = messageContents[messageContents.length - 1];
        const currentText = extractTextContent(lastMessageContent);
        const currentLength = currentText.length;
        
        if (currentLength >= 10) {
          const lengthDiff = Math.abs(currentLength - lastContentLength);
          
          if (lengthDiff <= 5) {
            stableCount++;
            
            if (stableCount >= 2) {
              const elapsedTime = Math.floor((Date.now() - globalStartTime) / 1000);
              console.log(`[Content] ✓ 内容加载完成 (${elapsedTime}秒, ${currentLength}字符)`);
              return currentText;
            }
          } else {
            stableCount = 0;
          }
          
          lastContentLength = currentLength;
        }
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    throw new Error("等待内容加载超时");
  }

})();

