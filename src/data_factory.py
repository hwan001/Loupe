import csv
import random
import os

class DataFactory:
    """
    시스템 운영에 필요한 CSV 데이터(HR, Actors, Actions)를 생성하는 팩토리 클래스.
    HR 데이터와 시뮬레이터 배우 데이터의 정합성을 보장합니다.
    """
    
    def __init__(self):
        self.total_count = 100
        self.first_names = ["철수", "영희", "민수", "서호", "민석", "주영", "도원", "서원", "지원", "현우", "지민", "수진", "우성", "재석", "동엽", "경규", "나래", "세형", "구라", "흥국"]
        self.last_names = ["김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신", "권", "황", "안", "송", "류", "홍"]
        
        self.majors = {
            "SECURITY": ["정보보호학", "컴퓨터공학", "사이버국방", "경찰행정학"],
            "IT": ["컴퓨터공학", "소프트웨어공학", "전자공학", "수학", "통계학"],
            "HR": ["경영학", "심리학", "교육공학", "행정학"],
            "EXECUTIVE": ["경영학(MBA)", "경제학", "법학", "정치외교학"],
            "STAFF": ["문헌정보학", "회계학", "신문방송학", "영문학", "무역학"]
        }
        
        self.certs = {
            "SECURITY": ["CISSP", "CISA", "정보보안기사", "CEH", "AWS Security"],
            "IT": ["AWS SA", "CKA", "SQLD", "정보처리기사", "Google Cloud Pro"],
            "HR": ["노무사", "PHR", "경영지도사", "직업상담사"],
            "EXECUTIVE": ["PMP", "CPA", "AICPA", "MBA수료"],
            "STAFF": ["전산회계", "컴퓨터활용능력", "토익 900+", "비서1급"]
        }

        self.teams = {
            "SECURITY": ["보안팀", "정보보호팀", "관제센터", "경호팀"],
            "IT": ["IT개발팀", "인프라팀", "데이터분석팀", "AI연구팀"],
            "HR": ["인사팀", "인재개발팀", "급여팀", "노무팀"],
            "EXECUTIVE": ["전략기획실", "비서실", "해외영업팀", "이사회"],
            "STAFF": ["총무팀", "재무팀", "홍보팀", "법무팀"]
        }

    def generate_name(self):
        return random.choice(self.last_names) + random.choice(self.first_names)

    def generate_all_data(self):
        """HR 데이터, Actor 데이터, Action 데이터를 한 번에 생성"""
        print("🏭 [Factory] 데이터 생성을 시작합니다...")
        
        # 1. HR 데이터 생성 (Master Data)
        hr_rows = self._create_hr_data()
        
        # 2. Actors 데이터 생성 (HR 데이터 기반 + 외부인 추가)
        self._create_actors_data(hr_rows)
        
        # 3. Actions 데이터 생성 (시나리오 패턴)
        self._create_actions_data()
        
        print("✅ [Factory] 모든 데이터 파일(hr_data.csv, actors.csv, actions.csv) 생성 완료!")

    def _create_hr_data(self):
        data = []
        # 그룹 비율 설정
        groups = (["SECURITY"] * 20 + ["IT"] * 30 + ["HR"] * 15 + ["EXECUTIVE"] * 10 + ["STAFF"] * 25)
        while len(groups) < self.total_count: groups.append("STAFF")
        random.shuffle(groups)

        counts = {"SECURITY": 0, "IT": 0, "HR": 0, "EXECUTIVE": 0, "STAFF": 0}

        for group in groups:
            counts[group] += 1
            prefix = group.lower()[:3] if group != "SECURITY" else "sec"
            if group == "EXECUTIVE": prefix = "exec"
            user_id = f"{prefix}-{1000 + counts[group]}"
            
            name = self.generate_name()
            age = random.randint(24, 58)
            gender = random.choice(["남성", "여성"])
            
            # 직급 로직
            if age < 28: role = "사원"
            elif age < 33: role = "대리"
            elif age < 40: role = "과장"
            elif age < 47: role = "차장"
            else: role = random.choice(["부장", "상무", "전무"])
            
            team = random.choice(self.teams[group])
            major = random.choice(self.majors[group])
            cert_count = random.choice([0, 1, 1, 2])
            certs = ", ".join(random.sample(self.certs[group], k=cert_count)) if cert_count > 0 else "없음"

            row = {
                "id": user_id, "name": name, "age": age, "gender": gender,
                "role": role, "team": team, "company": "태산그룹",
                "group": group, "major": major, "certifications": certs
            }
            data.append(row)

        with open("dummy/hr_data.csv", "w", newline="", encoding="utf-8") as f:
            fieldnames = ["id", "name", "age", "gender", "role", "team", "company", "group", "major", "certifications"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
            
        print(f"   - hr_data.csv 생성 완료 ({len(data)}명)")
        return data

    def _create_actors_data(self, hr_rows):
        # HR 직원들 그대로 배우로 등록
        actors = []
        for row in hr_rows:
            actors.append({
                "id": row["id"], "name": row["name"], "age": row["age"], "gender": row["gender"],
                "role": row["role"], "team": row["team"], "company": row["company"], "group": row["group"]
            })
            
        # 외부인/용의자 추가
        suspects = [
            {"id": "suspect-001", "name": "신원미상", "age": 40, "gender": "남성", "role": "unknown", "team": "unknown", "company": "unknown", "group": "SUSPECT"},
            {"id": "visitor-001", "name": "김방문", "age": 30, "gender": "여성", "role": "방문객", "team": "영업팀", "company": "협력사", "group": "VISITOR"}
        ]
        actors.extend(suspects)

        with open("dummy/actors.csv", "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["id", "name", "age", "gender", "role", "team", "company", "group"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(actors)
            
        print(f"   - actors.csv 생성 완료 ({len(actors)}명 - 직원+외부인)")

    def _create_actions_data(self):
        # 최적화된 시나리오 패턴
        actions = [
            {"category": "SEC", "target_group": "IT", "location": "서버실", "action": "보안 USB를 꽂고 데이터를 다운로드함", "source": "보안 로그"},
            {"category": "SEC", "target_group": "SUSPECT", "location": "지하 주차장", "action": "검은색 가방을 트렁크에 싣는 모습이 포착됨", "source": "CCTV"},
            {"category": "SEC", "target_group": "EXECUTIVE", "location": "강남 비밀 클럽", "action": "경쟁사 임원과 은밀히 만남", "source": "흥신소 제보"},
            {"category": "HR", "target_group": "HR", "location": "인사팀 상담실", "action": "연봉 협상 테이블을 엎고 나감", "source": "CCTV"},
            {"category": "HR", "target_group": "ALL", "location": "흡연실", "action": "팀장에 대한 욕설을 하며 담배를 피움", "source": "동료 직원 면담"},
            {"category": "RELATION", "target_group": "ALL", "location": "구내식당", "action": "함께 점심을 먹으며 웃고 떠듦 (친밀도 상승)", "source": "동료 목격담"},
            {"category": "RELATION", "target_group": "ALL", "location": "휴게실", "action": "서로의 뒷담화를 하다가 언성이 높아짐 (갈등 발생)", "source": "CCTV"},
            {"category": "RELATION", "target_group": "IT", "location": "개발팀 회의실", "action": "서로의 코드를 리뷰해주며 칭찬함 (협력)", "source": "팀장 관찰 기록"},
            {"category": "RELATION", "target_group": "SUSPECT", "location": "비상계단", "action": "은밀하게 쪽지를 건네고 헤어짐 (의심)", "source": "청소부 제보"}
        ]
        
        # 좀 더 늘리기 (단순 복제하여 다양성 확보)
        extended_actions = actions * 3 

        with open("dummy/actions.csv", "w", newline="", encoding="utf-8-sig") as f:
            fieldnames = ["category", "target_group", "location", "action", "source"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(extended_actions)
            
        print(f"   - actions.csv 생성 완료 ({len(extended_actions)}개 패턴)")