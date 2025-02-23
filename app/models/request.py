from pydantic import BaseModel, Field
from typing import Optional

class QueryRequest(BaseModel):
    text: str = Field(..., description="用户的自然语言查询")
    context_id: Optional[str] = Field(None, description="上下文ID，用于多轮对话") 