"""
Claude API 客户端模块
兼容多种 AI 服务商: Claude, MiniMax, OpenAI
"""
import os
import json
from typing import Dict
from ai_client import AIClient


class ClaudeClient:
    """AI 客户端 - 统一接口"""

    def __init__(self):
        self.client = AIClient()

    def analyze_sql(self, sql: str) -> dict:
        """分析 SQL 查询"""
        prompt = f"""你是一个资深的 Oracle DBA 和 SQL 性能优化专家。请分析以下 SQL 查询，识别潜在的性能问题。

SQL 语句：
{sql}

请按以下 JSON 格式返回分析结果：
{{
    "issues": [
        {{
            "severity": "紧急|建议|可选",
            "type": "问题类型",
            "description": "问题描述",
            "location": "问题位置"
        }}
    ],
    "complexity": {{
        "join_count": 数字,
        "subquery_level": 数字,
        "where_complexity": "低|中|高"
    }},
    "summary": "总体评估摘要"
}}
"""
        return self._call_ai(prompt)

    def explain_plan(self, plan: str, sql: str = "") -> dict:
        """解读执行计划"""
        prompt = f"""你是一个资深的 Oracle DBA。请解读以下执行计划，识别性能瓶颈。

SQL 语句：
{sql}

执行计划：
{plan}

请按以下 JSON 格式返回分析结果：
{{
    "bottlenecks": [
        {{
            "operation": "操作名称",
            "object": "表/索引对象",
            "cost": "成本值",
            "cardinality": "基数",
            "problem": "问题描述",
            "severity": "紧急|建议|可选"
        }}
    ],
    "warnings": ["警告信息列表"],
    "summary": "执行计划总体评估"
}}
"""
        return self._call_ai(prompt)

    def generate_optimizer_suggestions(self, sql: str, issues: list) -> dict:
        """生成优化建议"""
        issues_text = "\n".join([f"- {i['type']}: {i['description']}" for i in issues])

        prompt = f"""你是一个资深的 Oracle DBA 和 SQL 性能优化专家。请基于以下分析的问题，生成具体的优化建议。

SQL 语句：
{sql}

已识别的问题：
{issues_text}

请按以下 JSON 格式返回优化建议：
{{
    "suggestions": [
        {{
            "severity": "🔴 紧急|🟡 建议|🟢 可选",
            "title": "建议标题",
            "description": "详细描述",
            "method": "优化方法",
            "expected_benefit": "预期收益",
            "risk": "风险提示（如果没有则为空）",
            "reference": "Oracle 官方最佳实践引用"
        }}
    ]
}}
"""
        return self._call_ai(prompt)

    def rewrite_sql(self, sql: str, suggestions: list) -> dict:
        """SQL 改写"""
        suggestions_text = "\n".join([
            f"- {s['title']}: {s['method']}"
            for s in suggestions
        ])

        prompt = f"""你是一个资深的 Oracle DBA 和 SQL 性能优化专家。请根据以下优化建议，改写 SQL 语句。

原始 SQL：
{sql}

优化建议：
{suggestions_text}

请按以下 JSON 格式返回改写结果：
{{
    "optimized_sql": "优化后的SQL（格式化后的可执行SQL）",
    "differences": [
        {{
            "line": "行号",
            "original": "原始内容",
            "optimized": "优化后内容",
            "reason": "改写理由"
        }}
    ],
    "alternatives": [
        {{
            "sql": "备选优化SQL",
            "description": "方案描述"
        }}
    ]
}}
"""
        return self._call_ai(prompt)

    def _call_ai(self, prompt: str) -> dict:
        """调用 AI API"""
        if not self.client.is_available():
            return {"error": "未配置 AI API，请设置 MINIMAX_API_KEY 或 ANTHROPIC_API_KEY"}

        try:
            messages = [{"role": "user", "content": prompt}]
            response = self.client.chat(messages)
            return self._parse_json_response(response)
        except Exception as e:
            return {"error": str(e)}

    def _parse_json_response(self, response: str) -> dict:
        """解析 JSON 响应"""
        import re

        # 尝试提取 JSON 块
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # 如果无法解析，返回原始响应
        return {"raw_response": response}

    def is_available(self) -> bool:
        """检查是否可用"""
        return self.client.is_available()

    def get_provider_name(self) -> str:
        """获取当前服务商"""
        return self.client.get_provider_name()
