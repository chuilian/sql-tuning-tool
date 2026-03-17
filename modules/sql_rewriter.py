"""
SQL 改写模块
"""
import re
import sqlparse
from typing import Dict, List, Tuple


class SQLRewriter:
    """SQL 改写器"""

    def __init__(self):
        pass

    def rewrite(self, sql: str, suggestions: List[Dict]) -> Dict:
        """根据优化建议改写 SQL"""
        optimized_sql = sql

        differences = []

        # 应用各项改写
        for suggestion in suggestions:
            method = suggestion.get("method", "")
            issue_type = suggestion.get("issue_type", "")

            result = self._apply_rewrite(optimized_sql, issue_type, method, suggestions)
            optimized_sql = result["sql"]

            if result.get("diff"):
                differences.extend(result["diff"])

        # 格式化输出
        formatted_sql = self._format_sql(optimized_sql)

        # 生成 alternatives（简化版，实际由 AI 生成更详细）
        alternatives = self._generate_alternatives(sql, suggestions)

        return {
            "optimized_sql": formatted_sql,
            "differences": differences,
            "alternatives": alternatives,
            "original_sql": sql
        }

    def _apply_rewrite(self, sql: str, issue_type: str, method: str, suggestions: List[Dict]) -> Dict:
        """应用具体的改写规则"""
        sql_upper = sql.upper()

        # SELECT * 改写
        if issue_type == "SELECT *":
            # 尝试推断需要的列（简化版）
            from_match = re.search(r"FROM\s+(\w+)", sql, re.IGNORECASE)
            if from_match and "SELECT *" in sql_upper:
                table_name = from_match.group(1)
                # 保持原样，由 AI 建议具体列名
                return {
                    "sql": sql,
                    "diff": [{
                        "type": "SELECT *",
                        "original": "SELECT *",
                        "optimized": "SELECT 具体列名",
                        "reason": "避免读取不必要的列"
                    }]
                }

        # NOT IN 改写
        if issue_type == "NOT IN 大表":
            # 尝试检测 NOT IN 并建议改写
            not_in_match = re.search(r"WHERE\s+(\w+)\s+NOT\s+IN\s*\(([^)]+)\)", sql, re.IGNORECASE)
            if not_in_match:
                column = not_in_match.group(1)
                subquery = not_in_match.group(2)

                # 改写为 NOT EXISTS
                optimized = re.sub(
                    r"WHERE\s+(\w+)\s+NOT\s+IN\s*\(([^)]+)\)",
                    f"""WHERE NOT EXISTS (
        SELECT 1 FROM ({subquery}) t
        WHERE t.column = {table_name}.{column}
    )""",
                    sql,
                    flags=re.IGNORECASE
                )

                return {
                    "sql": optimized if optimized != sql else sql,
                    "diff": [{
                        "type": "NOT IN 改写",
                        "original": f"{column} NOT IN ({subquery})",
                        "optimized": "NOT EXISTS (改写后)",
                        "reason": "NOT IN 性能较差，NOT EXISTS 更优"
                    }]
                }

        # OR 改写
        if issue_type == "OR 条件":
            or_match = re.search(r"WHERE\s+(.+?)\s+OR\s+(.+?)(?:\s+AND|\s+GROUP|\s+ORDER|\s+$)",
                                  sql, re.IGNORECASE | re.DOTALL)
            if or_match:
                # 简化处理，实际需要更复杂的逻辑
                return {
                    "sql": sql,
                    "diff": [{
                        "type": "OR 改写",
                        "original": "WHERE col1 = a OR col2 = b",
                        "optimized": "WHERE col1 = a UNION ALL WHERE col2 = b",
                        "reason": "OR 可能导致全表扫描，UNION 可以利用索引"
                    }]
                }

        # 函数作用于列改写
        if issue_type == "函数作用于列":
            return {
                "sql": sql,
                "diff": [{
                    "type": "函数改写",
                    "original": "WHERE UPPER(name) = 'ABC'",
                    "optimized": "WHERE name = UPPER('ABC')",
                    "reason": "在列上使用函数会禁用索引，将函数移到常量侧"
                }]
            }

        # 前导通配符
        if issue_type == "前导通配符":
            return {
                "sql": sql,
                "diff": [{
                    "type": "LIKE 改写",
                    "original": "WHERE name LIKE '%abc'",
                    "optimized": "考虑全文索引或反向查询",
                    "reason": "前导通配符无法使用索引"
                }]
            }

        # 笛卡尔积
        if issue_type == "笛卡尔积":
            return {
                "sql": sql,
                "diff": [{
                    "type": "JOIN 条件",
                    "original": "FROM a, b (无关联条件)",
                    "optimized": "添加 ON 条件",
                    "reason": "缺少 JOIN 条件会产生笛卡尔积"
                }]
            }

        return {"sql": sql, "diff": []}

    def _format_sql(self, sql: str) -> str:
        """格式化 SQL"""
        return sqlparse.format(
            sql,
            reindent=True,
            keyword_case='upper',
            identifier_case='lower',
            comma_first=False
        )

    def _generate_alternatives(self, sql: str, suggestions: List[Dict]) -> List[Dict]:
        """生成替代方案"""
        alternatives = []

        # 检测是否有 NOT IN
        if "NOT IN" in sql.upper():
            alternatives.append({
                "sql": self._rewrite_not_in_to_exists(sql),
                "description": "NOT IN 改写为 NOT EXISTS 方案"
            })
            alternatives.append({
                "sql": self._rewrite_not_in_to_join(sql),
                "description": "NOT IN 改写为 LEFT JOIN 方案"
            })

        # 检测是否有 SELECT *
        if "SELECT *" in sql.upper():
            alternatives.append({
                "sql": self._suggest_select_columns(sql),
                "description": "指定具体列名方案（需要根据实际情况修改列名）"
            })

        return alternatives

    def _rewrite_not_in_to_exists(self, sql: str) -> str:
        """NOT IN 改写为 NOT EXISTS"""
        match = re.search(
            r"WHERE\s+(\w+(?:\.\w+)?)\s+NOT\s+IN\s*\((SELECT[^)]+)\)",
            sql,
            re.IGNORECASE | re.DOTALL
        )

        if match:
            column = match.group(1)
            subquery = match.group(2)

            return sql.replace(
                f"{column} NOT IN ({subquery})",
                f"""NOT EXISTS (
        SELECT 1 FROM ({subquery}) t
        WHERE t.{column.split('.')[-1]} = {column}
    )"""
            )

        return sql

    def _rewrite_not_in_to_join(self, sql: str) -> str:
        """NOT IN 改写为 LEFT JOIN"""
        match = re.search(
            r"WHERE\s+(\w+(?:\.\w+)?)\s+NOT\s+IN\s*\((SELECT[^)]+)\)",
            sql,
            re.IGNORECASE | re.DOTALL
        )

        if match:
            column = match.group(1)
            subquery = match.group(2)
            col_name = column.split('.')[-1]

            # 简化版改写
            return f"""-- 使用 LEFT JOIN 替代 NOT IN
SELECT a.*
FROM ({sql}) a
LEFT JOIN ({subquery}) b ON a.{col_name} = b.{col_name}
WHERE b.{col_name} IS NULL"""

        return sql

    def _suggest_select_columns(self, sql: str) -> str:
        """建议 SELECT 列名"""
        # 从 FROM 子句提取表名
        from_match = re.search(r"FROM\s+(\w+)", sql, re.IGNORECASE)

        if from_match:
            table_name = from_match.group(1)
            return sql.replace(
                "SELECT *",
                f"SELECT -- TODO: 根据实际需求添加列名\n       {table_name}.*"
            )

        return sql.replace(
            "SELECT *",
            "SELECT -- TODO: 添加需要的列名"
        )

    def generate_diff(self, original: str, optimized: str) -> str:
        """生成 SQL 差异对比（简化版）"""
        orig_lines = original.split("\n")
        opt_lines = optimized.split("\n")

        diff_result = []

        for i, (orig, opt) in enumerate(zip(orig_lines, opt_lines)):
            if orig.strip() != opt.strip():
                diff_result.append(f"- {orig}")
                diff_result.append(f"+ {opt}")
            else:
                diff_result.append(f"  {orig}")

        # 处理行数不同的情况
        if len(orig_lines) > len(opt_lines):
            diff_result.extend([f"- {line}" for line in orig_lines[len(opt_lines):]])
        elif len(opt_lines) > len(orig_lines):
            diff_result.extend([f"+ {line}" for line in opt_lines[len(orig_lines):]])

        return "\n".join(diff_result)
