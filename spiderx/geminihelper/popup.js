document.getElementById('runBtn').addEventListener('click', async () => {
  // 1. 获取你在插件窗口输入的文本
  const question = document.getElementById('questionInput').value;

  if (!question) {
    alert("请输入问题！");
    return;
  }

  // 2. 获取当前活动的标签页
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  // 3. 向页面注入脚本
  chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: sendToGemini, // 指定要执行的函数
    args: [question]    // 将你的问题作为参数传给该函数
  });
});

// 这个函数会被注入到 Gemini 页面中执行
function sendToGemini(promptText) {
  // --- 以下是你验证过的安全代码逻辑 ---
  
  const inputEditor = document.querySelector('.ql-editor');

  if (inputEditor) {
    console.log("插件开始运行...");
    
    // 1. 安全地填入内容 (避开 TrustedHTML 限制)
    inputEditor.textContent = ''; 
    const pTag = document.createElement('p');
    pTag.textContent = promptText;
    inputEditor.appendChild(pTag);

    // 2. 模拟输入事件 (激活发送按钮)
    inputEditor.dispatchEvent(new Event('input', { bubbles: true }));

    // 3. 延迟点击发送
    setTimeout(() => {
      const sendButton = document.querySelector('button[aria-label="发送"]');
      
      if (sendButton) {
         // 双重保险：如果按钮还没亮，再触发一次
         if (sendButton.getAttribute('aria-disabled') === 'true' || sendButton.disabled) {
             inputEditor.dispatchEvent(new Event('input', { bubbles: true }));
         }
         sendButton.click();
         console.log("插件已点击发送");
      } else {
         alert("未找到发送按钮，请确认你在 Gemini 界面");
      }
    }, 500);

  } else {
    alert("未找到输入框！请确保你打开的是 Gemini 网页 (gemini.google.com)");
  }
}