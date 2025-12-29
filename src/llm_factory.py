import os
from dotenv import load_dotenv

try:
    from langchain_openai import ChatOpenAI
except ImportError:
    ChatOpenAI = None

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

load_dotenv()

def get_chat_model():
    """
    환경 변수(LLM_PROVIDER)에 따라 적절한 LangChain ChatModel 객체를 반환합니다.
    """
    provider = os.getenv("LLM_PROVIDER", "openai").lower()  # 기본값 openai
    model_name = os.getenv("LLM_MODEL", "gpt-4o")
    temp = float(os.getenv("LLM_TEMPERATURE", "0"))

    print(f"🔌 [System] LLM 연결 시도: Provider='{provider}', Model='{model_name}'")

    if provider == "openai":
        if not ChatOpenAI: raise ImportError("langchain-openai 패키지가 필요합니다.")
        return ChatOpenAI(
            model_name=model_name,
            temperature=temp
        )

    elif provider == "google":
        if not ChatGoogleGenerativeAI: raise ImportError("langchain-google-genai 패키지가 필요합니다.")
        return ChatGoogleGenerativeAI(
            model=model_name,
            temperature=temp,
            convert_system_message_to_human=True
        )

    # (추가 확장 가능: Anthropic, Ollama 등)
    
    else:
        raise ValueError(f"지원하지 않는 LLM_PROVIDER입니다: {provider}")