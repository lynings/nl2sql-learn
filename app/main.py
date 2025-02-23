from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.postgresql import get_db
from app.services.factory import create_services
from app.models.request import QueryRequest
from app.models.response import SQLResponse, QueryResult
from sqlalchemy import text
import logging
import uvicorn
from app.utils.helpers import log_api_call

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# 创建服务实例
try:
    sql_generator = create_services()
    logger.info("服务实例创建成功")
except Exception as e:
    logger.error(f"服务实例创建失败: {str(e)}")
    raise

app = FastAPI(
    title="Text2SQL API",
    description="智能SQL生成服务",
    version="1.0.0"
)

@app.get("/")
async def health_check():
    """健康检查接口"""
    return {"status": "healthy", "message": "Text2SQL service is running"}

@app.post("/generate-sql", response_model=SQLResponse)
async def generate_sql(request: QueryRequest):
    """生成SQL查询语句"""
    try:
        logger.info(f"收到查询请求: {request.text}")
        result = await sql_generator.generate_sql(request.text)
        log_api_call("generate_sql", request.text, result)
        
        logger.info(f"生成的SQL: {result['sql']}")
        return result
    except Exception as e:
        logger.error(f"生成SQL时发生错误: {str(e)}", exc_info=True)
        log_api_call("generate_sql", request.text, error=e)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/execute-sql", response_model=QueryResult)
async def execute_sql(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """生成并执行SQL查询"""
    try:
        # 生成SQL
        result = await sql_generator.generate_sql(request.text)
        sql = result["sql"]
        
        # 执行查询
        query_result = await db.execute(text(sql))
        rows = query_result.fetchall()
        await db.commit()
        
        # 转换结果
        results = [dict(row._mapping) for row in rows]
        
        return {
            "sql": sql,
            "results": results,
            "intent": result["intent"],
            "context": result["context"]
        }
    except Exception as e:
        logger.error(f"执行SQL时发生错误: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 