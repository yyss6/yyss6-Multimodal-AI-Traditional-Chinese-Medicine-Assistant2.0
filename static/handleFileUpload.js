// 文件上传处理函数
function handleFileUpload(event) {
    const fileInput = event.target;
    const files = fileInput.files;
    
    if (files.length === 0) return;
    
    const file = files[0];
    const fileSize = file.size / 1024 / 1024; // 转换为MB
    
    // 检查文件大小
    if (fileSize > 16) {
        alert('文件过大，请上传小于16MB的文件');
        fileInput.value = '';
        return;
    }
    
    // 显示加载指示器
    const chatBox = document.getElementById('chat-box');
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'message system-message';
    loadingMsg.textContent = '正在处理文件...';
    chatBox.appendChild(loadingMsg);
    
    const formData = new FormData();
    formData.append('file', file);
    
    // 创建文件预览
    const filePreviewContainer = document.getElementById('file-preview-container');
    if (!filePreviewContainer.classList.contains('active')) {
        filePreviewContainer.classList.add('active');
    }
    
    const filePreview = document.createElement('div');
    filePreview.className = 'file-preview';
    filePreview.innerHTML = `
        <div class="file-info">
            <span class="file-name">${file.name}</span>
            <span class="file-size">(${fileSize.toFixed(2)} MB)</span>
            <button class="remove-file-btn" onclick="this.parentNode.parentNode.remove()">×</button>
        </div>
        <div class="file-content-preview">正在处理...</div>
    `;
    
    filePreviewContainer.appendChild(filePreview);
    
    // 发送文件到服务器
    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`上传失败: ${response.statusText}`);
        }
        return response.json();
    })
    .then(data => {
        // 移除加载消息
        loadingMsg.remove();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // 存储文件信息
        filePreview.dataset.fileUrl = data.file_url;
        filePreview.dataset.fileType = data.type;
        filePreview.dataset.fileName = file.name;
        filePreview.dataset.content = data.content || '';
        
        const contentPreview = filePreview.querySelector('.file-content-preview');
        
        // 根据文件类型处理预览
        if (data.type === 'image') {
            // 图片预览
            contentPreview.innerHTML = `<img src="${data.file_url}" alt="${file.name}" class="image-preview">`;
            
            // 存储base64数据
            if (data.base64) {
                filePreview.dataset.base64 = data.base64;
            }
            
            // 显示OCR结果
            if (data.content) {
                const ocrPreview = document.createElement('div');
                ocrPreview.className = 'ocr-preview';
                
                // 检查是否包含EasyOCR识别结果
                if (data.content.includes('EasyOCR识别文字：') || data.content.includes('图片中识别的文字：')) {
                    // 格式化OCR结果，突出显示识别的文字
                    const formattedContent = data.content
                        .replace(/EasyOCR识别文字：\n/g, '<strong class="ocr-title">EasyOCR识别文字：</strong><br>')
                        .replace(/图片中识别的文字：\n/g, '<strong class="ocr-title">图片中识别的文字：</strong><br>')
                        .replace(/图像内容描述：\n/g, '<strong class="ocr-title">图像内容描述：</strong><br>')
                        .replace(/\n/g, '<br>');
                    
                    ocrPreview.innerHTML = `
                        <div class="ocr-header">图像识别结果：</div>
                        <div class="ocr-content">${formattedContent}</div>
                    `;
                } else {
                    ocrPreview.innerHTML = `
                        <div class="ocr-header">图像识别结果：</div>
                        <div class="ocr-content">${data.content}</div>
                    `;
                }
                contentPreview.appendChild(ocrPreview);
            }
        } else if (data.type === 'audio') {
            // 音频预览
            contentPreview.innerHTML = `
                <audio controls>
                    <source src="${data.file_url}" type="audio/mpeg">
                    您的浏览器不支持音频播放
                </audio>
                <div class="audio-transcript">
                    <div class="transcript-header">音频转写：</div>
                    <div class="transcript-content">${data.content || '无法转写音频内容'}</div>
                </div>
            `;
        } else {
            // 文本文件预览
            const previewText = data.content ? data.content.substring(0, 500) + (data.content.length > 500 ? '...' : '') : '无法预览文件内容';
            contentPreview.innerHTML = `<pre class="text-preview">${previewText}</pre>`;
        }
        
        // 添加成功消息
        const successMsg = document.createElement('div');
        successMsg.className = 'message system-message';
        successMsg.textContent = `文件 ${file.name} 上传成功`;
        chatBox.appendChild(successMsg);
        
        // 3秒后移除成功消息
        setTimeout(() => {
            successMsg.remove();
        }, 3000);
    })
    .catch(error => {
        // 移除加载消息
        loadingMsg.remove();
        
        // 显示错误消息
        const errorMsg = document.createElement('div');
        errorMsg.className = 'message system-message error';
        errorMsg.textContent = `文件上传失败: ${error.message}`;
        chatBox.appendChild(errorMsg);
        
        // 移除文件预览
        filePreview.remove();
        
        // 如果没有其他预览，隐藏容器
        if (filePreviewContainer.children.length === 0) {
            filePreviewContainer.classList.remove('active');
        }
        
        // 3秒后移除错误消息
        setTimeout(() => {
            errorMsg.remove();
        }, 5000);
    });
    
    // 清空文件输入，允许再次选择相同文件
    fileInput.value = '';
}

// 显示通知函数
function showNotification(message, type = 'info') {
    const chatBox = document.getElementById('chat-box');
    const notification = document.createElement('div');
    notification.className = `message system-message ${type}`;
    notification.textContent = message;
    chatBox.appendChild(notification);
    
    // 3秒后移除通知
    setTimeout(() => {
        notification.remove();
    }, 3000);
}

// 显示加载指示器
function showLoadingIndicator(message) {
    const chatBox = document.getElementById('chat-box');
    const loadingMsg = document.createElement('div');
    loadingMsg.className = 'message system-message loading';
    loadingMsg.id = 'loading-indicator';
    loadingMsg.textContent = message || '正在处理...';
    chatBox.appendChild(loadingMsg);
    scrollToBottom();
}

// 隐藏加载指示器
function hideLoadingIndicator() {
    const loadingIndicator = document.getElementById('loading-indicator');
    if (loadingIndicator) {
        loadingIndicator.remove();
    }
}

// 显示打字指示器
function showTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.style.display = 'flex';
    }
    scrollToBottom();
}

// 隐藏打字指示器
function hideTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.style.display = 'none';
    }
}

// 滚动到底部
function scrollToBottom() {
    const chatBox = document.getElementById('chat-box');
    chatBox.scrollTop = chatBox.scrollHeight;
}

// 自动调整文本区域高度
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = (textarea.scrollHeight) + 'px';
}

// 高亮代码
function highlightCode() {
    document.querySelectorAll('pre code').forEach((block) => {
        if (window.hljs) {
            hljs.highlightBlock(block);
        }
    });
} 