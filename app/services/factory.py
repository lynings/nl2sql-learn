from app.database.postgresql import engine
from app.database.schema_store import SchemaStore, init_business_rules
from app.services.llm_service import LLMService
from app.services.entity_service import EntityService
from app.services.constraint_service import ConstraintService
from app.services.prompt_service import PromptService
from app.services.sql_generation import SQLGenerator

def create_services():
    """创建服务实例"""
    try:
        # 初始化业务规则
        init_business_rules()
        
        # 创建基础服务实例
        schema_store = SchemaStore(engine)
        llm_service = LLMService()
        
        # 创建依赖服务
        entity_service = EntityService(llm_service, schema_store)
        constraint_service = ConstraintService(llm_service, schema_store)
        prompt_service = PromptService()
        
        # 创建 SQL 生成器
        sql_generator = SQLGenerator(
            llm_service=llm_service,
            entity_service=entity_service,
            constraint_service=constraint_service,
            prompt_service=prompt_service,
            schema_store=schema_store
        )
        
        return sql_generator
    except Exception as e:
        raise Exception(f"创建服务实例失败: {str(e)}") 