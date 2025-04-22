// highlight-custom.js
function highlightCode() {
  document.querySelectorAll('pre code').forEach((block) => {
    if (hljs) {
      hljs.highlightBlock(block);
    }
  });
}

// 初始化时执行一次高亮
document.addEventListener('DOMContentLoaded', function() {
  if (typeof hljs !== 'undefined') {
    highlightCode();
  } else {
    console.warn('Highlight.js not loaded');
  }
}); 