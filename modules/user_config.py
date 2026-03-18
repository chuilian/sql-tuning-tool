"""
用户配置管理模块
使用 Streamlit session_state 存储，仅当前会话有效
"""
import os
import streamlit as st

# Session state key
CONFIG_KEY = "user_api_config"


def get_user_api_keys() -> dict:
    """获取用户配置的 API 密钥"""
    if CONFIG_KEY not in st.session_state:
        st.session_state[CONFIG_KEY] = {
            "minimax": os.getenv("MINIMAX_API_KEY", ""),
            "anthropic": os.getenv("ANTHROPIC_API_KEY", ""),
            "openai": os.getenv("OPENAI_API_KEY", "")
        }
    return st.session_state[CONFIG_KEY]


def save_user_api_key(provider: str, api_key: str):
    """保存用户 API 密钥"""
    if CONFIG_KEY not in st.session_state:
        st.session_state[CONFIG_KEY] = {"minimax": "", "anthropic": "", "openai": ""}

    key_name = {
        "minimax": "MINIMAX_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY"
    }.get(provider.lower(), "")

    if key_name:
        st.session_state[CONFIG_KEY][provider.lower()] = api_key
        os.environ[key_name] = api_key


def apply_user_env():
    """应用用户配置到环境变量"""
    config = get_user_api_keys()
    for key, value in config.items():
        key_name = {
            "minimax": "MINIMAX_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY"
        }.get(key, "")
        if key_name and value:
            os.environ[key_name] = value


# 兼容旧API
def load_user_config():
    """加载配置（兼容旧API）"""
    return get_user_api_keys()


def save_user_config(config: dict):
    """保存配置（兼容旧API）"""
    for key, value in config.items():
        provider = key.replace("API_KEY", "").lower()
        save_user_api_key(provider, value)


def get_user_api_keys_old() -> dict:
    """获取API密钥（兼容旧API）"""
    return get_user_api_keys()


# 初始化时应用环境变量
apply_user_env()
