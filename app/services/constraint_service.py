from typing import Dict, List, Any
import logging
import json
from pathlib import Path
from app.services.llm_service import LLMService
from app.database.schema_store import SchemaStore

logger = logging.getLogger(__name__)

class ConstraintService:
    def __init__(self, llm_service: LLMService, schema_store: SchemaStore):
        self.llm = llm_service
        self.schema_store = schema_store
        self.resources_dir = Path(__file__).parent.parent / "resources"
    
    def _load_template(self) -> str:
        """加载提示词模板"""
        template_path = self.resources_dir / "prompts" / "constraint_analysis.md"
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    async def parse_constraints(
        self,
        query: str,
        tables: List[str]
    ) -> Dict[str, Any]:
        """解析查询中的约束条件"""
        try:
            # 获取相关表的详细信息
            table_schemas = await self.schema_store.get_tables_schema(tables)
            
            # 构建提示词
            template = self._load_template()
            prompt = template.format(
                table_schemas=table_schemas,
                user_query=query
            )
            
            # 调用LLM
            result = await self.llm.generate(prompt)
            logger.info(f"LLM返回的约束分析结果: {result}")
            
            try:
                response = json.loads(result)
                if not isinstance(response, dict):
                    raise ValueError("LLM返回的结果格式不正确，应该是字典")
                
                # 验证每个表的约束条件格式
                for table, constraints in response.items():
                    if not isinstance(constraints, dict):
                        raise ValueError(f"表 {table} 的约束条件不是字典格式")
                    
                    # 确保所有必需的约束类型都存在
                    required_keys = ["where", "group_by", "having", "order_by", "limit"]
                    for key in required_keys:
                        if key not in constraints:
                            constraints[key] = [] if key != "limit" else None
                
                return response
            except json.JSONDecodeError as e:
                logger.error(f"解析LLM返回的JSON失败: {result}", exc_info=True)
                raise
        except Exception as e:
            logger.error(f"约束解析失败: {str(e)}", exc_info=True)
            raise 