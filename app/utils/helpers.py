import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

__all__ = ['log_api_call']  # 明确指定导出的函数

def log_api_call(func_name: str, input_data: Any, output_data: Any = None, error: Exception = None):
    """记录 API 调用的详细信息"""
    try:
        log_data = {
            "function": func_name,
            "input": input_data,
            "output": output_data,
            "error": str(error) if error else None
        }
        logger.info(f"API调用详情: {json.dumps(log_data, ensure_ascii=False, indent=2)}")
    except Exception as e:
        logger.error(f"记录API调用信息时发生错误: {str(e)}") 