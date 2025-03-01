# Test the integration
import os
import logging
import asyncio
from typing import Dict, List, Callable
from uuid import uuid4
from dotenv import load_dotenv
from stream_handler import StreamingCallbackHandler
from langchain_openai import ChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
from web_crawler import scrape_and_crawl_website  
from open_ai_modules import ChromeExtensionAssistant

if __name__ == "__main__":
    import asyncio

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Create an instance of the assistant
    assistant = ChromeExtensionAssistant()

    # Sample websites for testing
    websites = [
        "https://heychriss.com/",
        "https://www.anthropic.com/",
        "https://docs.anthropic.com/",
    ]

    async def test_assistant():
        print("\n🚀 Testing the Chrome extension assistant with multiple websites...")

        # Initialize with the first website
        result = await assistant.create_or_update_thread(websites[0])
        if "error" in result:
            print("❌ Error:", result["error"])
            return

        thread_id = result["thread_id"]
        print(f"✅ Created thread: {thread_id} for {websites[0]}\n")

        # Function to handle streaming tokens
        def handle_token(token: str) -> None:
            print(token, end="", flush=True)
        
        # Chat with the assistant on the first website
        print(f"\n💬 Now chatting about {websites[0]}")
        user_input = input("\nYou: ")
        print("Assistant: ", end="", flush=True)
        assistant.chat_stream(thread_id, user_input, handle_token)
        
        # Navigate to the second website (using the same thread)
        print(f"\n\n🌐 Navigating to {websites[1]}...")
        result = await assistant.create_or_update_thread(websites[1])
        if "error" in result:
            print("❌ Error:", result["error"])
            return
            
        print(f"✅ Updated thread with new website content\n")
        
        # Chat with the assistant on the second website
        print(f"\n💬 Now chatting about {websites[1]}")
        user_input = input("\nYou: ")
        print("Assistant: ", end="", flush=True)
        assistant.chat_stream(thread_id, user_input, handle_token)
        
        # Navigate to the third website (using the same thread)
        print(f"\n\n🌐 Navigating to {websites[2]}...")
        result = await assistant.create_or_update_thread(websites[2])
        if "error" in result:
            print("❌ Error:", result["error"])
            return
            
        print(f"✅ Updated thread with new website content\n")
        
        # Chat with the assistant on the third website
        print(f"\n💬 Now chatting about {websites[2]}")
        user_input = input("\nYou: ")
        print("Assistant: ", end="", flush=True)
        assistant.chat_stream(thread_id, user_input, handle_token)
        
        print("\n\n✨ Testing complete!")

    asyncio.run(test_assistant())