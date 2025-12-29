import csv
import random

# 설정: 생성할 인원 수
TOTAL_COUNT = 20

# 데이터 풀 (Data Pool)
FIRST_NAMES = ["철수", "영희", "민수", "서호", "민석", "주영", "도원", "서원", "지원", "현우", "지민", "수진", "우성", "재석", "동엽", "경규", "나래", "세형", "구라", "흥국"]
LAST_NAMES = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신", "권", "황", "안", "송", "류", "홍"]

MAJORS = {
    "SECURITY": ["정보보호학", "컴퓨터공학", "사이버국방", "경찰행정학"],
    "IT": ["컴퓨터공학", "소프트웨어공학", "전자공학", "수학", "통계학"],
    "HR": ["경영학", "심리학", "교육공학", "행정학"],
    "EXECUTIVE": ["경영학(MBA)", "경제학", "법학", "정치외교학"],
    "STAFF": ["문헌정보학", "회계학", "신문방송학", "영문학", "무역학"]
}

CERTS = {
    "SECURITY": ["CISSP", "CISA", "정보보안기사", "CEH", "AWS Security"],
    "IT": ["AWS SA", "CKA", "SQLD", "정보처리기사", "Google Cloud Pro"],
    "HR": ["노무사", "PHR", "경영지도사", "직업상담사"],
    "EXECUTIVE": ["PMP", "CPA", "AICPA", "MBA수료"],
    "STAFF": ["전산회계", "컴퓨터활용능력", "토익 900+", "비서1급"]
}

TEAMS = {
    "SECURITY": ["보안팀", "정보보호팀", "관제센터", "경호팀"],
    "IT": ["IT개발팀", "인프라팀", "데이터분석팀", "AI연구팀"],
    "HR": ["인사팀", "인재개발팀", "급여팀", "노무팀"],
    "EXECUTIVE": ["전략기획실", "비서실", "해외영업팀", "이사회"],
    "STAFF": ["총무팀", "재무팀", "홍보팀", "법무팀"]
}

ROLES = ["사원", "대리", "과장", "차장", "부장", "팀장", "상무", "전무"]

def generate_name():
    return random.choice(LAST_NAMES) + random.choice(FIRST_NAMES)

def create_hr_csv():
    data = []
    
    # 그룹별 할당 비율
    groups = (
        ["SECURITY"] * 20 + 
        ["IT"] * 30 + 
        ["HR"] * 15 + 
        ["EXECUTIVE"] * 10 + 
        ["STAFF"] * 25
    )
    
    # 100명 채우기 (모자르면 랜덤 추가)
    while len(groups) < TOTAL_COUNT:
        groups.append(random.choice(["IT", "STAFF"]))
        
    random.shuffle(groups)

    # 카운터
    counts = {"SECURITY": 0, "IT": 0, "HR": 0, "EXECUTIVE": 0, "STAFF": 0}

    for i in range(TOTAL_COUNT):
        group = groups[i]
        counts[group] += 1
        
        # ID 생성 (예: sec-1001)
        prefix = group.lower()[:3] if group != "SECURITY" else "sec"
        if group == "EXECUTIVE": prefix = "exec"
        user_id = f"{prefix}-{1000 + counts[group]}"
        
        # 기본 정보
        name = generate_name()
        age = random.randint(24, 58)
        gender = random.choice(["남성", "여성"])
        
        # 직급 (나이에 비례하여 대략적으로)
        if age < 28: role = "사원"
        elif age < 33: role = "대리"
        elif age < 40: role = "과장"
        elif age < 47: role = "차장"
        elif age < 52: role = "부장"
        else: role = random.choice(["상무", "전무", "부장"])
        
        if group == "EXECUTIVE" and age > 45: role = random.choice(["상무", "전무", "부사장"])

        # 팀, 전공, 자격증
        team = random.choice(TEAMS[group])
        major = random.choice(MAJORS[group])
        # 자격증은 0~2개 보유
        cert_count = random.choice([0, 1, 1, 2]) 
        my_certs = ", ".join(random.sample(CERTS[group], k=cert_count)) if cert_count > 0 else "없음"

        row = {
            "id": user_id,
            "name": name,
            "age": age,
            "gender": gender,
            "role": role,
            "team": team,
            "company": "태산그룹",
            "group": group,
            "major": major,
            "certifications": my_certs
        }
        data.append(row)

    # 파일 저장
    with open("hr_data.csv", "w", newline="", encoding="utf-8") as f:
        fieldnames = ["id", "name", "age", "gender", "role", "team", "company", "group", "major", "certifications"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
        
    print(f"✅ 'hr_data.csv' 파일이 생성되었습니다. (총 {TOTAL_COUNT}명)")

if __name__ == "__main__":
    create_hr_csv()