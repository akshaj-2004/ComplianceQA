from langchain_google_genai import ChatGoogleGenerativeAI
from ..config import settings

llm = ChatGoogleGenerativeAI(
        model = 'gemini-2.0-flash',
        api_key = settings.GEMINI_API_KEY,
        temperature = 0        
    )