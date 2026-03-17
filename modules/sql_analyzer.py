"""
SQL 分析模块 - 本地规则分析 + AI 增强分析
集成 Oracle 优化知识库
"""
import re
import sqlparse
import os
import sys
from typing import Dict, List, Tuple

# 确保模块路径正确
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle_knowledge import (
    ANTI_PATTERN_KNOWLEDGE,
    INDEX_KNOWLEDGE,
    SUBQUERY_KNOWLEDGE,
    JOIN_KNOWLEDGE
)


class SQLAnalyzer:
    """SQL 分析器 - 识别反模式和性能问题"""

    # 反模式定义（集成知识库）
    ANTI_PATTERNS = [
        {
            "pattern": r"SELECT\s+\*\s+FROM",
            "type": "SELECT *",
            "severity": "建议",
            "description": "使用 SELECT * 会读取不必要的列，增加 I/O 开销和网络传输量",
            "suggestion": "只选择需要的列",
            "reference": "Oracle SQL Tuning Guide - Avoid SELECT *"
        },
        {
            "pattern": r"WHERE\s+.*\s+NOT\s+IN\s*\(\s*SELECT",
            "type": "NOT IN 大表",
            "severity": "紧急",
            "description": SUBQUERY_KNOWLEDGE["not_in_issue"]["问题"][0],
            "suggestion": "改用 NOT EXISTS 或 LEFT JOIN + IS NULL",
            "reference": "Oracle SQL Tuning Guide - NOT IN vs NOT EXISTS"
        },
        {
            "pattern": r"WHERE\s+.*\s+LIKE\s+['\"]%",
            "type": "前导通配符",
            "severity": "建议",
            "description": ANTI_PATTERN_KNOWLEDGE["leading_wildcard"]["问题"],
            "suggestion": "避免前导通配符，或考虑 Oracle Text 全文索引",
            "reference": "Oracle Database Performance Tuning Guide"
        },
        {
            "pattern": r"WHERE\s+.*\s+IS\s+NOT\s+NULL",
            "type": "NOT NULL 条件",
            "severity": "可选",
            "description": "在有索引的列上使用 IS NOT NULL 可能导致索引失效",
            "suggestion": "根据实际情况评估，或使用函数索引",
            "reference": INDEX_KNOWLEDGE["index_hint"]["name"]
        },
        {
            "pattern": r"WHERE\s+.*\s+OR\s+",
            "type": "OR 条件",
            "severity": "建议",
            "description": ANTI_PATTERN_KNOWLEDGE["or_expansion"]["问题"],
            "suggestion": "改写为 UNION ALL 或使用 IN",
            "reference": "Oracle SQL Tuning Guide - OR Expansion"
        },
        {
            "pattern": r"WHERE\s+.*\s+!=\s*['\"]?\d+['\"]?|WHERE\s+.*\s+<>",
            "type": "不等于操作符",
            "severity": "建议",
            "description": INDEX_KNOWLEDGE["index_hint"]["使索引失效的情况"][3],
            "suggestion": "考虑改写为积极条件 (=, >, <) 或使用其他方式",
            "reference": INDEX_KNOWLEDGE["b_tree"]["name"]
        },
        {
            "pattern": r"WHERE\s+(?:TRUNC|UPPER|LOWER|SUBSTR|LENGTH|TO_CHAR|TO_DATE)\s*\(\s*\w+",
            "type": "函数作用于列",
            "severity": "建议",
            "description": ANTI_PATTERN_KNOWLEDGE["function_on_indexed_column"]["问题"],
            "suggestion": "创建函数索引，或将函数移到常量侧",
            "reference": INDEX_KNOWLEDGE["function_based"]["name"]
        },
        {
            "pattern": r"FROM\s+.*\s+,.*\s+,",
            "type": "笛卡尔积",
            "severity": "紧急",
            "description": ANTI_PATTERN_KNOWLEDGE["cartesian_product"]["问题"],
            "suggestion": "添加适当的 JOIN 条件",
            "reference": "Oracle SQL Tuning Guide - Join Methods"
        }
    ]

    def __init__(self):
        pass

    def analyze(self, sql: str) -> Dict:
        """分析 SQL 并返回结果"""
        sql = self._preprocess_sql(sql)

        issues = []
        issues.extend(self._find_anti_patterns(sql))
        issues.extend(self._analyze_complexity(sql))
        issues.extend(self._analyze_join_patterns(sql))
        issues.extend(self._analyze_subquery_patterns(sql))

        return {
            "issues": issues,
            "complexity": self._calculate_complexity(sql),
            "knowledge": self._extract_relevant_knowledge(issues),
            "summary": self._generate_summary(issues)
        }

    def _preprocess_sql(self, sql: str) -> str:
        """预处理 SQL"""
        # 移除注释
        sql = re.sub(r"--.*$", "", sql, flags=re.MULTILINE)
        sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
        return sql.strip()

    def _find_anti_patterns(self, sql: str) -> List[Dict]:
        """查找反模式"""
        issues = []
        sql_upper = sql.upper()

        for anti in self.ANTI_PATTERNS:
            if re.search(anti["pattern"], sql_upper, re.IGNORECASE):
                issues.append({
                    "severity": anti["severity"],
                    "type": anti["type"],
                    "description": anti["description"],
                    "suggestion": anti["suggestion"],
                    "reference": anti.get("reference", ""),
                    "location": self._find_location(sql, anti["pattern"])
                })

        # 检查隐式类型转换
        issues.extend(self._check_implicit_conversion(sql))

        # 检查标量子查询
        issues.extend(self._check_scalar_subquery(sql))

        return issues

    def _check_implicit_conversion(self, sql: str) -> List[Dict]:
        """检查隐式类型转换"""
        issues = []

        # 数字和字符串混用
        if re.search(r"WHERE\s+\w+\s*=\s*['\"]", sql, re.IGNORECASE):
            issues.append({
                "severity": "建议",
                "type": "隐式类型转换",
                "description": ANTI_PATTERN_KNOWLEDGE["implicit_conversion"]["问题"],
                "suggestion": "确保列类型和比较值类型一致",
                "reference": "Oracle SQL Tuning Guide - Data Type Conversion",
                "location": "WHERE 子句"
            })

        return issues

    def _check_scalar_subquery(self, sql: str) -> List[Dict]:
        """检查标量子查询"""
        issues = []

        # 检测 SELECT 中的标量子查询
        if re.search(r"SELECT\s+.*\s*\(\s*SELECT", sql, re.IGNORECASE):
            issues.append({
                "severity": "建议",
                "type": "标量子查询",
                "description": SUBQUERY_KNOWLEDGE["scalar_subquery"]["问题"],
                "suggestion": SUBQUERY_KNOWLEDGE["scalar_subquery"]["优化方案"][0],
                "reference": SUBQUERY_KNOWLEDGE["scalar_subquery"]["title"],
                "location": "SELECT 子句"
            })

        return issues

    def _analyze_join_patterns(self, sql: str) -> List[Dict]:
        """分析 JOIN 模式"""
        issues = []
        sql_upper = sql.upper()

        # 检测多表 FROM 缺少 JOIN（可能的笛卡尔积）
        from_matches = re.findall(r"FROM\s+(\w+)(?:\s+(?:AS\s+)?(\w+))?", sql, re.IGNORECASE)
        join_matches = re.findall(r"JOIN\s+(\w+)", sql_upper)

        if len(from_matches) > 1 and len(join_matches) < len(from_matches) - 1:
            # 可能有隐式连接
            comma_joins = len(re.findall(r"FROM\s+[^,]+,\s*", sql, re.IGNORECASE))
            if comma_joins > 0:
                issues.append({
                    "severity": "建议",
                    "type": "隐式连接语法",
                    "description": "使用逗号分隔多表是旧式语法，建议使用显式 JOIN",
                    "suggestion": "改用 INNER JOIN / LEFT JOIN 等显式语法",
                    "reference": "Oracle SQL Tuning Guide - Explicit vs Implicit Joins",
                    "location": "FROM 子句"
                })

        return issues

    def _analyze_subquery_patterns(self, sql: str) -> List[Dict]:
        """分析子查询模式"""
        issues = []
        sql_upper = sql.upper()

        # 检测相关子查询
        if re.search(r"WHERE\s+.*\s+(?:=|!=|>|<|>=|<=)\s*\(?\s*SELECT", sql, re.IGNORECASE):
            # 检查是否已经在外层使用 EXISTS/IN
            if not re.search(r"\b(?:EXISTS|IN|ANY|ALL)\b", sql_upper):
                issues.append({
                    "severity": "建议",
                    "type": "相关子查询",
                    "description": SUBQUERY_KNOWLEDGE["correlated_subquery"]["描述"],
                    "suggestion": "考虑使用 JOIN 或窗口函数改写",
                    "reference": SUBQUERY_KNOWLEDGE["correlated_subquery"]["title"],
                    "location": "WHERE 子句"
                })

        return issues

    def _analyze_complexity(self, sql: str) -> List[Dict]:
        """分析 SQL 复杂度"""
        issues = []
        sql_upper = sql.upper()

        # 计算 JOIN 数量
        join_count = len(re.findall(r"\bJOIN\b", sql_upper))

        # 计算子查询层级
        subquery_level = self._count_subquery_level(sql)

        # 检查是否有 DISTINCT / GROUP BY / ORDER BY（可能导致排序）
        has_sort = any([
            re.search(r"\bDISTINCT\b", sql_upper),
            re.search(r"\bGROUP\s+BY\b", sql_upper),
            re.search(r"\bORDER\s+BY\b", sql_upper)
        ])

        if join_count > 5:
            issues.append({
                "severity": "建议",
                "type": "多表 JOIN",
                "description": f"该 SQL 包含 {join_count} 个 JOIN，可能导致执行时间较长",
                "suggestion": "考虑拆分为多个简单查询、使用物化视图，或使用 LEADING Hint 优化连接顺序",
                "reference": "Oracle SQL Tuning Guide - Join Methods",
                "location": "FROM 子句"
            })

        if subquery_level > 2:
            issues.append({
                "severity": "建议",
                "type": "多层子查询",
                "description": f"该 SQL 包含 {subquery_level} 层子查询",
                "suggestion": "考虑使用 WITH 子句（CTE）提高可读性和可优化性",
                "reference": "Oracle SQL Tuning Guide - Subquery Optimization",
                "location": "子查询"
            })

        if has_sort:
            issues.append({
                "severity": "可选",
                "type": "排序操作",
                "description": ANTI_PATTERN_KNOWLEDGE["unnecessary_sort"]["问题"],
                "suggestion": "确认是否真正需要排序，考虑使用索引避免排序",
                "reference": "Oracle Database Performance Tuning Guide",
                "location": "SELECT/ORDER BY"
            })

        return issues

    def _count_subquery_level(self, sql: str) -> int:
        """计算子查询层级"""
        max_level = 0
        level = 0

        for char in sql.upper():
            if char == '(':
                level += 1
                max_level = max(max_level, level)
            elif char == ')':
                level = max(0, level - 1)

        return max_level

    def _calculate_complexity(self, sql: str) -> Dict:
        """计算 SQL 复杂度指标"""
        sql_upper = sql.upper()

        return {
            "join_count": len(re.findall(r"\bJOIN\b", sql_upper)),
            "subquery_level": self._count_subquery_level(sql),
            "where_complexity": self._assess_where_complexity(sql),
            "has_functions": bool(re.search(r"\bWHERE\s+\w+\s*\([^)]+\)", sql_upper)),
            "has_subqueries": bool(re.search(r"\b(SELECT|EXISTS|IN|ANY|ALL)\s*\(", sql_upper)),
            "has_distinct": bool(re.search(r"\bDISTINCT\b", sql_upper)),
            "has_group_by": bool(re.search(r"\bGROUP\s+BY\b", sql_upper)),
            "has_order_by": bool(re.search(r"\bORDER\s+BY\b", sql_upper)),
            "table_count": len(re.findall(r"FROM\s+(\w+)", sql_upper, re.IGNORECASE))
        }

    def _assess_where_complexity(self, sql: str) -> str:
        """评估 WHERE 条件复杂度"""
        where_match = re.search(r"WHERE\s+(.+?)(?:GROUP|ORDER|HAVING|LIMIT|$)", sql, re.IGNORECASE | re.DOTALL)

        if not where_match:
            return "低"

        where_clause = where_match.group(1)
        and_count = len(re.findall(r"\bAND\b", where_clause.upper()))
        or_count = len(re.findall(r"\bOR\b", where_clause.upper()))

        if and_count + or_count > 5:
            return "高"
        elif and_count + or_count > 2:
            return "中"
        return "低"

    def _extract_relevant_knowledge(self, issues: List[Dict]) -> Dict:
        """提取与问题相关的 Oracle 知识"""
        relevant = {
            "indexes": [],
            "joins": [],
            "subqueries": [],
            "hints": []
        }

        issue_types = [i.get("type", "") for i in issues]

        # 索引相关
        if "函数作用于列" in issue_types or "前导通配符" in issue_types:
            relevant["indexes"].append(INDEX_KNOWLEDGE["function_based"])
        if "不等于操作符" in issue_types or "NOT NULL 条件" in issue_types:
            relevant["indexes"].append(INDEX_KNOWLEDGE["index_hint"])

        # JOIN 相关
        if "多表 JOIN" in issue_types:
            relevant["joins"].append(JOIN_KNOWLEDGE["join_choice"])

        # 子查询相关
        if "NOT IN 大表" in issue_types:
            relevant["subqueries"].append(SUBQUERY_KNOWLEDGE["not_in_issue"])
        if "标量子查询" in issue_types or "相关子查询" in issue_types:
            relevant["subqueries"].append(SUBQUERY_KNOWLEDGE["scalar_subquery"])

        return relevant

    def _find_location(self, sql: str, pattern: str) -> str:
        """查找问题位置"""
        match = re.search(pattern, sql, re.IGNORECASE)
        if match:
            start = max(0, match.start() - 20)
            end = min(len(sql), match.end() + 20)
            return f"...{sql[start:end]}..."
        return "未知位置"

    def _generate_summary(self, issues: List[Dict]) -> str:
        """生成分析摘要"""
        if not issues:
            return "该 SQL 暂未发现明显问题"

        urgent_count = sum(1 for i in issues if i["severity"] == "紧急")
        suggest_count = sum(1 for i in issues if i["severity"] == "建议")

        summary = f"发现 {len(issues)} 个问题"
        if urgent_count > 0:
            summary += f"（其中 {urgent_count} 个紧急问题）"
        if suggest_count > 0:
            summary += f"，{suggest_count} 个建议"

        return summary

    def format_sql(self, sql: str) -> str:
        """格式化 SQL"""
        return sqlparse.format(
            sql,
            reindent=True,
            keyword_case='upper',
            identifier_case='lower'
        )

    def get_knowledge_reference(self, issue_type: str) -> Dict:
        """获取特定问题类型的知识参考"""
        knowledge_map = {
            "SELECT *": ANTI_PATTERN_KNOWLEDGE["select_star"],
            "NOT IN 大表": SUBQUERY_KNOWLEDGE["not_in_issue"],
            "前导通配符": ANTI_PATTERN_KNOWLEDGE["leading_wildcard"],
            "隐式类型转换": ANTI_PATTERN_KNOWLEDGE["implicit_conversion"],
            "OR 条件": ANTI_PATTERN_KNOWLEDGE["or_expansion"],
            "函数作用于列": ANTI_PATTERN_KNOWLEDGE["function_on_indexed_column"],
            "笛卡尔积": ANTI_PATTERN_KNOWLEDGE["cartesian_product"],
            "标量子查询": SUBQUERY_KNOWLEDGE["scalar_subquery"],
            "相关子查询": SUBQUERY_KNOWLEDGE["correlated_subquery"],
            "多表 JOIN": JOIN_KNOWLEDGE["join_choice"]
        }
        return knowledge_map.get(issue_type, {})
