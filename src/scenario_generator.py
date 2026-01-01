import time
import random
import csv
import os
from datetime import datetime

class ScenarioGenerator:
    def __init__(self, data_queue):
        self.queue = data_queue
        self.is_running = False
        
        # 1. 기본값 (데이터 없을 때의 Fallback)
        self.actors = [{"name": "김철수", "role": "부장", "team": "보안팀", "group": "SECURITY", "id": "sec-000", "age": "50", "gender": "남성"}]
        self.scenarios = [{"category": "SEC", "target_group": "SECURITY", "location": "서버실", "action": "점검", "source": "로그"}]

        # 2. CSV 데이터 로드
        self.load_csv_data()

    def load_csv_data(self):
        """CSV 로드 (인코딩 처리 및 공백 제거)"""
        if os.path.exists("dummy/actors.csv"):
            try:
                with open("dummy/actors.csv", 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    self.actors = [{k.strip(): v.strip() for k, v in row.items()} for row in reader]
                print(f"  [시뮬레이터] 등장인물 {len(self.actors)}명 로드 완료.")
            except Exception as e:
                print(f"  [시뮬레이터] actors.csv 로드 실패: {e}")
        else:
            print("  [시뮬레이터] dummy/actors.csv 파일이 없습니다. 기본값을 사용합니다.")
            
        if os.path.exists("dummy/actions.csv"):
            try:
                with open("dummy/actions.csv", 'r', encoding='utf-8-sig') as f:
                    reader = csv.DictReader(f)
                    self.scenarios = [{k.strip(): v.strip() for k, v in row.items()} for row in reader]
                print(f"  [시뮬레이터] 행동 패턴 {len(self.scenarios)}개 로드 완료.")
            except Exception as e:
                print(f"  [시뮬레이터] actions.csv 로드 실패: {e}")

    def _get_actor_profile(self, actor):
        """
        [핵심] 온톨로지가 요구하는 속성(ID, 나이, 성별 등)을 텍스트에 모두 포함시킵니다.
        LLM이 이 텍스트를 보고 노드 속성을 꽉 채울 수 있게 합니다.
        """
        name = actor.get('name', '신원미상')
        uid = actor.get('id', 'unknown')
        team = actor.get('team', '소속미상')
        role = actor.get('role', '직원')
        age = actor.get('age', '30')
        gender = actor.get('gender', '알수없음')
        
        return f"{team} {name} {role} (ID: {uid}, {age}세/{gender})"

    def generate_one(self):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. 주인공(Actor 1) 선택
        if not self.actors: return "데이터 없음"
        actor1 = random.choice(self.actors)
        group1 = actor1.get('group', 'ALL')
        
        # 2. 시나리오 필터링
        possible_actions = [
            s for s in self.scenarios 
            if s.get('target_group') == 'ALL' or s.get('target_group') == group1
        ]
        
        if not possible_actions:
            scene = random.choice(self.scenarios)
        else:
            scene = random.choice(possible_actions)

        # 3. [관계] 상대방(Actor 2) 선택 및 정보 구성
        category = scene.get('category', 'ETC')
        target_str = ""
        
        # 관계형 시나리오거나, 30% 확률로 일반 시나리오에도 동료가 등장하게 함 (데이터 풍부화)
        is_relation = (category == 'RELATION') or (random.random() < 0.3)
        
        if is_relation and len(self.actors) > 1:
            while True:
                actor2 = random.choice(self.actors)
                # 본인이 아닌 사람 선택
                id1 = actor1.get('id', actor1.get('name'))
                id2 = actor2.get('id', actor2.get('name'))
                if id1 != id2:
                    break
            
            # [수정] 상대방 정보도 Full Profile로 제공
            target_profile = self._get_actor_profile(actor2)
            target_str = f"대상 '{target_profile}'와(과) 함께 "
            
            # 카테고리가 일반 SEC/HR인데 동료가 등장했다면, RELATION으로 격상시킬 수도 있음 (선택사항)
            # 여기서는 원본 카테고리 유지

        # 4. 주인공 정보 포맷팅 (Full Profile)
        who_str = self._get_actor_profile(actor1)

        # 5. 문장 생성
        where = scene.get('location', '장소미상')
        what = scene.get('action', '행동함')
        source = scene.get('source', '제보')

        # 최종 문장 구성
        # 예: [2025-12-29] [제보-SEC/CCTV] 장소: '서버실'에서 식별된 인물 '보안팀 김철수 부장 (ID: sec-1001, 50세/남성)'이(가) ...
        content = (
            f"[{timestamp}] [제보-{category}/{source}] "
            f"장소: '{where}'에서 식별된 인물 '{who_str}'이(가) {target_str}다음 행동을 수행함: {what}."
        )
        return content
        
    def run(self):
        print("\n  [시뮬레이터] 페르소나 기반 시나리오 생성을 시작합니다.")
        self.is_running = True
        while self.is_running:
            text = self.generate_one()
            self.queue.put(("AUTO_GEN", text))
            time.sleep(random.randint(2, 5))
            
    def stop(self):
        self.is_running = False
        print("\n  [시뮬레이터] 중단됨.")