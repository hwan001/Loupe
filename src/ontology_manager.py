import json
import os
from langchain_core.prompts import PromptTemplate
from ontology import GraphSchema  # [Factory Default]

class OntologyManager:
    def __init__(self, llm, storage_file="src/schema_storage.json"):
        self.llm = llm
        self.storage_file = storage_file
        self.current_schema = self._load_schema()

    def _load_schema(self):
        """
        우선순위 1: 저장된 JSON 파일 (이전에 확장된 스키마)
        우선순위 2: ontology.py (기본 스키마)
        """
        if os.path.exists(self.storage_file):
            try:
                print(f"📂 [Ontology] 저장된 스키마 파일('{self.storage_file}')을 로드합니다.")
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️ 스키마 파일 로드 실패 (기본값 사용): {e}")
        
        print("🆕 [Ontology] 저장된 파일이 없어 기본 스키마(ontology.py)로 초기화합니다.")
        # 기본 스키마 구조
        return {
            "nodes": GraphSchema.NODES,
            "relationships": GraphSchema.RELATIONSHIPS
        }

    def save_schema(self):
        """현재 스키마를 JSON 파일로 저장"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_schema, f, indent=4, ensure_ascii=False)
            print(f"💾 [Ontology] 변경된 스키마가 '{self.storage_file}'에 저장되었습니다.")
        except Exception as e:
            print(f"⚠️ 스키마 저장 실패: {e}")

    def get_instruction_string(self):
        """Loupe 학습기용 프롬프트 생성 (동적 스키마 기반)"""
        txt = "You are a Knowledge Graph Architect. Follow this Dynamic Schema strictly:\n\n"
        
        txt += "[Node Definitions]\n"
        for label, spec in self.current_schema["nodes"].items():
            # JSON 로드 시와 ontology.py 로드 시 호환성 유지
            desc = spec.get('description', 'No description')
            props = spec.get('properties', {})
            prop_str = ", ".join([f"'{k}'" for k in props.keys()])
            
            txt += f"- **{label}** Node:\n"
            txt += f"  * Description: {desc}\n"
            txt += f"  * Required Properties: {prop_str}\n"
            
        txt += "\n[Allowed Relationships]\n"
        for rel in self.current_schema["relationships"]:
            txt += f"- {rel}\n"
            
        return txt

    def discover_schema(self, text_samples):
        """[AI] 데이터 패턴 분석 및 스키마 확장 제안"""
        print("🧠 [Architect] 데이터 패턴을 분석하여 온톨로지 확장을 시도합니다...")

        prompt_template = """
        You are a Knowledge Graph Architect.
        
        [Current Schema]:
        {current_schema}
        
        [New Data Samples]:
        {samples}
        
        [Task]:
        Analyze the data samples. If there are distinct entities or relationships NOT covered by the Current Schema, suggest new ones.
        
        [Output Format (JSON Only)]:
        {{
            "new_nodes": {{
                "NodeLabel": {{ "description": "...", "id_key": "id", "properties": {{ "prop": "desc" }} }}
            }},
            "new_relationships": [
                "(SourceNode)-[:RELATIONSHIP_TYPE]->(TargetNode)"
            ]
        }}
        If no new schema is needed, return empty JSON.
        """
        
        prompt = PromptTemplate(
            input_variables=["current_schema", "samples"],
            template=prompt_template
        )
        
        chain = prompt | self.llm
        try:
            samples_str = "\n".join(text_samples[:5]) 
            response = chain.invoke({
                "current_schema": json.dumps(self.current_schema, indent=2, ensure_ascii=False), 
                "samples": samples_str
            })
            
            content = response.content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            
            return json.loads(content)
            
        except Exception as e:
            print(f"⚠️ 스키마 발견 실패: {e}")
            return None

    def update_schema(self, suggestion):
        """제안된 스키마 병합 및 파일 저장"""
        if not suggestion: return
        
        new_nodes = suggestion.get("new_nodes", {})
        new_rels = suggestion.get("new_relationships", [])
        
        updated_count = 0
        
        # 노드 병합
        for label, spec in new_nodes.items():
            if label not in self.current_schema["nodes"]:
                self.current_schema["nodes"][label] = spec
                print(f"   ✨ [New Entity] '{label}' 엔티티가 추가되었습니다.")
                updated_count += 1
                
        # 관계 병합
        for rel in new_rels:
            if rel not in self.current_schema["relationships"]:
                self.current_schema["relationships"].append(rel)
                print(f"   🔗 [New Relation] 관계 규칙 추가: {rel}")
                updated_count += 1
                
        if updated_count > 0:
            self.save_schema()  # [핵심] 변경사항 파일 저장
            print("   ✅ 스키마 업데이트 및 저장이 완료되었습니다. (재시작 시 반영됨)")
        else:
            print("   (변동 사항 없음)")