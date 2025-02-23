from openai import AsyncOpenAI
from typing import Optional
from app.config import settings

class OpenAIService:
    def __init__(self):
        self.client = AsyncOpenAI(
            # api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE  # 可以设置为 Azure OpenAI 或其他兼容接口
        )
        self.model = settings.OPENAI_MODEL_NAME
    
    async def generate_sql(
        self,
        query: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        使用 OpenAI API 将自然语言转换为 SQL 查询
        
        Args:
            query: 用户的自然语言查询
            system_prompt: 可选的系统提示词
        
        Returns:
            str: 生成的 SQL 查询语句
        """
        if system_prompt is None:
            system_prompt = """You are an expert SQL assistant that converts natural language to precise PostgreSQL queries.
            Follow these rules:
            1. Only return the SQL query without any explanation
            2. Use standard PostgreSQL syntax
            3. Add appropriate table aliases when joining tables
            4. Include comments for complex parts of the query
            """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Convert this to SQL: {query}"}
        ]
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.1,  # 降低随机性，使输出更确定
            max_tokens=500,
            response_format={"type": "text"}
        )
        
        return response.choices[0].message.content.strip()

# 创建服务实例
openai_service = OpenAIService() 