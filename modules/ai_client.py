"""
AI 客户端 - 支持多种 AI 服务商
支持: Claude (Anthropic), MiniMax, OpenAI 等
"""
import os
import json
import requests
from typing import Dict, Optional


class AIClient:
    """通用 AI 客户端"""

    def __init__(self, provider: str = None):
        """
        初始化 AI 客户端

        Args:
            provider: AI 服务商，可选 'anthropic', 'minimax', 'openai'
                     如果不指定，自动检测环境变量
        """
        self.provider = self._detect_provider(provider)
        self.client = None

        if self.provider == 'anthropic':
            self._init_anthropic()
        elif self.provider == 'minimax':
            self._init_minimax()
        elif self.provider == 'openai':
            self._init_openai()

    def _detect_provider(self, provider: str = None) -> str:
        """自动检测 AI 服务商"""
        if provider:
            return provider.lower()

        # 按优先级检测
        if os.getenv("MINIMAX_API_KEY"):
            return "minimax"
        elif os.getenv("OPENAI_API_KEY"):
            return "openai"
        elif os.getenv("ANTHROPIC_API_KEY"):
            return "anthropic"

        return "none"

    def _init_anthropic(self):
        """初始化 Anthropic 客户端"""
        try:
            from anthropic import Anthropic
            self.client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        except ImportError:
            print("请安装 anthropic: pip install anthropic")

    def _init_minimax(self):
        """初始化 MiniMax 客户端 - 使用 REST API"""
        self.api_key = os.getenv("MINIMAX_API_KEY")
        self.base_url = os.getenv("MINIMAX_BASE_URL", "https://api.minimax.chat/v1")

    def _init_openai(self):
        """初始化 OpenAI 客户端"""
        try:
            import openai
            openai.api_key = os.getenv("OPENAI_API_KEY")
            if os.getenv("OPENAI_BASE_URL"):
                openai.base_url = os.getenv("OPENAI_BASE_URL")
            self.client = openai
        except ImportError:
            print("请安装 openai: pip install openai")

    def chat(self, messages: list, model: str = None, **kwargs) -> str:
        """
        发送聊天请求

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            model: 模型名称
            **kwargs: 其他参数

        Returns:
            AI 响应文本
        """
        if self.provider == 'anthropic':
            return self._chat_anthropic(messages, model, **kwargs)
        elif self.provider == 'minimax':
            return self._chat_minimax(messages, model, **kwargs)
        elif self.provider == 'openai':
            return self._chat_openai(messages, model, **kwargs)
        else:
            return json.dumps({"error": "未配置 AI API"})

    def _chat_anthropic(self, messages: list, model: str = None, **kwargs) -> str:
        """Anthropic Chat"""
        if not model:
            model = "claude-3-5-sonnet-20241022"

        try:
            # 转换消息格式
            content = "\n".join([f"{m['role']}: {m['content']}" for m in messages])

            response = self.client.messages.create(
                model=model,
                max_tokens=kwargs.get("max_tokens", 4000),
                messages=[{"role": "user", "content": content}]
            )
            return response.content[0].text
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _chat_minimax(self, messages: list, model: str = None, **kwargs) -> str:
        """MiniMax Chat"""
        if not model:
            # MiniMax 模型列表
            model = os.getenv("MINIMAX_MODEL", "abab6.5s-chat")

        # 获取 Group ID
        group_id = os.getenv("MINIMAX_GROUP_ID", "")

        url = f"{self.base_url}/text/chatcompletion_v2"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        # 转换消息格式
        formatted_messages = []
        for m in messages:
            formatted_messages.append({
                "role": m["role"],
                "text": m["content"]
            })

        data = {
            "model": model,
            "messages": formatted_messages,
            "max_tokens": kwargs.get("max_tokens", 4096),
            "temperature": kwargs.get("temperature", 0.7)
        }

        if group_id:
            data["group_id"] = group_id

        try:
            response = requests.post(url, headers=headers, json=data, timeout=60)
            result = response.json()

            if "choices" in result and len(result["choices"]) > 0:
                return result["choices"][0]["message"]["text"]
            else:
                return json.dumps(result)
        except Exception as e:
            return json.dumps({"error": str(e)})

    def _chat_openai(self, messages: list, model: str = None, **kwargs) -> str:
        """OpenAI Chat"""
        if not model:
            model = os.getenv("OPENAI_MODEL", "gpt-4")

        try:
            response = self.client.ChatCompletion.create(
                model=model,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", 4000),
                temperature=kwargs.get("temperature", 0.7)
            )
            return response.choices[0].message.content
        except Exception as e:
            return json.dumps({"error": str(e)})

    def is_available(self) -> bool:
        """检查 AI 客户端是否可用"""
        return self.provider != "none" and (
            os.getenv("ANTHROPIC_API_KEY") or
            os.getenv("MINIMAX_API_KEY") or
            os.getenv("OPENAI_API_KEY")
        )

    def get_provider_name(self) -> str:
        """获取当前服务商名称"""
        names = {
            "anthropic": "Claude (Anthropic)",
            "minimax": "MiniMax",
            "openai": "OpenAI",
            "none": "未配置"
        }
        return names.get(self.provider, self.provider)


# 便捷函数
def create_ai_client(provider: str = None) -> AIClient:
    """创建 AI 客户端"""
    return AIClient(provider)
