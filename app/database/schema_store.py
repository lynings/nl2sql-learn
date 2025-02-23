from typing import List, Dict, Any
from sqlalchemy import MetaData, inspect
from sqlalchemy.ext.asyncio import AsyncEngine
import json
import os
from app.config import settings
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class SchemaStore:
    def __init__(self, engine: AsyncEngine):
        self.engine = engine
        self.metadata = MetaData()
        self.cache = {}
        self.resources_dir = Path(__file__).parent.parent / "resources"
        self.descriptions_dir = self.resources_dir / "schemas" / "descriptions"
        self.ddl_dir = self.resources_dir / "schemas" / "ddl"
        # 加载业务规则配置
        self.business_rules = self._load_business_rules()
        
    def _load_business_rules(self) -> Dict[str, List[str]]:
        """加载业务规则配置文件"""
        rules_path = os.path.join(settings.CONFIG_DIR, "business_rules.json")
        try:
            with open(rules_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
    
    async def get_relevant_tables(
        self,
        entities: List[str],
        query_text: str
    ) -> List[Dict[str, str]]:
        """获取相关的表结构信息"""
        if not self.cache.get('tables'):
            # 使用 SQLAlchemy inspect 获取数据库表信息
            async with self.engine.connect() as conn:
                inspector = inspect(conn)
                tables = []
                for table_name in await inspector.get_table_names():
                    comment = await inspector.get_table_comment(table_name)
                    tables.append({
                        "name": table_name,
                        "description": comment.get("text", ""),
                        "columns": await inspector.get_columns(table_name)
                    })
                self.cache['tables'] = tables
        
        # 根据实体和查询文本过滤相关表
        relevant_tables = []
        for table in self.cache['tables']:
            if any(entity.lower() in table['name'].lower() for entity in entities) or \
               any(entity.lower() in table['description'].lower() for entity in entities) or \
               table['name'].lower() in query_text.lower():
                relevant_tables.append({
                    "name": table['name'],
                    "description": table['description']
                })
        
        return relevant_tables
    
    async def get_relevant_fields(
        self,
        tables: List[Dict[str, str]],
        query_text: str
    ) -> List[Dict[str, str]]:
        """获取相关的字段信息"""
        relevant_fields = []
        async with self.engine.connect() as conn:
            inspector = inspect(conn)
            for table in tables:
                columns = await inspector.get_columns(table['name'])
                for column in columns:
                    # 获取字段注释
                    comment = await self._get_column_comment(
                        inspector,
                        table['name'],
                        column['name']
                    )
                    if self._is_field_relevant(column['name'], comment, query_text):
                        relevant_fields.append({
                            "table": table['name'],
                            "name": column['name'],
                            "type": str(column['type']),
                            "description": comment or ""
                        })
        
        return relevant_fields
    
    async def get_business_rules(
        self,
        entities: List[str]
    ) -> List[str]:
        """获取相关的业务规则"""
        rules = []
        for entity in entities:
            if entity in self.business_rules:
                rules.extend(self.business_rules[entity])
        return rules
    
    async def _get_column_comment(
        self,
        inspector,
        table_name: str,
        column_name: str
    ) -> str:
        """获取字段注释"""
        try:
            return await inspector.get_column_comment(
                table_name,
                column_name
            )
        except:
            return ""
    
    def _is_field_relevant(
        self,
        field_name: str,
        comment: str,
        query_text: str
    ) -> bool:
        """判断字段是否相关"""
        query_terms = query_text.lower().split()
        field_terms = field_name.lower().split('_')
        comment_terms = comment.lower().split() if comment else []
        
        # 检查字段名或注释是否与查询相关
        return any(
            term in query_terms
            for term in field_terms + comment_terms
        )

    async def get_all_tables_info(self) -> str:
        """获取所有表的基本描述信息"""
        try:
            tables_info = []
            
            if not self.descriptions_dir.exists():
                raise FileNotFoundError(f"表描述目录不存在: {self.descriptions_dir}")
            
            # 读取所有表描述文件
            for file_path in self.descriptions_dir.glob("*.md"):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 提取表名（文件名去掉.md后缀）
                table_name = file_path.stem
                
                # 提取描述（第一段内容）
                description = ""
                lines = content.split("\n")
                if len(lines) > 2:  # 跳过标题行
                    description = lines[2].strip()
                
                info = f"- {table_name}: {description}"
                tables_info.append(info.strip())
            
            result = "\n\n".join(tables_info)
            logger.info(f"从描述文件获取到的表信息: {result}")
            return result
            
        except Exception as e:
            logger.error(f"获取表信息失败: {str(e)}", exc_info=True)
            raise
    
    async def get_tables_schema(self, tables: List[str]) -> str:
        """获取指定表的DDL和字段信息"""
        try:
            schemas = []
            
            for table in tables:
                file_path = self.ddl_dir / f"{table}.md"
                if not file_path.exists():
                    logger.warning(f"表DDL文件不存在: {file_path}")
                    continue
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                schemas.append(content)
            
            return "\n\n".join(schemas)
        except Exception as e:
            logger.error(f"获取表结构失败: {str(e)}", exc_info=True)
            raise
    
    async def get_business_rules(self, tables: List[str]) -> List[str]:
        """获取指定表的业务规则"""
        try:
            rules = []
            
            for table in tables:
                file_path = self.ddl_dir / f"{table}.md"
                if not file_path.exists():
                    continue
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # 提取业务规则部分
                if "## 业务规则" in content:
                    rules_section = content.split("## 业务规则")[1].strip()
                    table_rules = [
                        f"{table}: {r.lstrip('123456789.').strip()}"
                        for r in rules_section.split("\n")
                        if r.strip() and r.strip()[0].isdigit()
                    ]
                    rules.extend(table_rules)
            
            return rules
        except Exception as e:
            logger.error(f"获取业务规则失败: {str(e)}", exc_info=True)
            raise

# 创建示例业务规则文件
EXAMPLE_BUSINESS_RULES = {
    "user": [
        "用户邮箱必须唯一",
        "密码必须经过加密存储",
        "用户状态包括：活跃、禁用、待验证"
    ],
    "order": [
        "订单状态变更需要记录历史",
        "订单金额必须大于0",
        "订单完成后不可修改"
    ],
    "product": [
        "产品价格必须大于0",
        "产品库存不能为负",
        "产品状态包括：在售、下架、缺货"
    ]
}

def init_business_rules():
    """初始化业务规则配置文件"""
    config_dir = settings.CONFIG_DIR
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    
    rules_path = os.path.join(config_dir, "business_rules.json")
    if not os.path.exists(rules_path):
        with open(rules_path, 'w', encoding='utf-8') as f:
            json.dump(EXAMPLE_BUSINESS_RULES, f, ensure_ascii=False, indent=2) 