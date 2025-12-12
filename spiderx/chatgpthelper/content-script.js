(function() {
  'use strict';

  console.log('[ChatGPT Helper] Content Script Loaded');

  // ==================== 监听来自 Background 的消息 ====================
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('[Content] 收到消息:', request.action);

    // PING 消息用于检查 Content Script 是否已加载
    if (request.action === 'PING') {
      sendResponse({ success: true, ready: true });
      return false;
    }

    if (request.action === 'EXECUTE_PROMPT') {
      processChatGPTQuestion(request.prompt, request.title, request.task_id)
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
  
  async function processChatGPTQuestion(promptText, title, taskId) {
    console.log("[Content] 开始执行 - 标题:", title);
    console.log("[Content] Prompt 长度:", promptText.length);
    console.log("[Content] 任务ID:", taskId);
    
    // 步骤1: 点击"创建新对话"按钮
    console.log("[Content] 步骤1: 发起新对话");
    const newChatButton = document.querySelector('a[data-testid="create-new-chat-button"]');
    
    if (newChatButton) {
      newChatButton.click();
      await new Promise(resolve => setTimeout(resolve, 3000));
    } else {
      console.log("[Content] 未找到新建对话按钮，尝试继续...");
    }
    
    // 步骤2: 填入问题
    console.log("[Content] 步骤2: 填入问题");
    
    // ChatGPT 的输入框有两种形式：
    // 1. ProseMirror 编辑器 (contenteditable div)
    // 2. 隐藏的 textarea
    
    // 尝试方式1: ProseMirror 编辑器
    let inputEditor = document.querySelector('#prompt-textarea[contenteditable="true"]');
    
    if (inputEditor) {
      // 清空并填入内容
      inputEditor.innerHTML = '';
      const pTag = document.createElement('p');
      pTag.textContent = promptText;
      inputEditor.appendChild(pTag);
      inputEditor.dispatchEvent(new Event('input', { bubbles: true }));
      inputEditor.dispatchEvent(new Event('change', { bubbles: true }));
    } else {
      // 尝试方式2: textarea
      const textarea = document.querySelector('textarea#prompt-textarea, textarea[name="prompt-textarea"]');
      
      if (textarea) {
        textarea.value = promptText;
        textarea.dispatchEvent(new Event('input', { bubbles: true }));
        textarea.dispatchEvent(new Event('change', { bubbles: true }));
      } else {
        throw new Error("未找到输入框");
      }
    }
    
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 步骤3: 点击发送
    console.log("[Content] 步骤3: 发送问题");
    
    // ChatGPT 发送按钮选择器
    let sendButton = document.querySelector('button[data-testid="send-button"]');
    
    if (!sendButton) {
      sendButton = document.querySelector('button#composer-submit-button');
    }
    
    if (!sendButton) {
      // 尝试通过 aria-label 查找
      const allButtons = document.querySelectorAll('button');
      sendButton = Array.from(allButtons).find(
        btn => btn.getAttribute('aria-label')?.includes('发送') || 
               btn.getAttribute('aria-label')?.includes('Send')
      );
    }
    
    if (!sendButton) {
      throw new Error("未找到发送按钮");
    }
    
    // 检查按钮是否可用
    if (sendButton.disabled) {
      // 重新触发输入事件
      if (inputEditor) {
        inputEditor.dispatchEvent(new Event('input', { bubbles: true }));
      }
      await new Promise(resolve => setTimeout(resolve, 500));
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
    
    const response = await fetch('http://localhost:1126/save-result', {
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
    
    const maxWaitTime = 180000; // 3分钟
    const globalStartTime = Date.now();
    
    // 记录开始时已有的复制按钮数量
    const initialCopyButtonCount = document.querySelectorAll('button[data-testid="copy-turn-action-button"]').length;
    console.log(`[Content] 初始复制按钮数量: ${initialCopyButtonCount}`);
    
    // 等待新的复制按钮出现（表示 AI 回复完成）
    while (Date.now() - globalStartTime < maxWaitTime) {
      const copyButtons = document.querySelectorAll('button[data-testid="copy-turn-action-button"]');
      
      if (copyButtons.length > initialCopyButtonCount) {
        const elapsedTime = Math.floor((Date.now() - globalStartTime) / 1000);
        console.log(`[Content] ✓ 检测到新复制按钮，AI 回复完成 (${elapsedTime}秒)`);
        
        // 获取最后一条助手消息的内容
        const assistantMessages = document.querySelectorAll('[data-message-author-role="assistant"]');
        
        console.log(`[Content] 找到 ${assistantMessages.length} 条助手消息`);
        
        if (assistantMessages.length > 0) {
          const lastMessage = assistantMessages[assistantMessages.length - 1];
          
          // 调试：打印 DOM 结构
          console.log('[Content] lastMessage DOM:');
          console.log('[Content] - outerHTML:', lastMessage.outerHTML.substring(0, 500));
          console.log('[Content] - innerHTML:', lastMessage.innerHTML.substring(0, 500));
          console.log('[Content] - textContent:', lastMessage.textContent.substring(0, 200));
          
          // 检查页面上是否有 .markdown.prose 元素
          const allMarkdownProse = document.querySelectorAll('.markdown.prose');
          console.log(`[Content] 页面上找到 ${allMarkdownProse.length} 个 .markdown.prose 元素`);
          if (allMarkdownProse.length > 0) {
            const lastMarkdown = allMarkdownProse[allMarkdownProse.length - 1];
            console.log('[Content] 最后一个 .markdown.prose 内容:', lastMarkdown.textContent.substring(0, 200));
          }
          
          // 优先从内部容器提取内容
          let contentElement = null;
          let content = '';
          
          // 尝试多种可能的内容容器选择器（通用选择器）
          const contentSelectors = [
            '[class*="markdown"]',
            '[class*="prose"]',
            '.text-base',
            '.whitespace-pre-wrap',
            'article'
          ];
          
          for (const selector of contentSelectors) {
            contentElement = lastMessage.querySelector(selector);
            if (contentElement) {
              console.log(`[Content] ✓ 找到内容容器: ${selector}`);
              console.log('[Content] - 容器 innerHTML:', contentElement.innerHTML.substring(0, 500));
              content = extractTextContent(contentElement);
              if (content.length > 0) {
                console.log(`[Content] ✓ 从 ${selector} 提取到内容 (${content.length}字符)`);
                break;
              }
            }
          }
          
          // 如果上面的选择器都没找到，尝试直接获取所有文本
          if (!content || content.length === 0) {
            console.log('[Content] 尝试直接从 lastMessage 提取文本...');
            content = extractTextContent(lastMessage);
          }
          
          // 如果还是没有，尝试 textContent
          if (!content || content.length === 0) {
            console.log('[Content] 尝试使用 textContent...');
            content = lastMessage.textContent?.trim() || '';
          }
          
          // 尝试：查找所有 p 标签
          if (!content || content.length === 0) {
            console.log('[Content] 尝试查找所有 p 标签...');
            const paragraphs = lastMessage.querySelectorAll('p');
            content = Array.from(paragraphs).map(p => p.textContent).join('\n').trim();
          }
          
          // 兜底：直接从页面获取最后一个 .markdown.prose
          if (!content || content.length === 0) {
            console.log('[Content] 兜底：直接从页面获取 .markdown.prose...');
            const allMarkdownProse = document.querySelectorAll('.markdown.prose');
            if (allMarkdownProse.length > 0) {
              const lastMarkdown = allMarkdownProse[allMarkdownProse.length - 1];
              content = extractTextContent(lastMarkdown);
              console.log(`[Content] 从页面 .markdown.prose 提取到 ${content.length} 字符`);
            }
          }
          
          console.log(`[Content] ✓ 内容提取完成 (${content.length}字符)`);
          console.log('[Content] 提取的内容预览:', content.substring(0, 200));
          return content;
        }
        
        throw new Error("未找到助手消息内容");
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    throw new Error("等待响应超时");
  }

})();

