import os
import time
import threading
import queue
import uuid
from dotenv import load_dotenv

from langchain_community.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_openai import ChatOpenAI
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_core.prompts import PromptTemplate
from langchain_core.documents import Document
from scenario_generator import ScenarioGenerator

# [설정] 환경 변수 로드
load_dotenv()

# [시스템 연결]
llm = ChatOpenAI(temperature=0, model_name=os.getenv("LLM_MODEL", "gpt-4o"))
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    username=os.getenv("NEO4J_USERNAME", "neo4j"),
    password=os.getenv("NEO4J_PASSWORD", "password")
)

# [비동기] 데이터가 쌓이는 대기열 (Message Queue)
data_queue = queue.Queue()

# ---------------------------------------------------------
# 1. [Worker] 백그라운드에서 조용히 일하는 학습 로봇
# ---------------------------------------------------------
def ingestion_worker():
    print("  [시스템] 백그라운드 데이터 학습 작업자가 시작되었습니다.")
    
    # 1. [AI 역할] 순수하게 사실 관계(Fact)만 추출하도록 지시 (Evidence 생성 지시는 제거)
    instructions = """
    당신은 범죄 수사 전문 데이터 분석가입니다.
    텍스트를 분석하여 인물, 장소, 사건 간의 관계를 추출하세요.
    
    1. 인물 이름 정규화: '김철수 부장' -> '김철수' (직함 제거)
    2. 관계 연결: 'SUSPECTED_TO_BE', 'ACCOMPLICE', 'RELATED_TO' 등 적극적 연결
    3. 추론: 명시되지 않아도 문맥상 연결되면 관계 생성
    """

    transformer = LLMGraphTransformer(
        llm=llm,
        allowed_nodes=["Person", "Organization", "Project", "Event", "Item", "Location", "Rumor", "Unknown"],
        allowed_relationships=["WORKS_FOR", "LEADS", "HAS_ROLE", "INVOLVED_IN", "LOCATED_AT", "OWNS", "CREATED", "TRANSFERRED", "RELATED_TO", "HAS_DEBT", "VISITED", "MET_WITH", "COPIED", "SUSPECTED_TO_BE", "ACCOMPLICE", "USED", "HACKED"],
        additional_instructions=instructions
    )

    while True:
        try:
            source_type, text = data_queue.get()
            prefix = "  [자동]" if source_type == "AUTO_GEN" else "  [제보]"
            print(f"\n{prefix} 수신: '{text}' -> 학습 시작...")
            
            # 2. [Step A] AI가 텍스트에서 노드와 관계 추출
            documents = [Document(page_content=text)]
            graph_documents = transformer.convert_to_graph_documents(documents)
            
            if graph_documents:
                # 3. [Step B] 그래프 DB에 사실 관계 저장
                graph.add_graph_documents(graph_documents)
                
                # 4. [Step C] '증거(Evidence) 노드' 직접 생성 및 연결
                # 고유 ID 생성 (시간 + 랜덤)
                evidence_id = f"EV_{int(time.time())}_{str(uuid.uuid4())[:8]}"
                
                # 방금 AI가 찾아낸 노드들의 ID 목록 추출
                extracted_node_ids = [node.id for node in graph_documents[0].nodes]
                
                # Cypher 쿼리로 증거 노드 생성 + 발견된 노드들과 연결
                evidence_query = """
                MERGE (e:Evidence {id: $ev_id})
                SET e.text = $text, 
                    e.source = $source, 
                    e.timestamp = datetime()
                
                WITH e
                MATCH (n) 
                WHERE n.id IN $node_ids
                MERGE (n)-[:MENTIONED_IN]->(e)
                """
                
                graph.query(evidence_query, params={
                    "ev_id": evidence_id,
                    "text": text,
                    "source": source_type,
                    "node_ids": extracted_node_ids
                })
                
                print(f"  [백그라운드] 학습 완료 (노드 {len(extracted_node_ids)}개 연결됨, 증거 ID: {evidence_id})")
            else:
                print(f"  [백그라운드] 정보 추출 실패 (내용 부족)")
            
            data_queue.task_done()
            
        except Exception as e:
            print(f"  [백그라운드 오류] {e}")

# 스레드 실행 (프로그램 시작 시 한 번만 실행)
worker_thread = threading.Thread(target=ingestion_worker, daemon=True)
worker_thread.start()


# ---------------------------------------------------------
# 2. [Agents] 분야별 전문 에이전트 설정
# ---------------------------------------------------------

# (A) 보안 전문 에이전트
def run_security_agent(query):
    print("  [오퍼레이터] '보안 팀'을 호출합니다.")
    return ask_graph_agent(query, role="Security Expert")

# (B) 인사/탐정 전문 에이전트
def run_hr_agent(query):
    print("  [오퍼레이터] '인사/조사 팀'을 호출합니다.")
    return ask_graph_agent(query, role="HR & Investigation Expert")

def ask_graph_agent(question, role):
    # 1. [검색 전략]
    CYPHER_GENERATION_TEMPLATE = f"""
    Task: Generate Cypher statement to query a graph database.
    You are a {{role}}.
    
    [Schema]:
    {{schema}}
    
    [Instructions]:
    1. Use only the provided relationship types and properties in the schema.
    2. Do NOT search for abstract concepts like "suspicious", "security", "threat" directly in node IDs. 
       Instead, map them to specific entities as defined below.

    3. [Evidence Retrieval Strategy] (가장 중요!)
       - When finding a path between entities, ALWAYS try to retrieve the connected 'Evidence' node to show the source text.
       - Query Structure Example:
         MATCH path = (p:Person)-[*1..2]-(target)
         OPTIONAL MATCH (p)-[:MENTIONED_IN]->(e:Evidence)
         RETURN path, e.text AS evidence_text, e.source AS source

    4. [Core Logic] When searching for answers, always look for the 'surrounding context' (1-2 hops).
       Example: MATCH path = (p:Person)-[*1..2]-(target) ... RETURN path
    
    5. [Target Mapping Strategy] (매우 중요! 질문의 의도를 구체적인 키워드로 변환하세요)
       - If asking about "Security" or "Suspicious":
         Look for nodes containing: 'USB', '서버', '해킹', '비밀', '클럽', '비트코인', '신원 미상', 'CCTV'
         Query Example: 
         MATCH (n) WHERE n.id CONTAINS 'USB' OR n.id CONTAINS '서버' OR n.id CONTAINS '해킹' OR n.id CONTAINS '비밀' OR n.id CONTAINS '클럽' OR n.id CONTAINS '비트코인' OR n.id CONTAINS '신원 미상' OR n.id CONTAINS 'CCTV'
         MATCH path = (n)-[*1..2]-(related) RETURN path
         
       - If asking about "HR" or "Conflict":
         Look for nodes containing: '싸움', '언쟁', '갈등', '루머', '소문', '블라인드', '연봉', '의심', '이직', '퇴사', '사직', '급여', '대출'
    
    6. [ID Search Rule] 
       - Always use `CONTAINS` for filtering string IDs.
       - Use 'id' property, NOT 'name'. (e.g., p.id CONTAINS '김')
    
    7. 'Who', 'Relation', 'Why':
       - Must check 'SUSPECTED_TO_BE', 'ACCOMPLICE', 'RELATED_TO' relationships.

    The question is:
    {{question}}
    """
    
    cypher_prompt = PromptTemplate(
        input_variables=["schema", "question"],
        partial_variables={"role": role},
        template=CYPHER_GENERATION_TEMPLATE
    )

    # 2. [답변 전략] (기존과 동일)
    QA_TEMPLATE = f"""
    당신은 {{role}}입니다.
    아래의 [조회된 데이터]를 바탕으로 답하세요.
    
    [조회된 데이터]:
    {{context}}
    
    [답변 가이드라인]:
    1. **[증거 기반]** 답변을 할 때 반드시 근거가 되는 'evidence_text'(원본 텍스트)를 인용해서 보여주세요.
       예: "김철수가 의심됩니다. 근거는 다음과 같습니다: '[14:00] CCTV에서 서버실 침입 확인됨'"
    2. 발견된 사실들 사이의 타임라인이나 인과관계를 탐정처럼 설명하세요.
    3. 정보가 없으면 솔직하게 말하세요.
    
    질문: {{question}}
    답변:
    """

    qa_prompt = PromptTemplate(
        input_variables=["context", "question"],
        partial_variables={"role": role},
        template=QA_TEMPLATE
    )

    try:
        chain = GraphCypherQAChain.from_llm(
            llm, 
            graph=graph, 
            verbose=True, 
            allow_dangerous_requests=True, 
            cypher_prompt=cypher_prompt,
            qa_prompt=qa_prompt
        )
        return chain.invoke(question)
    except Exception as e:
        return {"result": f"오류 발생: {e}"}


# ---------------------------------------------------------
# 3. [Operator] 질문 분석 및 할당 (The Router)
# ---------------------------------------------------------
def operator_router(query):
    """
    사용자의 질문 의도를 파악하여 적절한 에이전트에게 연결합니다.
    """
    prompt = f"""
    아래 질문을 분석하여 다음 중 담당할 부서를 하나만 선택해 단어로 출력하세요: [SECURITY, HR, GENERAL]
    
    [판단 기준]
    - SECURITY: CCTV, 로그, 해킹, 출입 기록, 파일 복사, 물리적 보안 위반
    - HR: 조직도, 직책, 채용, 해고, 사내 소문(평판), 개인의 재정 상태, 가족 관계, 인물 간의 사적 관계
    - GENERAL: 그 외 일반적인 질문

    질문: {query}
    담당부서:
    """
    response = llm.invoke(prompt)
    if hasattr(response, 'content'):
        dept = response.content.strip().upper()
    else:
        dept = str(response).strip().upper()
    
    if "SECURITY" in dept:
        return run_security_agent(query)
    elif "HR" in dept:
        return run_hr_agent(query)
    else:
        return ask_graph_agent(query, role="General Assistant")

# ---------------------------------------------------------
# 4. [초기화] 데이터베이스 초기화
# ---------------------------------------------------------
def reset_brain():
    print("\n [경고] 데이터베이스의 모든 지식을 영구 삭제합니다.")
    confirm = input("정말 초기화하시겠습니까? (y/n): ").strip().lower()
    
    if confirm == 'y':
        try:
            # Neo4j의 모든 노드와 관계를 끊고 삭제하는 쿼리
            graph.query("MATCH (n) DETACH DELETE n")
            print(" [시스템] 루페의 뇌가 깨끗하게 비워졌습니다. (초기화 완료)")
        except Exception as e:
            print(f" 초기화 실패: {e}")
    else:
        print("취소되었습니다.")


# ---------------------------------------------------------
# 4. [메인] 사용자 인터페이스 (수정됨)
# ---------------------------------------------------------
if __name__ == "__main__":
    print("--- Loupe v0.5: Multi-Agent & Simulator ---")
    print("실시간 시나리오 생성 및 비동기 학습 시스템")
    
    # [NEW] 시뮬레이터 객체 생성 (아직 실행은 안 됨)
    # generator.py 파일이 같은 폴더에 있어야 합니다.
    simulator = ScenarioGenerator(data_queue)
    sim_thread = None

    while True:
        # 시뮬레이터가 켜져 있는지 상태 확인
        sim_status = "ON" if simulator.is_running else "OFF"
        
        print(f"\n------------------------------------------------")
        print(f" [1] 수동 제보   [2] 질문하기(Router)   [3] 시뮬레이터 {sim_status}")
        print(f" [4] 뇌 초기화   [q] 종료")
        choice = input(" 선택 > ")
        
        if choice == '1':
            text = input("제보할 내용: ")
            data_queue.put(("사용자제보", text))
            print("  제보가 접수되었습니다. (백그라운드에서 처리됩니다)")
            
        elif choice == '2':
            query = input("질문: ")
            # 오퍼레이터가 분석 후 적절한 요원에게 배정
            result = operator_router(query)
            print(f"  답변: {result['result']}")
            
        elif choice == '3':
            # [NEW] 시뮬레이터 토글 기능
            if not simulator.is_running:
                # 시뮬레이터의 run 메서드를 별도 스레드로 실행 (안 그러면 프로그램 멈춤)
                sim_thread = threading.Thread(target=simulator.run, daemon=True)
                sim_thread.start()
            else:
                # 멈추기
                simulator.stop()
                if sim_thread:
                    sim_thread.join() # 스레드가 안전하게 끝날 때까지 대기

        elif choice == '4':
            # [NEW] 데이터베이스 초기화
            reset_brain()

        elif choice == 'q':
            if simulator.is_running: simulator.stop()
            print("시스템을 종료합니다.")
            break