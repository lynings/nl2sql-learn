from typing import Dict, List, Any
from app.database.schema_store import SchemaStore

class ContextService:
    def __init__(self, schema_store: SchemaStore):
        self.schema_store = schema_store
    
    async def get_relevant_context(
        self,
        intent: Dict[str, str],
        query: str
    ) -> Dict[str, Any]:
        """获取相关的上下文信息"""
        
        # 获取相关表结构
        tables = await self.schema_store.get_relevant_tables(
            entities=intent["entities"],
            query_text=query
        )
        
        # 获取字段信息
        fields = await self.schema_store.get_relevant_fields(
            tables=tables,
            query_text=query
        )
        
        # 获取业务规则
        business_rules = await self.schema_store.get_business_rules(
            entities=intent["entities"]
        )
        
        return {
            "tables": tables,
            "fields": fields,
            "business_rules": business_rules,
            "query_type": intent["query_type"],
            "time_range": intent["time_range"],
            "aggregation": intent["aggregation"]
        } 