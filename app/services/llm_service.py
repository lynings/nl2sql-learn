from typing import Optional, Dict, Any
import aiohttp
import json
import logging
from app.config import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

class LLMService:
    def __init__(self):
        self.client = OpenAI()
        self.base_url = settings.OLLAMA_BASE_URL
        self.model = settings.OLLAMA_MODEL
        logger.info(f"初始化 LLM 服务: base_url={self.base_url}, model={self.model}")
    
    async def generate(self, prompt: str) -> str:
        """调用LLM生成响应"""
        try:
            # 调用API
            response = await self._call_api(prompt)
            
            # 提取JSON响应
            result = self._extract_json(response)
            
            # 验证JSON格式
            if not self._validate_json_response(result, prompt):
                raise ValueError("LLM响应格式不正确")
            
            return result
            
        except Exception as e:
            logger.error(f"LLM生成失败: {str(e)}", exc_info=True)
            raise
    
    def _validate_json_response(self, response: str, prompt: str) -> bool:
        """验证JSON响应格式"""
        try:
            # 解析JSON
            data = json.loads(response)
            
            # 根据prompt类型判断需要验证的字段
            if "表识别提示词" in prompt:
                return self._validate_table_extraction(data)
            elif "字段识别提示词" in prompt:
                return self._validate_field_extraction(data)
            elif "约束分析提示词" in prompt:
                return self._validate_constraint_analysis(data)
            elif "SQL Generation" in prompt:
                return self._validate_sql_generation(data)
            else:
                logger.warning(f"未知的prompt类型，跳过验证: {prompt[:100]}")
                return True
                
        except json.JSONDecodeError:
            logger.error("响应不是有效的JSON格式")
            return False
        except Exception as e:
            logger.error(f"验证JSON响应时发生错误: {str(e)}")
            return False
    
    def _validate_table_extraction(self, data: Dict) -> bool:
        """验证表识别结果"""
        if not isinstance(data, list):
            return False
        return True
    
    def _validate_field_extraction(self, data: Dict) -> bool:
        """验证字段识别结果"""
        if not isinstance(data, dict):
            return False
        # 检查每个值是否为字符串列表
        for value in data.values():
            if not isinstance(value, list):
                return False
            if not all(isinstance(x, str) for x in value):
                return False
        return True
    
    def _validate_constraint_analysis(self, data: Dict) -> bool:
        """验证约束分析结果"""
        if not isinstance(data, dict):
            return False
        
        # 检查每个表的约束条件格式
        for table_constraints in data.values():
            if not isinstance(table_constraints, dict):
                return False
            
            # 检查必需的约束类型
            required_keys = ["where", "group_by", "having", "order_by", "limit"]
            for key in required_keys:
                if key not in table_constraints:
                    return False
                
                # 检查约束值的类型
                if key == "limit":
                    if not isinstance(table_constraints[key], (int, type(None))):
                        return False
                else:
                    if not isinstance(table_constraints[key], list):
                        return False
        return True
    
    def _validate_sql_generation(self, data: Dict) -> bool:
        """验证SQL生成结果"""
        if not isinstance(data, dict):
            return False
        if "sql" not in data:
            return False
        if "description" not in data:
            return False
        return True

    async def _call_api(self, prompt: str):
        """
        使用 Ollama API 生成响应
        
        Args:
            prompt: 提示词
            
        Returns:
            str: 生成的响应
        """
        try:
            # 构建完整的提示词，要求返回 JSON 格式
            full_prompt = f"""请将以下自然语言转换为PostgreSQL查询语句。

用户查询：{prompt}

要求：
1. 返回JSON格式，包含以下字段：
   - sql: 生成的SQL语句
   - description: SQL的简要说明（可选）
2. SQL语句要求：
   - 使用标准PostgreSQL语法
   - 使用适当的表别名
   - 对复杂部分添加注释

只返回JSON格式的结果，不要包含其他说明文字。
"""
            logger.debug(f"发送请求到 Ollama API, prompt 长度: {len(prompt)}")
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": False
                    }
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Ollama API 返回错误: status={response.status}, error={error_text}")
                        raise Exception(f"Ollama API error: {error_text}")
                    
                    result = await response.json()
                    logger.debug(f"收到 Ollama API 响应: {json.dumps(result, ensure_ascii=False)[:200]}...")
                    
                    if "error" in result:
                        logger.error(f"Ollama API 返回错误: {result['error']}")
                        raise Exception(f"Ollama API error: {result['error']}")
                    
                    if "response" not in result:
                        logger.error(f"Ollama API 响应格式错误: {json.dumps(result, ensure_ascii=False)}")
                        raise Exception("Invalid response format from Ollama API")
                    
                    return result["response"]
                    
        except aiohttp.ClientError as e:
            logger.error(f"请求 Ollama API 时发生网络错误: {str(e)}", exc_info=True)
            raise Exception(f"Network error when calling Ollama API: {str(e)}")
        except json.JSONDecodeError as e:
            logger.error(f"解析 Ollama API 响应时发生错误: {str(e)}", exc_info=True)
            raise Exception(f"Failed to parse Ollama API response: {str(e)}")
        except Exception as e:
            logger.error(f"调用 Ollama API 时发生未知错误: {str(e)}", exc_info=True)
            raise

    def _extract_json(self, response: str) -> str:
        """
        提取 JSON 响应
        
        Args:
            response: 响应文本
            
        Returns:
            str: 提取的 JSON 字符串
        """
        # 处理可能包含的 markdown 代码块
        if "```json" in response:
            # 提取 json 代码块中的内容
            start = response.find("```json\n") + 7
            end = response.find("```", start)
            if end == -1:  # 如果没有找到结束标记
                end = len(response)
            json_str = response[start:end].strip()
        else:
            json_str = response.strip()
        
        return json_str

llm_service = LLMService() 