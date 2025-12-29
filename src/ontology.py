
class GraphSchema:
    """
    그래프 데이터베이스의 노드 및 관계 정의를 관리하는 클래스 (Single Source of Truth)
    """

    # 1. 노드 정의 (Entity Definitions)
    NODES = {
        "Person": {
            "description": "회사 직원 또는 외부 인물",
            "id_key": "id",  # 고유 식별자 키
            "properties": {
                "id": "사번 (예: 'sec-1001'). 없으면 이름 사용.",
                "name": "이름 (예: '김철수')",
                "team": "소속 부서 (예: '보안팀')",
                "role": "직급 (예: '부장')",
                "gender": "성별 ('남성' 또는 '여성'으로 통일)",
                "age": "나이 (Integer)"
            }
        },
        "Organization": {
            "description": "팀, 회사, 학교 등 조직",
            "id_key": "id",
            "properties": {
                "id": "조직명 (예: '보안팀', '태산그룹')",
                "type": "조직 유형 ('Team', 'Company', 'School')"
            }
        },
        "Event": {
            "description": "발생한 사건, 로그, 행동",
            "id_key": "id",
            "properties": {
                "action": "행동 내용 (예: 'USB 접속')",
                "location": "장소",
                "time": "발생 시각 (Timestamp)",
                "source": "출처 (예: 'CCTV', 'Log')"
            }
        },
        "Certificate": {
            "description": "자격증",
            "id_key": "id",
            "properties": {
                "id": "자격증 명칭 (예: 'CISSP')"
            }
        }
    }

    # 2. 관계 정의 (Relationship Rules)
    RELATIONSHIPS = [
        "(Person)-[:WORKS_FOR]->(Organization:Team)",
        "(Organization:Team)-[:PART_OF]->(Organization:Company)",
        "(Person)-[:HAS_CERT]->(Certificate)",
        "(Person)-[:INTERACTED {{score: Int, action: String}}]->(Person)",
        "(Person)-[:PERFORMED]->(Event)"
    ]

    @classmethod
    def get_prompt_instruction(cls):
        """
        LLM에게 주입할 스키마 가이드라인 텍스트를 자동 생성합니다.
        """
        prompt_text = "You are a Knowledge Graph Architect. Follow this Schema strictly:\n\n"
        
        # 노드 규칙 생성
        prompt_text += "[Node Definitions & Properties]\n"
        for label, spec in cls.NODES.items():
            props = ", ".join([f"'{k}'" for k in spec['properties'].keys()])
            prompt_text += f"1. **{label}** Node:\n"
            prompt_text += f"   - Description: {spec['description']}\n"
            prompt_text += f"   - Unique ID: Use property '{spec['id_key']}'\n"
            prompt_text += f"   - Required Properties: {props}\n"
            
            # 상세 규칙 추가
            for k, v in spec['properties'].items():
                prompt_text += f"     * {k}: {v}\n"
            prompt_text += "\n"

        # 관계 규칙 생성
        prompt_text += "[Allowed Relationships]\n"
        for rel in cls.RELATIONSHIPS:
            prompt_text += f"- {rel}\n"
            
        prompt_text += "\n[Strict Rules]\n"
        prompt_text += "1. NEVER create nodes for Age, Price, or Gender. Use properties.\n"
        prompt_text += "2. ID must be unique. If 'sec-1001' is available, use it as 'id'.\n"
        
        return prompt_text

    @classmethod
    def get_qa_mapping(cls):
        """QA 에이전트용 속성 매핑 정보"""
        return """
        [Property Mapping] (Derived from Ontology):
           - **Gender**: Use property 'gender' ('남성', '여성')
           - **ID**: Use property 'id'
           - **Name**: Use property 'name'
           - **Team**: Use property 'team'
           - **Role**: Use property 'role'
        """