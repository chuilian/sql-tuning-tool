"""
Supabase 客户端模块
"""
import os
from supabase import create_client, Client
from datetime import datetime


class SupabaseClient:
    """Supabase 客户端 - 用于存储分析历史"""

    def __init__(self):
        self.client: Client = None
        self._init_client()

    def _init_client(self):
        """初始化 Supabase 客户端"""
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")

        if supabase_url and supabase_key:
            try:
                self.client = create_client(supabase_url, supabase_key)
            except Exception as e:
                print(f"Supabase 初始化失败: {e}")
        else:
            print("警告: 未配置 Supabase，跳过初始化")

    def save_analysis(self, sql: str, analysis_result: dict) -> dict:
        """保存分析记录"""
        if not self.client:
            return {"success": False, "error": "Supabase 未初始化"}

        try:
            data = {
                "sql_text": sql,
                "analysis_result": analysis_result,
                "created_at": datetime.utcnow().isoformat()
            }

            response = self.client.table("analyses").insert(data).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def get_history(self, limit: int = 10) -> list:
        """获取分析历史"""
        if not self.client:
            return []

        try:
            response = (
                self.client.table("analyses")
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return response.data
        except Exception as e:
            print(f"获取历史失败: {e}")
            return []

    def save_feedback(self, analysis_id: int, feedback: str) -> dict:
        """保存用户反馈"""
        if not self.client:
            return {"success": False, "error": "Supabase 未初始化"}

        try:
            data = {
                "analysis_id": analysis_id,
                "feedback": feedback,
                "created_at": datetime.utcnow().isoformat()
            }

            response = self.client.table("feedbacks").insert(data).execute()
            return {"success": True, "data": response.data}
        except Exception as e:
            return {"success": False, "error": str(e)}
