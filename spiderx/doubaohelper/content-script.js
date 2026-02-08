(function() {
  'use strict';

  console.log('[豆包 Helper] Content Script Loaded');

  // ==================== 监听来自 Background 的消息 ====================
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === 'PING') {
      sendResponse({ success: true, ready: true });
      return false;
    }

    if (request.action === 'EXECUTE_PROMPT') {
      processDoubaoQuestion(request.prompt, request.title, request.task_id)
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
  
  async function processDoubaoQuestion(promptText, title, taskId) {
    const processStartTime = Date.now();
    console.log(`[Content] 🚀 开始处理任务 | ID: ${taskId} | 标题: ${title}`);
    
    // 步骤1: 点击"创建新对话"按钮
    const newChatButton = document.querySelector('div[data-testid="create_conversation_button"]');
    if (newChatButton) {
      console.log('[Content] 点击创建新对话按钮');
      newChatButton.click();
      await new Promise(resolve => setTimeout(resolve, 3000));
    } else {
      console.log('[Content] ⚠️  未找到创建新对话按钮，继续执行');
    }
    
    // 步骤2: 填入问题
    const inputTextarea = document.querySelector('textarea[data-testid="chat_input_input"]');
    
    if (!inputTextarea) {
      throw new Error("未找到输入框 (data-testid='chat_input_input')");
    }
    
    console.log('[Content] 找到输入框，填入问题');
    inputTextarea.value = promptText;
    inputTextarea.dispatchEvent(new Event('input', { bubbles: true }));
    inputTextarea.dispatchEvent(new Event('change', { bubbles: true }));
    
    await new Promise(resolve => setTimeout(resolve, 500));
    
    // 步骤3: 点击发送按钮
    const sendButton = document.querySelector('button[data-testid="chat_input_send_button"]');
    
    if (!sendButton) {
      throw new Error("未找到发送按钮 (data-testid='chat_input_send_button')");
    }
    
    console.log('[Content] 点击发送按钮');
    sendButton.click();
    console.log(`[Content] ✅ 问题已发送，等待AI响应...`);
    
    // 步骤4: 等待并获取结果
    const content = await waitForResponse();
    
    // 步骤5: 发送到后端
    const requestData = { title, content };
    if (taskId) {
      requestData.task_id = taskId;
    }
    
    const response = await fetch('http://localhost:1127/save-result', {
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
  
  // 检查是否存在中断按钮（AI正在生成）
  function isGenerating() {
    const breakButton = document.querySelector('div[data-testid="chat_input_local_break_button"]');
    return breakButton !== null;
  }

  async function waitForResponse() {
    const maxWaitTime = 600000; // 10分钟
    const startTime = Date.now();
    
    console.log(`[Content] 🔍 === 开始等待响应 ===`);
    
    // 等待AI开始生成（中断按钮出现）
    let generationStarted = false;
    while (Date.now() - startTime < maxWaitTime) {
      if (isGenerating()) {
        console.log(`[Content] 🚀 检测到AI开始生成（中断按钮出现）`);
        generationStarted = true;
        break;
      }
      await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    if (!generationStarted) {
      console.log(`[Content] ⚠️ 等待AI生成开始超时，继续检查回答内容...`);
    }
    
    // 等待AI生成结束（中断按钮消失）
    while (Date.now() - startTime < maxWaitTime) {
      const isStillGenerating = isGenerating();
      
      if (!isStillGenerating && generationStarted) {
        console.log(`[Content] ✅ === AI生成完成 ===`);
        console.log(`[Content] ✅ 中断按钮已消失`);
        
        // 额外等待确保DOM完全渲染
        console.log(`[Content] ⏳ 等待3秒确保DOM完全渲染...`);
        await new Promise(resolve => setTimeout(resolve, 3000));
        console.log(`[Content] ⏳ 3秒等待完成，开始提取内容`);
        
        // 获取所有AI回答内容（豆包使用 data-testid="receive_message" 外层和 data-testid="message_text_content" 内层）
        const allReceiveMessages = document.querySelectorAll('div[data-testid="receive_message"]');
        console.log(`[Content] 📊 找到 ${allReceiveMessages.length} 个接收消息容器`);
        
        if (allReceiveMessages.length > 0) {
          // 获取最后一个接收消息容器
          const lastReceiveMessage = allReceiveMessages[allReceiveMessages.length - 1];
          // 在容器内查找所有 message_text_content 元素（可能有多个，第一个是思考，第二个是具体内容）
          const contentElements = lastReceiveMessage.querySelectorAll('div[data-testid="message_text_content"]');
          console.log(`[Content] 📊 找到 ${contentElements.length} 个 message_text_content 元素`);
          
          if (contentElements.length > 0) {
            // 合并所有 message_text_content 的内容
            let allContent = '';
            contentElements.forEach((element, index) => {
              const partContent = extractTextContent(element);
              console.log(`[Content] 📝 提取第 ${index + 1} 个内容长度: ${partContent ? partContent.length : 0} | 前50字符: ${partContent ? partContent.substring(0, 50) : '空'}`);
              if (partContent && partContent.length > 0) {
                if (allContent.length > 0) {
                  allContent += '\n\n'; // 用两个换行分隔不同的 message_text_content
                }
                allContent += partContent;
              }
            });
            
            console.log(`[Content] 📝 合并后总内容长度: ${allContent.length} | 前100字符: ${allContent.substring(0, 100)}`);
            
            if (allContent.length > 0) {
              return allContent;
            }
          } else {
            console.log(`[Content] ⚠️ 在接收消息容器内未找到 message_text_content 元素`);
          }
        }
        
        throw new Error(`未找到AI回答内容 | 接收消息数量: ${allReceiveMessages.length}`);
      }
      
      // 每10秒打印一次等待状态
      const elapsed = Math.round((Date.now() - startTime) / 1000);
      if (elapsed % 10 === 0 && elapsed > 0) {
        console.log(`[Content] ⏳ 等待中... | 已等待: ${elapsed}秒 | AI生成中: ${isStillGenerating}`);
      }
      
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
    
    throw new Error(`等待响应超时 | 已等待: ${Math.round(maxWaitTime/1000)}秒`);
  }

})();
