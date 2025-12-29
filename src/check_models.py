import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    print("❌ .env 파일에 GOOGLE_API_KEY가 없습니다.")
else:
    genai.configure(api_key=api_key)
    print("🔍 사용 가능한 Gemini 모델 목록:")
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                print(f" - {m.name}")
    except Exception as e:
        print(f"❌ 목록 조회 실패: {e}")