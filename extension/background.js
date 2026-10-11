// 搜绎 - 后台 Service Worker
// 职责：管理右键菜单、处理工具栏图标点击、广播选中文字到侧边栏

const STORAGE_KEYS = {
  LAST_SELECTED: "souyi.lastSelected",
};

// 安装时创建右键菜单
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "souyi-generate",
    title: "用搜绎生成检索方案",
    contexts: ["selection"],
  });
});

// 右键菜单点击 → 把选中文字存到 storage 并打开侧边栏
chrome.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === "souyi-generate" && info.selectionText) {
    await chrome.storage.local.set({
      [STORAGE_KEYS.LAST_SELECTED]: {
        text: info.selectionText,
        tabTitle: tab?.title || "",
        tabUrl: tab?.url || "",
        timestamp: Date.now(),
      },
    });
    // 打开侧边栏（Manifest V3）
    if (chrome.sidePanel && chrome.sidePanel.open) {
      await chrome.sidePanel.open({ tabId: tab.id });
    }
  }
});

// 监听 content script 的选中文字消息（备选通道）
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg?.type === "souyi.selection" && msg.text) {
    chrome.storage.local.set({
      [STORAGE_KEYS.LAST_SELECTED]: {
        text: msg.text,
        tabTitle: sender.tab?.title || "",
        tabUrl: sender.tab?.url || "",
        timestamp: Date.now(),
      },
    });
    sendResponse({ ok: true });
    return false;
  }
  return false;
});

// 工具栏图标点击 → 打开侧边栏
chrome.action.onClicked.addListener(async (tab) => {
  if (chrome.sidePanel && chrome.sidePanel.open) {
    await chrome.sidePanel.open({ tabId: tab.id });
  }
});
