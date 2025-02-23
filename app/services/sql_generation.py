from typing import Dict, Any
import logging
from app.services.llm_service import LLMService
from app.services.entity_service import EntityService
from app.services.constraint_service import ConstraintService
from app.services.prompt_service import PromptService
from app.database.schema_store import SchemaStore

logger = logging.getLogger(__name__)

class SQLGenerator:
    def __init__(
        self,
        llm_service: LLMService,
        entity_service: EntityService,
        constraint_service: ConstraintService,
        prompt_service: PromptService,
        schema_store: SchemaStore
    ):
        self.llm = llm_service
        self.entity_service = entity_service
        self.constraint_service = constraint_service
        self.prompt_service = prompt_service
        self.schema_store = schema_store
        logger.info("SQL生成器初始化完成")
    
    async def generate_sql(self, query: str) -> Dict[str, Any]:
        """生成SQL查询"""
        try:
            # 1. 实体抽取
            logger.info(f"开始实体抽取: {query}")
            try:
                entities = await self.entity_service.extract_entities(query)
                logger.info(f"实体抽取结果: {entities}")
            except Exception as e:
                logger.error("实体抽取失败", exc_info=True)
                raise Exception(f"实体抽取失败: {str(e)}")
            
            # 2. 约束解析
            logger.info("开始约束解析")
            try:
                constraints = await self.constraint_service.parse_constraints(
                    query,
                    entities["tables"]
                )
                logger.info(f"约束解析结果: {constraints}")
            except Exception as e:
                logger.error("约束解析失败", exc_info=True)
                raise Exception(f"约束解析失败: {str(e)}")
            
            # 3. 获取业务规则
            business_rules = await self.schema_store.get_business_rules(
                entities=entities["tables"]
            )
            
            # 4. 生成完整 prompt
            prompt = self.prompt_service.generate_prompt(
                query=query,
                entities=entities,
                constraints=constraints,
                business_rules=business_rules
            )
            
            # 5. 生成SQL
            logger.info("开始生成SQL")
            sql = await self.llm.generate(prompt)
            logger.info(f"生成的SQL: {sql}")
            
            return {
                "sql": sql,
                "entities": entities,
                "constraints": constraints
            }
        except Exception as e:
            logger.error(f"生成SQL过程中发生错误: {str(e)}", exc_info=True)
            raise 