import os
import time
import threading
import queue
import uuid
import sys
import csv  # [NEW] 샘플 데이터 읽기용
from dotenv import load_dotenv

# [LangChain & Neo4j]
from langchain_community.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document

# [Custom Modules]
from ontology_manager import OntologyManager 
from ontology import GraphSchema
from scenario_generator import ScenarioGenerator
from hr_manager import HRDataManager
from utils import load_prompt_file
from data_generator import DataGenerator
from llm_factory import get_chat_model

# [설정] 환경 변수 로드
load_dotenv()

# [1. LLM 연결 (Factory Pattern)]
try:
    llm = get_chat_model()
except Exception as e:
    print(f"❌ LLM 초기화 실패: {e}")
    sys.exit(1)

# [2. DB 연결]
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    username=os.getenv("NEO4J_USERNAME", "neo4j"),
    password=os.getenv("NEO4J_PASSWORD", "password")
)

# [비동기] 데이터 대기열
data_queue = queue.Queue()

# [프롬프트 및 스키마 로드]
QA_PROMPT_TEXT = load_prompt_file("src/prompt_qa.md")

# [매니저 초기화]
hr_manager = HRDataManager(data_queue, graph)
data_generator = DataGenerator(dummy_dir="dummy", total_count=50) 
ontology_manager = OntologyManager(llm) # 동적 스키마 매니저

# 초기 학습 지침 생성 (OntologyManager가 관리하는 스키마 기반)
INGESTION_INSTRUCTIONS = ontology_manager.get_instruction_string()


# ---------------------------------------------------------
# 1. [Worker] 자율 온톨로지 학습기
# ---------------------------------------------------------
def ingestion_worker():
    print("  [Loupe] 자율 학습 엔진 가동 (Dynamic Ontology 기반)")
    
    # 워커 시작 시점의 최신 스키마 노드 리스트 가져오기
    current_allowed_nodes = list(ontology_manager.current_schema["nodes"].keys())
    print(f"  적용된 스키마: {', '.join(current_allowed_nodes)} 등.")

    transformer = LLMGraphTransformer(
        llm=llm,
        allowed_nodes=current_allowed_nodes, # 동적 리스트 주입
        allowed_relationships=[], 
        additional_instructions=INGESTION_INSTRUCTIONS # 위에서 생성한 지침 주입
    )

    while True:
        try:
            source_type, text = data_queue.get()
            prefix = "  [자동]" if source_type == "AUTO_GEN" else "  [제보]"
            if source_type == "HR_DB": prefix = "  [HR]"
            
            print(f"\n{prefix} 수신: '{text}' -> 학습 시작...")
            
            documents = [Document(page_content=text)]
            graph_documents = transformer.convert_to_graph_documents(documents)
            
            if graph_documents:
                graph.add_graph_documents(graph_documents)
                
                # Evidence Node 생성 로직
                evidence_id = f"EV_{int(time.time())}_{str(uuid.uuid4())[:8]}"
                extracted_node_ids = [node.id for node in graph_documents[0].nodes]
                
                evidence_query = """
                MERGE (e:Evidence {id: $ev_id})
                SET e.text = $text, e.source = $source, e.timestamp = datetime()
                WITH e
                MATCH (n) WHERE n.id IN $node_ids
                MERGE (n)-[:MENTIONED_IN]->(e)
                """
                graph.query(evidence_query, params={
                    "ev_id": evidence_id, "text": text, 
                    "source": source_type, "node_ids": extracted_node_ids
                })
                print(f"  [백그라운드] 학습 완료 (노드 {len(extracted_node_ids)}개 연결됨)")
            else:
                print(f"  [백그라운드] 정보 추출 실패")
            
            data_queue.task_done()
        except Exception as e:
            print(f"  [백그라운드 오류] {e}")

threading.Thread(target=ingestion_worker, daemon=True).start()

# ---------------------------------------------------------
# 2. [Agent] QA Engine
# ---------------------------------------------------------
def ask_loupe(question):
    graph.refresh_schema()
    mapping_rules = GraphSchema.get_qa_mapping()
    
    CYPHER_GENERATION_TEMPLATE = f"""
    Task: Generate Cypher statement to query a graph database.
    [Schema]:
    {{schema}}
    {mapping_rules}
    [Instructions]:
    1. Use 'elementId()' or 'id' property.
    2. Try to return Evidence nodes.
    Question: {{question}}
    """
    
    cypher_prompt = PromptTemplate(input_variables=["schema", "question"], template=CYPHER_GENERATION_TEMPLATE)
    qa_prompt = PromptTemplate(input_variables=["context", "question"], template=QA_PROMPT_TEXT)

    try:
        chain = GraphCypherQAChain.from_llm(
            llm, graph=graph, verbose=True, allow_dangerous_requests=True,
            cypher_prompt=cypher_prompt, qa_prompt=qa_prompt
        )
        return chain.invoke(question)
    except Exception as e:
        return {"result": f"오류 발생: {e}"}

# ---------------------------------------------------------
# 3. [Logic] 관계 집계 엔진
# ---------------------------------------------------------
def aggregate_relationships():
    print("  [시스템] 인물 간 상호작용 점수를 집계하여 관계 지도를 갱신합니다...")
    query = """
    MATCH (p1:Person)-[r:INTERACTED]->(p2:Person)
    WITH p1, p2, sum(r.score) AS total_score
    WHERE total_score IS NOT NULL
    MERGE (p1)-[rel:RELATIONSHIP]-(p2)
    SET rel.strength = total_score, rel.last_updated = datetime()
    RETURN count(rel) as updated_count
    """
    try:
        result = graph.query(query)
        count = result[0]['updated_count'] if result else 0
        print(f"  {count}쌍의 인물 관계 강도(strength)가 갱신되었습니다.")
    except Exception as e:
        print(f"  관계 집계 오류: {e}")

# ---------------------------------------------------------
# 4. [Main] 사용자 인터페이스
# ---------------------------------------------------------
if __name__ == "__main__":
    print("--- Loupe v1.0: Full Integrated System ---")
    print(f"--- Engine: {os.getenv('LLM_PROVIDER', 'Unknown').upper()} / {os.getenv('LLM_MODEL')} ---")
    
    simulator = ScenarioGenerator(data_queue)
    sim_thread = None

    dummy_actors = "dummy/actors.csv"
    dummy_actions = "dummy/actions.csv"
    dummy_hr_data = "dummy/hr_data.csv"

    try:
        while True:
            sim_status = "ON" if simulator.is_running else "OFF"
            
            print(f"\n------------------------------------------------")
            print(f" [1] 수동 제보   [2] 질문하기   [3] 시뮬레이터 {sim_status}")
            print(f" [4] 초기화   [5] HR 데이터 로드   [6] 관계 점수 집계")
            print(f" [7] 더미 데이터 생성   [8] AI 온톨로지 개선   [q] 종료")
            choice = input(" 선택 > ")
            
            if choice == '1':
                text = input("제보할 내용: ")
                if text.strip(): 
                    data_queue.put(("USER", text))
                    print("  접수되었습니다.")
                
            elif choice == '2':
                query = input("질문: ")
                if query.strip():
                    print("  분석 중...")
                    res = ask_loupe(query)
                    print(f"\n  답변:\n{res['result']}")
                
            elif choice == '3':
                if not simulator.is_running:
                    if not os.path.exists(dummy_actors):
                        print(f"{dummy_actors}가 없습니다. ([7]번으로 더미 데이터 생성 가능)")
                    else:
                        sim_thread = threading.Thread(target=simulator.run, daemon=True)
                        sim_thread.start()
                else:
                    simulator.stop()
                    if sim_thread: sim_thread.join()

            elif choice == '4':
                if input("  정말 초기화합니까? (y/n): ") == 'y':
                    try:
                        graph.query("MATCH (n) DETACH DELETE n") # 데이터 초기화
                        ontology_manager.clear() # 스키마 초기화
                        data_generator.clear() # 더미 데이터 삭제

                        print("  초기화 완료")
                    except Exception as e:
                        print(f"  초기화 실패: {e}")

            elif choice == '5':
                if not os.path.exists(dummy_hr_data):
                    print(f"{dummy_hr_data} 파일이 없습니다. ([7]번으로 HR 더미 데이터 생성 가능)")
                else:
                    hr_manager.load_csv(dummy_hr_data)
                    hr_manager.run_relationship_inference() # 관계 추론

            elif choice == '6':
                aggregate_relationships()
                
            elif choice == '7':
                data_generator.generate_all_data()

            elif choice == '8':
                print("  최근 시나리오 데이터를 분석하여 스키마 확장을 시도합니다...")
                samples = []
                
                if os.path.exists(dummy_actions):
                     with open(dummy_actions, 'r', encoding='utf-8-sig') as f:
                        reader = csv.DictReader(f)
                        for i, row in enumerate(reader):
                            if i >= 5: break
                            samples.append(f"장소 {row['location']}에서 {row['target_group']} 그룹이 '{row['action']}' 행동을 함.")
                
                if samples:
                    suggestion = ontology_manager.discover_schema(samples)
                    if suggestion:
                        print("\n AI가 제안한 스키마 변경안:")
                        print(suggestion)
                        if input("  이 변경사항을 적용하시겠습니까? (y/n): ") == 'y':
                            ontology_manager.update_schema(suggestion)
                            print("  주의: 변경된 스키마를 적용하려면 프로그램을 재시작해주세요.")
                    else:
                        print("  현재 데이터로는 새로운 스키마가 필요하지 않습니다.")
                else:
                    print(f" 분석할 {dummy_actions} 파일이 없습니다. ([7]번으로 생성 가능)")

            elif choice == 'q':
                if simulator.is_running: simulator.stop()
                print("시스템을 종료합니다.")
                sys.exit(0)
                
    except KeyboardInterrupt:
        if simulator.is_running: simulator.stop()
        print("\n강제 종료")
        sys.exit(0)