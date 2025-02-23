from pydantic import BaseModel
from typing import List, Any, Optional

class SQLResponse(BaseModel):
    sql: str
    # intent: str
    # context: dict

class QueryResult(BaseModel):
    sql: str
    results: List[dict]
    intent: str
    context: dict 