# Loupe

## Getting started

### .env 설정
- .env.example를 .env로 복사하고 API 키를 설정합니다.
- neo4j 연결 정보를 설정합니다.
    - 로컬에 neo4j 생성 (사용중인 neo4j가 있다면 생략) 
        - `docker compose up -d`

### Loupe 실행
```sh
uv run loupe.py
```


### 더미 데이터 생성
```
------------------------------------------------
 [1] 수동 제보   [2] 질문하기(Router)   [3] 시뮬레이터 OFF ⚪
 [4] 뇌 초기화   [q] 종료
 선택 > 3

🎰 [시뮬레이터] 가상 시나리오(보안+HR) 생성을 시작합니다. (5초~10초 간격)

------------------------------------------------
```


### Neo4j 데이터 확인

- 노드, 관계 생성 예시 (시뮬레이터 사용 시)
    1. http://localhost:7474/browser/ 접근
    2. 쿼리 : `match(n) return n`
        ![alt text](neo4j-1.png)

