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

    async def create_thread(self, website_url: str):
        """
        Create a new conversation thread with scraped website content.
        """
        thread_id = self._generate_thread_id()

        # Scrape website and extract content
        print(f"🔍 Scraping website: {website_url}...")
        scrape_result = scrape_and_crawl_website(website_url)

        print("✅ Website scraped successfully!")

        # Create system prompt and conversation chain
        system_prompt = self._create_system_prompt(website_url, scrape_result)
        self.threads[thread_id] = self._create_conversation_chain(system_prompt)

        return {"thread_id": thread_id}

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

# Test the integration
if __name__ == "__main__":
    import asyncio

    # Configure logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    # Create an instance of the assistant
    assistant = ChromeExtensionAssistant()

    # Sample website for testing
    sample_website_url = "https://heychriss.com/"

    async def test_assistant():
        print("\n🚀 Creating a conversation thread with scraped website content...")

        # Scrape website and create a thread
        result = await assistant.create_thread(sample_website_url)
        if "error" in result:
            print("❌ Error:", result["error"])
            return

        thread_id = result["thread_id"]
        print(f"✅ Created thread: {thread_id} for {sample_website_url}\n")

        while True:
            user_question = input("\n🧑 You: ")

            if user_question.lower() in ["exit", "quit"]:
                print("👋 Exiting chat...")
                break

            response = assistant.chat(thread_id, user_question)
            print(f"🤖 Assistant: {response}")

    asyncio.run(test_assistant())
