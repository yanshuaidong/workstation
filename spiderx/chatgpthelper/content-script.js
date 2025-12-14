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
  
  function isElementVisible(element, debug = false) {
    if (!element) {
      if (debug) console.log('[Visibility] 元素为null');
      return false;
    }
    
    const rect = element.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) {
      if (debug) console.log('[Visibility] 元素尺寸为0', { width: rect.width, height: rect.height });
      return false;
    }
    
    // 检查元素自身
    const style = window.getComputedStyle(element);
    if (style.display === 'none') {
      if (debug) console.log('[Visibility] 元素 display: none');
      return false;
    }
    if (style.visibility === 'hidden') {
      if (debug) console.log('[Visibility] 元素 visibility: hidden');
      return false;
    }
    if (style.opacity === '0') {
      if (debug) console.log('[Visibility] 元素 opacity: 0');
      return false;
    }
    
    // 检查父元素链的 opacity (关键修复：父元素 opacity 为 0 会导致子元素不可见)
    let current = element.parentElement;
    let depth = 0;
    while (current && current !== document.body && depth < 10) {
      const parentStyle = window.getComputedStyle(current);
      if (parentStyle.opacity === '0') {
        if (debug) console.log(`[Visibility] 父元素 opacity: 0`, { tag: current.tagName, depth });
        return false;
      }
      if (parentStyle.display === 'none') {
        if (debug) console.log(`[Visibility] 父元素 display: none`, { tag: current.tagName, depth });
        return false;
      }
      if (parentStyle.visibility === 'hidden') {
        if (debug) console.log(`[Visibility] 父元素 visibility: hidden`, { tag: current.tagName, depth });
        return false;
      }
      current = current.parentElement;
      depth++;
    }
    
    if (element.offsetParent === null && style.position !== 'fixed') {
      if (debug) console.log('[Visibility] 元素 offsetParent 为 null 且非 fixed 定位');
      return false;
    }
    
    if (debug) {
      console.log('[Visibility] 元素判定为可见', {
        rect: { top: rect.top, left: rect.left, width: rect.width, height: rect.height },
        display: style.display,
        visibility: style.visibility,
        opacity: style.opacity,
        position: style.position,
        offsetParent: element.offsetParent ? element.offsetParent.tagName : null
      });
    }
    
    return true;
  }
  
  function getVisibleCopyButtonCount(enableDebug = false) {
    const copyButtons = document.querySelectorAll('button[data-testid="copy-turn-action-button"]');
    let visibleCount = 0;
    
    if (enableDebug) {
      console.log(`[CopyButton] 找到 ${copyButtons.length} 个复制按钮`);
    }
    
    copyButtons.forEach((btn, index) => {
      const isVisible = isElementVisible(btn, enableDebug);
      if (isVisible) visibleCount++;
      
      if (enableDebug) {
        // 打印父元素链的可见性信息
        let parentInfo = [];
        let current = btn.parentElement;
        let depth = 0;
        while (current && current !== document.body && depth < 5) {
          const pStyle = window.getComputedStyle(current);
          parentInfo.push({
            tag: current.tagName,
            class: current.className?.substring?.(0, 50) || '',
            display: pStyle.display,
            visibility: pStyle.visibility,
            opacity: pStyle.opacity
          });
          current = current.parentElement;
          depth++;
        }
        
        console.log(`[CopyButton] 按钮${index}:`, {
          isVisible,
          buttonHTML: btn.outerHTML.substring(0, 100),
          parentChain: parentInfo
        });
      }
    });
    
    return visibleCount;
  }
  
  // 检查是否存在停止按钮（流式传输中）
  function isStreamingInProgress() {
    const stopButton = document.querySelector('button[data-testid="stop-button"]');
    return stopButton !== null;
  }

  async function waitForResponse() {
    const maxWaitTime = 600000; // 10分钟
    const startTime = Date.now();
    
    // 初始化时打印当前状态
    console.log(`[Content] 🔍 === 开始等待响应 ===`);
    const initialVisibleCount = getVisibleCopyButtonCount(true);
    console.log(`[Content] 🔍 初始复制按钮数量: ${initialVisibleCount}`);
    console.log(`[Content] 🔍 当前是否在流式传输中: ${isStreamingInProgress()}`);
    
    // 等待流式传输开始（停止按钮出现）
    let streamingStarted = false;
    while (Date.now() - startTime < maxWaitTime) {
      if (isStreamingInProgress()) {
        console.log(`[Content] 🚀 检测到流式传输开始（停止按钮出现）`);
        streamingStarted = true;
        break;
      }
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    if (!streamingStarted) {
      console.log(`[Content] ⚠️ 等待流式传输开始超时，继续检查复制按钮...`);
    }
    
    // 等待流式传输结束（停止按钮消失）+ 复制按钮数量增加
    while (Date.now() - startTime < maxWaitTime) {
      const isStreaming = isStreamingInProgress();
      const currentVisibleCount = getVisibleCopyButtonCount(false);
      
      // 流式传输结束（停止按钮消失）且复制按钮数量增加
      if (!isStreaming && currentVisibleCount > initialVisibleCount) {
        console.log(`[Content] ✅ === 流式传输完成 ===`);
        console.log(`[Content] ✅ 停止按钮已消失，复制按钮数量: ${initialVisibleCount} → ${currentVisibleCount}`);
        // 打印详细信息
        getVisibleCopyButtonCount(true);
        
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
        console.log(`[Content] ⏳ 等待中... | 已等待: ${elapsed}秒 | 流式传输中: ${isStreaming} | 复制按钮: ${currentVisibleCount}(初始${initialVisibleCount})`);
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    throw new Error(`等待响应超时 | 已等待: ${Math.round(maxWaitTime/1000)}秒 | 最终复制按钮数量: ${getVisibleCopyButtonCount()} | 初始: ${initialVisibleCount}`);
  }

})();
