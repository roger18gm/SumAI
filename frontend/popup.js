// Global variables to store thread information
let currentThreadId = null;
let currentWebsiteUrl = null;

// Initialize when the popup opens
document.addEventListener('DOMContentLoaded', async () => {
    try {
        // Get current tab URL
        const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
        currentWebsiteUrl = tabs[0].url;
        
        // Display loading message
        Reply("Initializing... Please wait while I analyze this website.");
        
        // Create a thread with the current website
        await createOrUpdateThread(currentWebsiteUrl);
        
        // Initialization complete message
        Reply("Ready! What would you like to know about this website?");
        
        // Set up listeners for URL changes
        setupTabListeners();
        
        // Ensure scrolling works properly
        setupScrolling();
    } catch (error) {
        console.error("Initialization error:", error);
        Reply("Sorry, I couldn't connect to the website. Please try again later.");
    }
});

// Set up listeners for tab/URL changes
function setupTabListeners() {
    // Listen for tab updates (URL changes)
    chrome.tabs.onUpdated.addListener(async (tabId, changeInfo, tab) => {
        if (changeInfo.url) {
            // URL has changed
            currentWebsiteUrl = changeInfo.url;
            Reply(`I notice you've navigated to a new page. Let me analyze it...`);
            
            try {
                await createOrUpdateThread(currentWebsiteUrl);
                Reply("I'm ready to answer questions about this new page.");
            } catch (error) {
                console.error("Error updating thread for new URL:", error);
                Reply("I had trouble analyzing this new page. Please try refreshing.");
            }
        }
    });
}

// Set up scrolling for the chat box
function setupScrolling() {
    const chatBox = document.getElementById('chatBox');
    
    // Add custom styling for scroll behavior
    chatBox.style.overflowY = 'auto';
    chatBox.style.maxHeight = 'calc(100% - 80px)'; // Adjust based on your UI
    
    // Ensure we scroll to the bottom on new messages
    const observer = new MutationObserver(() => {
        chatBox.scrollTop = chatBox.scrollHeight;
    });
    
    observer.observe(chatBox, { childList: true });
}

// Create or update thread with current website
async function createOrUpdateThread(websiteUrl) {
    try {
        // Replace with your actual backend API URL
        const backendUrl = "http://127.0.0.1:5000/create_thread";
        
        const response = await fetch(backendUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ website_url: websiteUrl })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Store the thread ID
        currentThreadId = data.thread_id;
        console.log("Thread created/updated:", currentThreadId);
        return data;
    } catch (error) {
        console.error("Error creating/updating thread:", error);
        throw error;
    }
}

// Send message to AI and get streaming response
async function sendMessageToAI(userMessage) {
    try {
        if (!currentThreadId) {
            throw new Error("No active thread. Please reload the extension.");
        }
        
        // Replace with your actual backend API URL - using stream endpoint
        const backendUrl = "http://127.0.0.1:5000/chat_stream";
        
        const response = await fetch(backendUrl, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                thread_id: currentThreadId,
                message: userMessage
            })
        });
        
        if (!response.ok) {
            throw new Error(`API error: ${response.status}`);
        }
        
        return response; // Return the response for streaming
    } catch (error) {
        console.error("Error sending message to AI:", error);
        throw error;
    }
}

// Handle user input submission
document.getElementById('submitBtn').addEventListener('click', () => {
    handleUserInput();
});

// Add event listener for Enter key press
document.getElementById('prompt').addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
        event.preventDefault(); // Prevent default form submission behavior
        handleUserInput();
    }
});

// Process user input and get AI response with streaming
async function handleUserInput() {
    const userInput = document.getElementById('prompt');
    const chatBox = document.getElementById('chatBox');
    const userText = userInput.value.trim();

    if (userText) {
        // Display user message
        const userPrompt = document.createElement('div');
        userPrompt.className = 'flex justify-end';
        userPrompt.innerHTML = `<p class="inline-flex max-w-sm bg-blue-500 text-white p-3 rounded-lg rounded-br-none self-end">${userText}</p>`;
        chatBox.appendChild(userPrompt);
        
        // Clear input field
        userInput.value = '';
        
        // Create AI response container
        const AIReply = document.createElement('div');
        AIReply.className = 'flex justify-start';
        AIReply.innerHTML = `<p id="currentReply" class="inline-flex max-w-sm bg-gray-50 p-3 rounded-lg rounded-bl-none self-start">...</p>`;
        chatBox.appendChild(AIReply);
        
        // Get response element for updating
        const replyElement = AIReply.querySelector('#currentReply');
        
        try {
            // Get streaming response from AI
            const response = await sendMessageToAI(userText);
            
            // Set up streaming with EventSource or ReadableStream
            if (response.body) {
                // Modern streaming with ReadableStream
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let responseText = '';
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const chunk = decoder.decode(value, { stream: true });
                    responseText += chunk;
                    replyElement.textContent = responseText;
                    
                    // Scroll to bottom with each new chunk
                    chatBox.scrollTop = chatBox.scrollHeight;
                }
            } else {
                // Fallback to non-streaming
                const data = await response.json();
                replyElement.textContent = data.response || "No response received";
            }
        } catch (error) {
            replyElement.textContent = "Sorry, I encountered an error. Please try again.";
        }
        
        // Generate a new ID for the reply element (remove the temporary ID)
        replyElement.removeAttribute('id');
        
        // Scroll to bottom of chat
        chatBox.scrollTop = chatBox.scrollHeight;
    }
}

// Display AI message (for non-streaming messages)
function Reply(message) {
    const chatBox = document.getElementById('chatBox');
    const AIReply = document.createElement('div');
    AIReply.className = 'flex justify-start';
    AIReply.innerHTML = `<p class="inline-flex max-w-sm bg-gray-50 p-3 rounded-lg rounded-bl-none self-start">${message}</p>`;
    chatBox.appendChild(AIReply);
    
    // Auto-scroll to latest message
    chatBox.scrollTop = chatBox.scrollHeight;
    
    // Add fade-in animation
    setTimeout(function() {
        AIReply.classList.add('animate-fadeIn');
    }, 100);
}

// Helper function for sleep/delay
function Sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}