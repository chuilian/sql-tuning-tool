"""
用户配置管理模块
支持用户级别的 API 密钥配置，存储在用户本地
"""
import os
import json
from pathlib import Path

# 配置目录
CONFIG_DIR = Path.home() / ".sql-optimizer"
CONFIG_FILE = CONFIG_DIR / "config.json"


def ensure_config_dir():
    """确保配置目录存在"""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


def load_user_config() -> dict:
    """加载用户配置"""
    ensure_config_dir()
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_user_config(config: dict):
    """保存用户配置"""
    ensure_config_dir()
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def get_user_api_keys() -> dict:
    """获取用户配置的 API 密钥"""
    config = load_user_config()
    return {
        "minimax": config.get("MINIMAX_API_KEY", ""),
        "anthropic": config.get("ANTHROPIC_API_KEY", ""),
        "openai": config.get("OPENAI_API_KEY", "")
    }


def set_user_api_key(provider: str, api_key: str):
    """设置用户 API 密钥"""
    config = load_user_config()
    key_name = {
        "minimax": "MINIMAX_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "openai": "OPENAI_API_KEY"
    }.get(provider.lower(), "")

    if key_name:
        if api_key:
            config[key_name] = api_key
        else:
            config.pop(key_name, None)
        save_user_config(config)


def clear_user_config():
    """清除用户配置"""
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()


def apply_user_env():
    """将用户配置应用到当前进程环境变量"""
    config = load_user_config()
    for key, value in config.items():
        if value:  # 只设置非空值
            os.environ[key] = value
