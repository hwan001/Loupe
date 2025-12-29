import csv
import time
from ontology import GraphSchema

class HRDataManager:
    def __init__(self, queue, graph):
        self.queue = queue
        self.graph = graph

    def load_csv(self, filename="dummy/hr_data.csv"):
        """
        [Direct Injection]
        CSV 데이터를 읽어 LLM을 거치지 않고 직접 Neo4j에 노드와 속성을 주입합니다.
        이 방식은 속성 누락을 100% 방지합니다.
        """
        print(f"📂 [HR] '{filename}' 데이터를 로드하여 DB에 직접 동기화합니다...")
        
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
            if not rows:
                print("⚠️ CSV 파일이 비어있습니다.")
                return

            print(f"   - 총 {len(rows)}명의 임직원 데이터를 처리 중...")

            # 1. 인물(Person) 및 조직(Organization) 노드 직접 생성 쿼리
            # UNWIND를 사용하여 대량 데이터를 한 번에 처리 (Batch Processing)
            query_ingest = """
            UNWIND $rows AS row
            
            // 1. Person 노드 생성 (속성 완벽 보존)
            MERGE (p:Person {id: row.id})
            SET p.name = row.name,
                p.age = toInteger(row.age),
                p.gender = row.gender,
                p.role = row.role,
                p.team = row.team,
                p.company = row.company,
                p.major = row.major
            
            // 2. Organization(Team) 노드 및 관계 연결
            MERGE (t:Organization {id: row.team})
            SET t.type = 'Team'
            MERGE (p)-[:WORKS_FOR]->(t)
            
            // 3. Organization(Company) 노드 및 관계 연결
            MERGE (c:Organization {id: row.company})
            SET c.type = 'Company'
            MERGE (t)-[:PART_OF]->(c)
            
            // 4. Major(전공) 노드 연결
            MERGE (m:Major {id: row.major})
            MERGE (p)-[:STUDIED]->(m)
            """
            
            # 자격증 처리는 리스트 형태라 별도 로직 필요, 혹은 위에서 처리 가능하지만
            # 복잡도를 낮추기 위해 루프 내에서 개별 처리하지 않고, 여기서는 간단히 무시하거나
            # 필요 시 아래와 같이 추가 쿼리 실행 가능.
            
            # 쿼리 실행
            self.graph.query(query_ingest, params={'rows': rows})
            
            # 자격증(Certificate) 별도 처리 (쉼표로 구분된 경우)
            for row in rows:
                if row.get('certifications') and row['certifications'] != "없음":
                    certs = [c.strip() for c in row['certifications'].split(',')]
                    query_cert = """
                    MATCH (p:Person {id: $pid})
                    UNWIND $certs AS cert_name
                    MERGE (c:Certificate {id: cert_name})
                    MERGE (p)-[:HAS_CERT]->(c)
                    """
                    self.graph.query(query_cert, params={'pid': row['id'], 'certs': certs})

            # [선택] Evidence 확보를 위해 텍스트 로그만 큐에 남김 (학습용이 아니라 증적용)
            # 여기서는 그래프 생성을 이미 했으므로 큐에 넣지 않거나, 
            # "시스템 로그" 형태로만 큐에 넣어 Evidence 노드만 따로 만들게 할 수 있음.
            # (깔끔하게 그래프만 구성하려면 생략 가능)

            print(f"   ✅ {len(rows)}명의 데이터가 그래프 DB에 완벽하게 적재되었습니다.")
            
        except FileNotFoundError:
            print(f"❌ 파일을 찾을 수 없습니다: {filename}")
        except Exception as e:
            print(f"❌ 데이터 적재 중 오류 발생: {e}")

    def run_relationship_inference(self):
        """Phase 2: 그래프 내부를 분석하여 관계 연결 및 가중치 부여 (Inference)"""
        print("🔗 [HR] 인물 간 관계 및 가중치 추론(Inference)을 시작합니다...")
        
        # [규칙 1] 같은 팀(Organization) 소속이면 'CO_WORKER' 관계 형성
        query_team = """
        MATCH (p1:Person)-[:WORKS_FOR]->(t:Organization)<-[:WORKS_FOR]-(p2:Person)
        WHERE elementId(p1) < elementId(p2) 
        MERGE (p1)-[r:CO_WORKER]-(p2)
        SET r.strength = 8, 
            r.source = 'System_Inference_Team'
        RETURN count(r) as connections
        """
        
        # [규칙 2] 같은 전공(Major)이면 'ALUMNI' 관계 형성
        query_major = """
        MATCH (p1:Person)-[:STUDIED]->(m:Major)<-[:STUDIED]-(p2:Person)
        WHERE elementId(p1) < elementId(p2)
        MERGE (p1)-[r:ALUMNI]-(p2)
        SET r.strength = 3, 
            r.source = 'System_Inference_Major'
        RETURN count(r) as connections
        """
        
        try:
            # 팀 동료 추론
            res1 = self.graph.query(query_team)
            c1 = res1[0]['connections'] if res1 else 0
            
            # 전공 동문 추론
            res2 = self.graph.query(query_major)
            c2 = res2[0]['connections'] if res2 else 0
            
            print(f"   🔹 [결과] 같은 부서 동료 관계: {c1}건 연결됨.")
            print(f"   🔹 [결과] 같은 전공 동문 관계: {c2}건 연결됨.")
            
        except Exception as e:
            print(f"   ⚠️ 추론 쿼리 실행 실패: {e}")