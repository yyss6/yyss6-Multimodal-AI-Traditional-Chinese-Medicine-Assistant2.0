/**
 * 中医传承视频播放器
 * 为视频播放页面提供增强的交互体验
 */

document.addEventListener('DOMContentLoaded', function() {
    // 获取视频元素和容器
    const videoContainer = document.querySelector('.video-container');
    const video = document.querySelector('.video-container video');
    
    if (!video || !videoContainer) return;
    
    // 创建加载状态指示器
    if (!document.querySelector('.video-loading-overlay')) {
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'video-loading-overlay';
        loadingOverlay.innerHTML = `
            <div class="spinner-border" role="status">
                <span class="visually-hidden">加载中...</span>
            </div>
            <div class="loading-text">视频加载中，请稍候...</div>
        `;
        videoContainer.appendChild(loadingOverlay);
    }
    
    // 设置加载超时检查
    const loadingTimeout = setTimeout(function() {
        const loadingOverlay = document.querySelector('.video-loading-overlay');
        if (loadingOverlay && loadingOverlay.style.display !== 'none') {
            loadingOverlay.querySelector('.loading-text').innerHTML = '视频加载较慢，请检查网络连接...';
        }
    }, 5000);
    
    // 视频元数据加载完成
    video.addEventListener('loadedmetadata', function() {
        clearTimeout(loadingTimeout);
        const loadingOverlay = document.querySelector('.video-loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.style.opacity = '0';
            setTimeout(() => {
                loadingOverlay.style.display = 'none';
            }, 300);
        }
        
        console.log('视频元数据已加载', {
            duration: video.duration.toFixed(2) + '秒',
            width: video.videoWidth + 'px',
            height: video.videoHeight + 'px'
        });
        
        // 显示视频已准备好的提示
        showNotification('视频准备就绪，可以开始播放', 'info');
    });
    
    // 视频加载失败处理
    video.addEventListener('error', function() {
        clearTimeout(loadingTimeout);
        const loadingOverlay = document.querySelector('.video-loading-overlay');
        if (loadingOverlay) {
            loadingOverlay.innerHTML = `
                <div class="text-danger" style="text-align: center;">
                    <i class="bi bi-exclamation-triangle-fill" style="font-size: 2rem;"></i>
                    <div style="margin-top: 15px;">视频加载失败，请稍后再试</div>
                    <button id="retry-load" class="btn btn-outline-light btn-sm mt-3">
                        <i class="bi bi-arrow-clockwise me-1"></i>重试
                    </button>
                </div>
            `;
            loadingOverlay.style.opacity = '1';
            loadingOverlay.style.display = 'flex';
            
            // 添加重试按钮事件
            const retryButton = document.getElementById('retry-load');
            if (retryButton) {
                retryButton.addEventListener('click', function() {
                    // 重新加载视频
                    const currentSrc = video.src;
                    video.src = '';
                    
                    // 恢复加载状态
                    loadingOverlay.innerHTML = `
                        <div class="spinner-border" role="status">
                            <span class="visually-hidden">加载中...</span>
                        </div>
                        <div class="loading-text">正在重新加载视频，请稍候...</div>
                    `;
                    
                    // 短暂延迟后重新加载
                    setTimeout(() => {
                        video.src = currentSrc;
                        video.load();
                    }, 500);
                });
            }
        }
        console.error('视频加载失败', video.error);
    });
    
    // 视频开始播放
    let playEventSent = false;
    video.addEventListener('play', function() {
        if (!playEventSent) {
            playEventSent = true;
            
            // 发送视频播放统计数据 - 这里可以添加AJAX请求
            const videoId = new URLSearchParams(window.location.search).get('video_id');
            if (videoId) {
                console.log('发送视频播放统计', { videoId });
                
                // 使用Fetch API发送播放记录
                fetch('/api/video/view', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ video_id: videoId })
                })
                .then(response => {
                    if (!response.ok) {
                        throw new Error('网络响应不正常');
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('播放记录已发送', data);
                })
                .catch(error => {
                    console.error('发送播放记录失败', error);
                });
            }
        }
    });
    
    // 监听视频进度
    video.addEventListener('timeupdate', function() {
        // 记录播放进度，可以用于断点续播
        const currentTime = video.currentTime;
        const duration = video.duration;
        const percent = (currentTime / duration * 100).toFixed(2);
        
        // 每30秒保存一次进度到本地存储
        if (Math.floor(currentTime) % 30 === 0 && currentTime > 0) {
            const videoId = new URLSearchParams(window.location.search).get('video_id');
            if (videoId) {
                localStorage.setItem(`video_progress_${videoId}`, currentTime);
                console.log('保存播放进度', { videoId, currentTime, percent: percent + '%' });
            }
        }
    });
    
    // 检查并恢复上次播放进度
    function checkSavedProgress() {
        const videoId = new URLSearchParams(window.location.search).get('video_id');
        if (!videoId) return;
        
        const savedTime = localStorage.getItem(`video_progress_${videoId}`);
        if (savedTime && video.duration > 0) {
            // 只有当保存的进度小于视频总时长的95%时才恢复
            if (parseFloat(savedTime) < video.duration * 0.95) {
                video.currentTime = parseFloat(savedTime);
                console.log('恢复上次播放进度', { time: savedTime + '秒' });
                
                // 显示恢复播放提示
                showNotification('已恢复上次观看进度');
            }
        }
    }
    
    // 视频可以播放时检查进度
    video.addEventListener('canplay', checkSavedProgress);
    
    // 监听缓冲状态
    video.addEventListener('waiting', function() {
        document.querySelector('.buffering-indicator').style.display = 'block';
    });
    
    video.addEventListener('playing', function() {
        document.querySelector('.buffering-indicator').style.display = 'none';
    });
    
    // 显示通知提示
    function showNotification(message, type = 'success') {
        const existingNotification = document.querySelector('.video-notification');
        if (existingNotification) {
            existingNotification.remove();
        }
        
        const notification = document.createElement('div');
        notification.className = `video-notification ${type}`;
        notification.textContent = message;
        
        videoContainer.appendChild(notification);
        
        // 显示通知
        setTimeout(() => {
            notification.style.display = 'block';
            notification.style.opacity = '1';
            
            // 2秒后自动消失
            setTimeout(() => {
                notification.style.opacity = '0';
                setTimeout(() => {
                    notification.remove();
                }, 500);
            }, 2000);
        }, 100);
    }
    
    // 添加键盘快捷键支持
    document.addEventListener('keydown', function(e) {
        // 只有当视频元素处于焦点或容器处于焦点时才响应
        if (document.activeElement === video || 
            document.activeElement === videoContainer ||
            document.activeElement === document.body) {
            
            switch(e.key) {
                case ' ':  // 空格键 - 播放/暂停
                    e.preventDefault();
                    if (video.paused) {
                        video.play();
                    } else {
                        video.pause();
                    }
                    break;
                
                case 'f':  // F键 - 全屏
                    e.preventDefault();
                    toggleFullScreen();
                    break;
                
                case 'ArrowLeft':  // 左箭头 - 后退5秒
                    e.preventDefault();
                    video.currentTime = Math.max(0, video.currentTime - 5);
                    showNotification('后退 5 秒');
                    break;
                
                case 'ArrowRight':  // 右箭头 - 前进5秒
                    e.preventDefault();
                    video.currentTime = Math.min(video.duration, video.currentTime + 5);
                    showNotification('前进 5 秒');
                    break;
                
                case 'ArrowUp':  // 上箭头 - 增加音量
                    e.preventDefault();
                    video.volume = Math.min(1, video.volume + 0.1);
                    showNotification('音量: ' + Math.round(video.volume * 100) + '%');
                    break;
                
                case 'ArrowDown':  // 下箭头 - 减小音量
                    e.preventDefault();
                    video.volume = Math.max(0, video.volume - 0.1);
                    showNotification('音量: ' + Math.round(video.volume * 100) + '%');
                    break;
                
                case 'm':  // M键 - 静音/取消静音
                    e.preventDefault();
                    video.muted = !video.muted;
                    showNotification(video.muted ? '已静音' : '已取消静音');
                    break;
            }
        }
    });
    
    // 全屏切换功能
    function toggleFullScreen() {
        if (!document.fullscreenElement) {
            if (videoContainer.requestFullscreen) {
                videoContainer.requestFullscreen();
            } else if (videoContainer.webkitRequestFullscreen) {
                videoContainer.webkitRequestFullscreen();
            } else if (videoContainer.msRequestFullscreen) {
                videoContainer.msRequestFullscreen();
            }
            showNotification('进入全屏模式');
        } else {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
            showNotification('退出全屏模式');
        }
    }
    
    // 添加双击全屏功能
    videoContainer.addEventListener('dblclick', function() {
        toggleFullScreen();
    });
    
    // 视频结束处理
    video.addEventListener('ended', function() {
        showNotification('视频播放完成', 'info');
        
        // 自动播放下一个视频（如果有相关视频）
        const relatedVideos = document.querySelectorAll('.related-video-card a');
        if (relatedVideos && relatedVideos.length > 0) {
            // 在视频播放结束5秒后，如果用户没有交互，自动播放第一个相关视频
            const autoplayTimer = setTimeout(() => {
                window.location.href = relatedVideos[0].href;
            }, 5000);
            
            // 如果用户与页面交互，取消自动播放
            document.addEventListener('click', function cancelAutoplay() {
                clearTimeout(autoplayTimer);
                document.removeEventListener('click', cancelAutoplay);
            });
            
            showNotification('5秒后将播放下一个视频...', 'info');
        }
    });
    
    // 分享功能
    setupSharingButtons();
});

// 设置分享按钮功能
function setupSharingButtons() {
    // 复制链接
    const shareLink = document.querySelector('.share-link');
    if (shareLink) {
        shareLink.addEventListener('click', function(e) {
            e.preventDefault();
            const url = window.location.href;
            
            navigator.clipboard.writeText(url).then(
                function() {
                    alert('链接已复制到剪贴板！');
                },
                function() {
                    // 剪贴板API失败时使用传统方法
                    const textArea = document.createElement('textarea');
                    textArea.value = url;
                    textArea.style.position = 'fixed';
                    textArea.style.opacity = '0';
                    document.body.appendChild(textArea);
                    textArea.focus();
                    textArea.select();
                    
                    try {
                        document.execCommand('copy');
                        alert('链接已复制到剪贴板！');
                    } catch (err) {
                        alert('无法复制链接：' + err);
                    }
                    
                    document.body.removeChild(textArea);
                }
            );
        });
    }
    
    // 微信分享
    const shareWechat = document.querySelector('.share-wechat');
    if (shareWechat) {
        shareWechat.addEventListener('click', function(e) {
            e.preventDefault();
            // 生成二维码或提示用户扫描
            alert('请打开微信扫一扫，扫描二维码进行分享');
            // 这里可以添加生成二维码的代码
        });
    }
    
    // 微博分享
    const shareWeibo = document.querySelector('.share-weibo');
    if (shareWeibo) {
        shareWeibo.addEventListener('click', function(e) {
            e.preventDefault();
            const url = encodeURIComponent(window.location.href);
            const title = encodeURIComponent(document.title);
            const shareUrl = `https://service.weibo.com/share/share.php?url=${url}&title=${title}`;
            window.open(shareUrl, '_blank', 'width=700,height=500');
        });
    }
} 