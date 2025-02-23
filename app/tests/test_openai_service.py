import asyncio
import pytest
from app.services.openai_service import openai_service

@pytest.mark.asyncio
async def test_sql_generation():
    test_cases = [
        "查询所有用户的姓名和邮箱",
        "统计每个部门的员工数量和平均工资",
        "找出最近30天内登录次数最多的前10个用户",
    ]
    
    for query in test_cases:
        print(f"\n测试查询: {query}")
        try:
            sql = await openai_service.generate_sql(query)
            print(f"生成的SQL:\n{sql}")
            assert sql.strip(), "SQL 不应为空"
            assert "SELECT" in sql.upper(), "SQL 应该包含 SELECT 语句"
        except Exception as e:
            pytest.fail(f"测试失败: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_sql_generation()) 