// 搜绎 - 内容脚本
// 职责：监听页面文本选中事件，把选中文本发给 background.js

(function () {
  // 选中文本变化时，发送到 background
  let lastSent = "";
  document.addEventListener("mouseup", () => {
    setTimeout(() => {
      const sel = window.getSelection();
      const text = sel ? sel.toString().trim() : "";
      if (text && text !== lastSent && text.length >= 2) {
        lastSent = text;
        chrome.runtime.sendMessage({ type: "souyi.selection", text });
      }
    }, 50);
  });

  document.addEventListener("keyup", (e) => {
    if (e.shiftKey || e.key === "Shift") {
      setTimeout(() => {
        const sel = window.getSelection();
        const text = sel ? sel.toString().trim() : "";
        if (text && text !== lastSent && text.length >= 2) {
          lastSent = text;
          chrome.runtime.sendMessage({ type: "souyi.selection", text });
        }
      }, 50);
    }
  });
})();
