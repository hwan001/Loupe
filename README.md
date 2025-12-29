# Loupe

## Getting started

### .env 설정
- .env.example를 .env로 복사하고 API 키를 설정합니다.
- neo4j 연결 정보를 설정합니다.
    - 로컬에 neo4j 생성 (사용중인 neo4j가 있다면 생략) 
        - `docker compose up -d`

### Loupe 실행
```sh
uv run src/loupe.py
```

### UI 및 더미데이터 생성
```
📂 [Ontology] 저장된 스키마 파일('src/schema_storage.json')을 로드합니다.
🧠 [Loupe] 자율 학습 엔진 가동 (Dynamic Ontology 기반)
--- 🔮 Loupe v1.0: Full Integrated System ---
   📜 적용된 스키마: Person, Organization, Event, Certificate 등.
--- 🤖 Engine: GOOGLE / gemini-flash-latest ---
  ✅ [시뮬레이터] 등장인물 102명 로드 완료.
  ✅ [시뮬레이터] 행동 패턴 27개 로드 완료.

------------------------------------------------
 [1] 수동 제보   [2] 질문하기   [3] 시뮬레이터 OFF ⚪
 [4] 뇌 초기화   [5] HR 데이터 로드   [6] 관계 점수 집계
 [7] 테스트 데이터 생성(CSV)   [8] AI 온톨로지 발견(New)   [q] 종료
 선택 > 7
```



### Neo4j 데이터 확인

- 노드, 관계 생성 예시 (시뮬레이터 사용 시)
    1. http://localhost:7474/browser/ 접근
    2. 쿼리 : `match(n) return n`
        ![alt text](neo4j-1.png)


### google ai 모델 호출 실패 시 확인

.env에 구글 API 키 셋팅 후
```
uv run src/check_models.py
```