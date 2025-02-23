from typing import Dict
from app.services.llm_service import LLMService

class IntentService:
    def __init__(self, llm_service: LLMService):
        self.llm = llm_service
    
    async def analyze_intent(self, query: str) -> Dict[str, str]:
        """分析用户查询的意图"""
        prompt = f"""分析以下查询的意图，返回JSON格式：
        查询：{query}
        
        要求：
        1. 识别查询类型（SELECT/INSERT/UPDATE/DELETE）
        2. 识别涉及的主要业务实体
        3. 识别时间范围（如果有）
        4. 识别聚合操作（如果有）
        
        仅返回JSON，格式如下：
        {{
            "query_type": "SELECT/INSERT/UPDATE/DELETE",
            "entities": ["entity1", "entity2"],
            "time_range": "last_30_days/specific_date/null",
            "aggregation": "count/sum/avg/null"
        }}
        """
        
        result = await self.llm.generate(prompt)
        return result 