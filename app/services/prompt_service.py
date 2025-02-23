from typing import Dict, List, Any
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

class PromptService:
    def __init__(self):
        self.resources_dir = Path(__file__).parent.parent / "resources"
    
    def _load_prompt_template(self) -> str:
        """加载 prompt 模板"""
        template_path = self.resources_dir / "prompts" / "sql_generation.md"
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _load_table_ddl(self, table_name: str) -> str:
        """加载表 DDL"""
        ddl_path = self.resources_dir / "schemas" / f"{table_name}.md"
        if not ddl_path.exists():
            logger.warning(f"表结构文件不存在: {ddl_path}")
            return ""
        
        with open(ddl_path, 'r', encoding='utf-8') as f:
            content = f.read()
            # 提取 DDL 部分
            start = content.find("```sql")
            end = content.find("```", start + 6)
            if start != -1 and end != -1:
                return content[start+6:end].strip()
            return ""
    
    def generate_prompt(
        self,
        query: str,
        entities: Dict[str, List[str]],
        constraints: Dict[str, Any],
        business_rules: List[str]
    ) -> str:
        """
        生成完整的 prompt
        """
        # 收集相关表的 DDL
        table_ddls = []
        for table in entities["tables"]:
            ddl = self._load_table_ddl(table)
            if ddl:
                table_ddls.append(ddl)
        
        # 格式化查询字段
        query_fields = []
        for table, fields in entities["fields"].items():
            for field in fields:
                query_fields.append(f"{table}.{field}")
        
        # 格式化约束条件
        formatted_constraints = []
        for table, table_constraints in constraints.items():
            table_formatted = []
            if table_constraints.get("where"):
                table_formatted.append(f"WHERE 条件：{', '.join(table_constraints['where'])}")
            if table_constraints.get("group_by"):
                table_formatted.append(f"分组条件：{', '.join(table_constraints['group_by'])}")
            if table_constraints.get("having"):
                table_formatted.append(f"HAVING 条件：{', '.join(table_constraints['having'])}")
            if table_constraints.get("order_by"):
                table_formatted.append(f"排序条件：{', '.join(table_constraints['order_by'])}")
            if table_constraints.get("limit"):
                table_formatted.append(f"限制条数：{table_constraints['limit']}")
            
            if table_formatted:
                formatted_constraints.append(f"表 {table} 的约束条件：")
                formatted_constraints.extend([f"  - {c}" for c in table_formatted])
        
        # 填充模板
        template = self._load_prompt_template()
        prompt = template.format(
            table_ddl="\n\n".join(table_ddls),
            query_fields="\n".join(query_fields),
            constraints="\n".join(formatted_constraints),
            business_rules="\n".join(business_rules),
            user_query=query
        )
        
        logger.info(f"生成的完整 prompt:\n{prompt}")
        return prompt

    def generate_sql_prompt(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> str:
        """生成SQL转换提示词"""
        
        # 构建表结构描述
        table_desc = self._format_table_info(context["tables"])
        
        # 构建字段描述
        field_desc = self._format_field_info(context["fields"])
        
        # 构建业务规则
        rules_desc = self._format_business_rules(context["business_rules"])
        
        prompt = f"""作为一个PostgreSQL专家，请将以下自然语言转换为SQL查询。

表结构信息：
{table_desc}

字段信息：
{field_desc}

业务规则：
{rules_desc}

查询类型：{context["query_type"]}
时间范围：{context["time_range"]}
聚合操作：{context["aggregation"]}

用户查询：{query}

要求：
1. 只返回SQL语句，不要包含任何解释
2. 使用标准PostgreSQL语法
3. 使用适当的表别名
4. 对复杂部分添加注释
5. 确保遵循业务规则
"""
        return prompt
    
    def _format_table_info(self, tables: List[Dict]) -> str:
        return "\n".join([
            f"- {table['name']}: {table['description']}"
            for table in tables
        ])
    
    def _format_field_info(self, fields: List[Dict]) -> str:
        return "\n".join([
            f"- {field['table']}.{field['name']}: {field['description']}"
            for field in fields
        ])
    
    def _format_business_rules(self, rules: List[str]) -> str:
        return "\n".join([f"- {rule}" for rule in rules]) 