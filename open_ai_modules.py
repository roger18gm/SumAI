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
from web_crawler import scrape_and_crawl_website  # Import the scraper function

class ChromeExtensionAssistant:
    """An AI assistant for a Chrome extension that answers questions about the current website."""

    def __init__(self, model_name: str = "gpt-4o"):
        """Initialize the assistant with default configuration."""
        self.model_name = model_name
        self.threads: Dict[str, ConversationChain] = {}
        self.llm = None
        self.active_thread_id = None  # Track the current active thread

        # Setup the assistant
        self._load_api_key()
        self._initialize_llm()

        logging.info(f"Chrome extension assistant initialized with model: {model_name}")

    def _load_api_key(self) -> None:
        """Load the OpenAI API key from environment variables."""
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY.")
        os.environ["OPENAI_API_KEY"] = api_key

    def _initialize_llm(self) -> None:
        """Initialize the language model."""
        self.llm = ChatOpenAI(
            model_name=self.model_name, 
            temperature=0.7,  
            streaming=True
        )

    def _create_system_prompt(self, website_url: str, website_content: str) -> str:
        """
        Create a system prompt with the website context.
        """
        return f"""You are an AI assistant in a Chrome extension. Your task is to assist users by answering questions about {website_url}. 
The content of this website has been extracted using a web scraper.

IMPORTANT RULES:
- You **must** answer questions **ONLY** using the given context.
- If the user asks you questions that are not related to the website, please answer and be nice, but your focus
is to always answer the questions with the given context
- **DO NOT hallucinate** or generate answers outside of the provided data.
- If the answer is **not found**, state: **"I can only answer based on the extracted website content."**

**Context:**
{website_content}
"""

    def _create_memory(self, system_prompt: str) -> ConversationBufferMemory:
        """Create a conversation memory buffer with the system prompt."""
        memory = ConversationBufferMemory(return_messages=True)
        memory.chat_memory.add_message(SystemMessage(content=system_prompt))
        return memory

    def _create_conversation_chain(self, system_prompt: str) -> ConversationChain:
        """Create a conversation chain."""
        memory = self._create_memory(system_prompt)
        return ConversationChain(llm=self.llm, memory=memory, verbose=False)

    def _generate_thread_id(self) -> str:
        """Generate a unique thread identifier."""
        return str(uuid4())

    async def _update_thread_context(self, thread_id: str, website_url: str) -> Dict:
        """
        Update the context of an existing thread with new website content.
        
        Args:
            thread_id: The ID of the thread to update
            website_url: The URL of the new website to scrape
            
        Returns:
            Dictionary with thread_id or error message
        """
        try:
            # Scrape the new website
            print(f"🔍 Scraping new website: {website_url}...")
            scrape_result = scrape_and_crawl_website(website_url)
            print("✅ Website scraped successfully!")
            
            # Create a new system prompt with the updated website content
            system_prompt = self._create_system_prompt(website_url, scrape_result)
            
            # Create a new conversation chain with the updated system prompt
            self.threads[thread_id] = self._create_conversation_chain(system_prompt)
            
            return {"thread_id": thread_id}
        except Exception as e:
            return {"error": f"Failed to update thread context: {str(e)}"}

    async def create_or_update_thread(self, website_url: str) -> Dict:
        """
        Create a new thread or update the existing active thread with new website content.
        
        Args:
            website_url: The URL of the website to scrape
            
        Returns:
            Dictionary with thread_id or error message
        """
        try:
            # If there's an active thread, update it with the new website content
            if self.active_thread_id and self.active_thread_id in self.threads:
                print(f"📝 Updating existing thread {self.active_thread_id} with new website: {website_url}")
                return await self._update_thread_context(self.active_thread_id, website_url)
            
            # Otherwise, create a new thread
            thread_id = self._generate_thread_id()
            print(f"🆕 Creating new thread {thread_id} for website: {website_url}")
            
            # Scrape website and extract content
            print(f"🔍 Scraping website: {website_url}...")
            scrape_result = scrape_and_crawl_website(website_url)
            print("✅ Website scraped successfully!")
            
            # Create system prompt and conversation chain
            system_prompt = self._create_system_prompt(website_url, scrape_result)
            self.threads[thread_id] = self._create_conversation_chain(system_prompt)
            
            # Set as the active thread
            self.active_thread_id = thread_id
            
            return {"thread_id": thread_id}
        except Exception as e:
            return {"error": f"Failed to create or update thread: {str(e)}"}

    def chat(self, thread_id: str, user_question: str) -> str:
        """Send a question to the LLM."""
        if thread_id not in self.threads:
            return "Error: Thread not found."

        return self.threads[thread_id].predict(input=user_question)

    def chat_stream(self, thread_id: str, user_question: str, stream_callback: Callable[[str], None]) -> str:
        """Stream responses from the AI."""
        if thread_id not in self.threads:
            return "Error: Thread not found."

        streaming_handler = StreamingCallbackHandler(stream_callback)
        chain = self.threads[thread_id]

        full_response = ""
        def collect_tokens(token: str) -> None:
            nonlocal full_response
            full_response += token
            stream_callback(token)

        collector_handler = StreamingCallbackHandler(collect_tokens)
        chain.predict(input=user_question, callbacks=[collector_handler])

        return full_response

    def get_active_thread_id(self) -> str:
        """Get the ID of the active thread."""
        return self.active_thread_id

