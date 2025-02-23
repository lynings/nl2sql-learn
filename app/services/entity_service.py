from typing import Dict, List, Any
import logging
import json
from pathlib import Path
from app.services.llm_service import LLMService
from app.database.schema_store import SchemaStore

logger = logging.getLogger(__name__)

class EntityService:
    def __init__(self, llm_service: LLMService, schema_store: SchemaStore):
        self.llm = llm_service
        self.schema_store = schema_store
        self.resources_dir = Path(__file__).parent.parent / "resources"
        logger.info("实体服务初始化完成")
    
    def _load_template(self, template_type: str) -> str:
        """加载提示词模板"""
        try:
            template_files = {
                "table": "prompts/table_extraction.md",
                "field": "prompts/field_extraction.md"
            }
            
            if template_type not in template_files:
                raise ValueError(f"未知的模板类型: {template_type}")
            
            file_path = self.resources_dir / template_files[template_type]
            if not file_path.exists():
                raise FileNotFoundError(f"模板文件不存在: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                template = f.read().strip()
            logger.info(f"已加载模板 {template_type}: {template[:100]}...")
            return template
        except Exception as e:
            logger.error(f"加载{template_type}模板失败: {str(e)}", exc_info=True)
            raise
    
    async def extract_entities(self, query: str) -> Dict[str, Any]:
        """分两步提取实体信息"""
        try:
            # 1. 识别涉及的表
            tables = await self._extract_tables(query)
            logger.info(f"识别到的表: {tables}")
            
            # 2. 识别涉及的字段
            table_to_fields = await self._extract_fields(query, tables)
            logger.info(f"识别到的字段: {table_to_fields}")
            
            return {
                "tables": tables,
                "fields": table_to_fields
            }
        except Exception as e:
            logger.error(f"实体提取失败: {str(e)}", exc_info=True)
            raise
    
    async def _extract_tables(self, query: str) -> List[str]:
        """识别查询涉及的表"""
        try:
            # 获取所有可用表的信息
            available_tables = await self.schema_store.get_all_tables_info()
            logger.info(f"获取到的表信息: {available_tables}")
            
            # 构建提示词
            template = self._load_template("table")
            prompt = template.format(
                available_tables=available_tables,
                user_query=query
            )
            logger.info(f"生成的表识别提示词: {prompt}")
            
            # 调用LLM
            result = await self.llm.generate(prompt)
            logger.info(f"LLM返回的表识别结果: {result}")
            
            # 解析JSON响应
            try:
                response = json.loads(result)
                if not isinstance(response, list):
                    raise ValueError("LLM返回的结果格式不正确，应该是字符串列表")
                return response
            except json.JSONDecodeError as e:
                logger.error(f"解析LLM返回的JSON失败: {result}", exc_info=True)
                raise
            
        except Exception as e:
            logger.error(f"表识别失败: {str(e)}", exc_info=True)
            raise
    
    async def _extract_fields(self, query: str, tables: List[str]) -> Dict[str, List[str]]:
        """识别查询涉及的字段"""
        # 获取相关表的详细信息
        table_schemas = await self.schema_store.get_tables_schema(tables)
        
        # 构建提示词
        template = self._load_template("field")
        prompt = template.format(
            table_schemas=table_schemas,
            user_query=query
        )
        
        # 调用LLM
        result = await self.llm.generate(prompt)
        logger.info(f"LLM返回的字段识别结果: {result}")
        
        try:
            response = json.loads(result)
            if not isinstance(response, dict):
                raise ValueError("LLM返回的结果格式不正确，应该是字典")
            # 验证每个表的字段是否为列表
            for table, fields in response.items():
                if not isinstance(fields, list):
                    raise ValueError(f"表 {table} 的字段不是列表格式")
            return response
        except json.JSONDecodeError as e:
            logger.error(f"解析LLM返回的JSON失败: {result}", exc_info=True)
            raise 