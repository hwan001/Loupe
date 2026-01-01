import os

# [Helper] 텍스트 파일 로더 함수
def load_prompt_file(filename):
    """파일을 읽어서 문자열로 반환"""
    try:
        # 파일이 없으면 빈 문자열 반환 방지용 에러 처리
        if not os.path.exists(filename):
            print(f"  경고: 프롬프트 파일 '{filename}'이 없습니다.")
            return ""
            
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read().strip()
            
    except Exception as e:
        print(f"  프롬프트 로드 오류 ({filename}): {e}")
        return ""

