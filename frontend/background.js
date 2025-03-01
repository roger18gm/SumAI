// Background script for the extension
let currentTabId = null;
let currentThreadId = null;

// Listen for tab changes
chrome.tabs.onActivated.addListener(async (activeInfo) => {
    currentTabId = activeInfo.tabId;
    // You could save state here
});

// Listen for extension install/update
chrome.runtime.onInstalled.addListener(() => {
    console.log("Extension installed or updated");
});

// Store thread information when created
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "setThreadId") {
        chrome.storage.local.set({ key: value }).then(() => {
            console.log("Value is set");
          });
        currentThreadId = message.threadId;
        console.log("Thread ID stored in background:", currentThreadId);
        sendResponse({success: true});
    }
    
    if (message.action === "getThreadId") {
        chrome.storage.local.get(["key"]).then((result) => {
            console.log("Value is " + result.key);
          });
        sendResponse({threadId: currentThreadId});
    }
    
    // Always return true for async response
    return true;
});