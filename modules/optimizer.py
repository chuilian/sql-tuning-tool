"""
优化建议生成模块
集成 Oracle 优化知识库
"""
import re
import os
import sys
from typing import Dict, List

# 确保模块路径正确
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle_knowledge import (
    ANTI_PATTERN_KNOWLEDGE,
    INDEX_KNOWLEDGE,
    JOIN_KNOWLEDGE,
    SUBQUERY_KNOWLEDGE,
    PARTITION_KNOWLEDGE,
    HINT_KNOWLEDGE,
    PERFORMANCE_REFERENCE
)


class Optimizer:
    """SQL 优化建议生成器"""

    def generate(self, issues: List[Dict], plan_bottlenecks: List[Dict] = None) -> Dict:
        """生成优化建议"""
        suggestions = []

        # 处理 SQL 分析发现的问题
        for issue in issues:
            suggestion = self._generate_from_issue(issue)
            if suggestion:
                suggestions.append(suggestion)

        # 处理执行计划瓶颈
        if plan_bottlenecks:
            for bottleneck in plan_bottlenecks:
                suggestion = self._generate_from_bottleneck(bottleneck)
                if suggestion:
                    suggestions.append(suggestion)

        # 按严重性排序
        severity_order = {"🔴 紧急": 0, "🟡 建议": 1, "🟢 可选": 2}
        suggestions.sort(key=lambda x: severity_order.get(x.get("severity", "🟢 可选"), 3))

        return {
            "suggestions": suggestions,
            "total_count": len(suggestions),
            "urgent_count": sum(1 for s in suggestions if "🔴" in s.get("severity", "")),
            "hints": self._generate_hint_suggestions(issues, plan_bottlenecks),
            "knowledge": self._collect_knowledge(issues, plan_bottlenecks)
        }

    def _generate_from_issue(self, issue: Dict) -> Dict:
        """从问题生成建议"""
        issue_type = issue.get("type", "")

        # 映射问题类型到优化建议
        suggestions_map = {
            "SELECT *": {
                "title": "避免使用 SELECT *",
                "description": ANTI_PATTERN_KNOWLEDGE["select_star"]["问题"][0],
                "method": "只选择需要的列，列出具体的列名。",
                "expected_benefit": "减少 I/O 操作和网络传输，提升查询性能",
                "risk": "",
                "reference": "Oracle SQL Tuning Guide - Avoid SELECT *"
            },
            "NOT IN 大表": {
                "title": "改写 NOT IN 为 NOT EXISTS 或外部连接",
                "description": SUBQUERY_KNOWLEDGE["not_in_issue"]["问题"][0],
                "method": "改用 NOT EXISTS 或改写为 LEFT JOIN + IS NULL。",
                "expected_benefit": "显著提升查询性能，特别是在大表上",
                "risk": "需要确保语义等价",
                "reference": "Oracle SQL Tuning Guide - NOT IN vs NOT EXISTS",
                "examples": SUBQUERY_KNOWLEDGE["not_in_issue"]["示例"]
            },
            "前导通配符": {
                "title": "避免前导通配符",
                "description": ANTI_PATTERN_KNOWLEDGE["leading_wildcard"]["问题"],
                "method": "避免前导通配符，或考虑使用 Oracle Text 全文索引。",
                "expected_benefit": "可以使用索引，减少扫描数据量",
                "risk": "",
                "reference": "Oracle Database Performance Tuning Guide - Indexes"
            },
            "OR 条件": {
                "title": "改写 OR 条件",
                "description": ANTI_PATTERN_KNOWLEDGE["or_expansion"]["问题"],
                "method": "改用 UNION ALL 或 IN 列表。",
                "expected_benefit": "更好地利用索引",
                "risk": "",
                "reference": "Oracle SQL Tuning Guide - OR Expansion",
                "examples": ANTI_PATTERN_KNOWLEDGE["or_expansion"]["示例改写"]
            },
            "NOT NULL 条件": {
                "title": "优化 IS NOT NULL 条件",
                "description": "在列上使用 IS NOT NULL 可能导致索引失效。",
                "method": "评估是否确实需要此条件，或使用函数索引。",
                "expected_benefit": "可以利用索引",
                "risk": "",
                "reference": INDEX_KNOWLEDGE["b_tree"]["适用场景"][3]
            },
            "不等于操作符": {
                "title": "避免使用不等于操作符",
                "description": INDEX_KNOWLEDGE["index_hint"]["使索引失效的情况"][3],
                "method": "尝试改写为积极条件 (=, >, <)，或使用其他方式实现。",
                "expected_benefit": "可以使用索引",
                "risk": "",
                "reference": INDEX_KNOWLEDGE["b_tree"]["不适用场景"][3]
            },
            "函数作用于列": {
                "title": "避免在列上使用函数 / 创建函数索引",
                "description": ANTI_PATTERN_KNOWLEDGE["function_on_indexed_column"]["问题"],
                "method": "将函数移到常量侧，或创建函数索引。",
                "expected_benefit": "可以使用索引",
                "risk": "函数索引有额外存储和维护开销",
                "reference": INDEX_KNOWLEDGE["function_based"]["示例"],
                "examples": [ANTI_PATTERN_KNOWLEDGE["function_on_indexed_column"]["函数索引示例"]]
            },
            "笛卡尔积": {
                "title": "添加 JOIN 条件",
                "description": ANTI_PATTERN_KNOWLEDGE["cartesian_product"]["问题"],
                "method": "确保所有表都有正确的 ON 条件。",
                "expected_benefit": "消除笛卡尔积，显著提升性能",
                "risk": "",
                "reference": "Oracle SQL Tuning Guide - Join Methods"
            },
            "隐式类型转换": {
                "title": "避免隐式类型转换",
                "description": ANTI_PATTERN_KNOWLEDGE["implicit_conversion"]["问题"],
                "method": "确保列类型和比较值类型一致。",
                "expected_benefit": "可以使用索引，避免额外开销",
                "risk": "",
                "reference": "Oracle SQL Tuning Guide - Data Type Conversion",
                "examples": ANTI_PATTERN_KNOWLEDGE["implicit_conversion"]["示例"]
            },
            "标量子查询": {
                "title": "改写标量子查询",
                "description": SUBQUERY_KNOWLEDGE["scalar_subquery"]["问题"],
                "method": SUBQUERY_KNOWLEDGE["scalar_subquery"]["优化方案"][0],
                "expected_benefit": "减少执行次数，提升性能",
                "risk": "",
                "reference": SUBQUERY_KNOWLEDGE["scalar_subquery"]["title"],
                "examples": [SUBQUERY_KNOWLEDGE["scalar_subquery"]["示例"]["优化SQL"]]
            },
            "相关子查询": {
                "title": "改写相关子查询",
                "description": SUBQUERY_KNOWLEDGE["correlated_subquery"]["描述"],
                "method": SUBQUERY_KNOWLEDGE["correlated_subquery"]["优化方案"][0],
                "expected_benefit": "减少执行次数，提升性能",
                "risk": "",
                "reference": SUBQUERY_KNOWLEDGE["correlated_subquery"]["title"]
            },
            "多表 JOIN": {
                "title": "优化多表 JOIN",
                "description": "多表 JOIN 可能执行时间较长，考虑优化连接顺序。",
                "method": "使用 LEADING Hint 指定连接顺序，或拆分为多个查询。",
                "expected_benefit": "减少中间结果集，提升性能",
                "risk": "",
                "reference": JOIN_KNOWLEDGE["join_choice"]["选择原则"]["nested_loop"],
                "hint": HINT_KNOWLEDGE["leading"]["hint"]
            },
            "多层子查询": {
                "title": "简化子查询层级",
                "description": "多层嵌套子查询难以理解和优化。",
                "method": "使用 WITH 子句（CTE）提高可读性。",
                "expected_benefit": "提高可维护性，Oracle 可能更好地优化 CTE",
                "risk": "",
                "reference": "Oracle SQL Tuning Guide - Subquery Optimization"
            },
            "隐式连接语法": {
                "title": "使用显式 JOIN 语法",
                "description": "使用逗号分隔多表是旧式语法，建议使用显式 JOIN。",
                "method": "改用 INNER JOIN / LEFT JOIN 等显式语法。",
                "expected_benefit": "代码更清晰，优化器更好理解",
                "risk": "",
                "reference": "Oracle SQL Tuning Guide - Explicit vs Implicit Joins"
            },
            "排序操作": {
                "title": "优化排序操作",
                "description": ANTI_PATTERN_KNOWLEDGE["unnecessary_sort"]["问题"],
                "method": "确认是否真正需要排序，考虑使用索引避免排序。",
                "expected_benefit": "减少内存消耗，提升性能",
                "risk": "",
                "reference": "Oracle Database Performance Tuning Guide"
            }
        }

        # 获取建议或使用默认
        suggestion_data = suggestions_map.get(issue_type, {
            "title": f"优化: {issue_type}",
            "description": issue.get("description", ""),
            "method": issue.get("suggestion", ""),
            "expected_benefit": "提升性能",
            "risk": "",
            "reference": issue.get("reference", "")
        })

        # 添加严重性
        severity_map = {"紧急": "🔴 紧急", "建议": "🟡 建议", "可选": "🟢 可选"}

        return {
            "severity": severity_map.get(issue.get("severity", "建议"), "🟡 建议"),
            "issue_type": issue_type,
            **suggestion_data
        }

    def _generate_from_bottleneck(self, bottleneck: Dict) -> Dict:
        """从执行计划瓶颈生成建议"""
        bottleneck_type = bottleneck.get("type", "")

        suggestions_map = {
            "全表扫描": {
                "title": "优化全表扫描",
                "description": bottleneck.get("description", ""),
                "method": "分析查询条件，创建合适的 B-Tree 索引或考虑分区表。",
                "expected_benefit": "大幅减少 I/O，提升性能",
                "risk": "索引维护有开销",
                "reference": INDEX_KNOWLEDGE["b_tree"]["适用场景"][0],
                "hint": INDEX_KNOWLEDGE["b_tree"]["示例"]
            },
            "嵌套循环": {
                "title": "优化嵌套循环",
                "description": bottleneck.get("description", ""),
                "method": "评估驱动表选择，确保驱动表有合适的索引；或改用 HASH JOIN。",
                "expected_benefit": "减少连接次数，提升性能",
                "risk": "",
                "reference": JOIN_KNOWLEDGE["nested_loop"]["name"],
                "hint": f"{JOIN_KNOWLEDGE['nested_loop']['hint']} 或 /*+ USE_HASH(t1 t2) */"
            },
            "排序操作": {
                "title": "优化排序操作",
                "description": bottleneck.get("description", ""),
                "method": "创建索引消除排序，或调整 SORT_AREA_SIZE 参数。",
                "expected_benefit": "减少内存消耗，提升性能",
                "risk": "",
                "reference": "Oracle Database Performance Tuning Guide"
            },
            "高成本": {
                "title": "降低执行成本",
                "description": bottleneck.get("description", ""),
                "method": "需要综合优化：添加索引、重写 SQL、优化统计信息。",
                "expected_benefit": "显著降低执行时间",
                "risk": "需要测试验证",
                "reference": "Oracle SQL Tuning Guide"
            },
            "笛卡尔积": {
                "title": "消除笛卡尔积",
                "description": bottleneck.get("description", ""),
                "method": "检查并添加缺失的 JOIN 条件。",
                "expected_benefit": "消除严重性能问题",
                "risk": "",
                "reference": "Oracle SQL Tuning Guide - Join Methods"
            },
            "警告": {
                "title": "处理警告信息",
                "description": bottleneck.get("description", ""),
                "method": "根据具体警告内容采取相应措施。",
                "expected_benefit": "避免潜在问题",
                "risk": "",
                "reference": "Oracle Database SQL Tuning Guide"
            }
        }

        suggestion_data = suggestions_map.get(bottleneck_type, {
            "title": f"优化: {bottleneck_type}",
            "description": bottleneck.get("description", ""),
            "method": bottleneck.get("suggestion", ""),
            "expected_benefit": "提升性能",
            "risk": "",
            "reference": ""
        })

        # 添加严重性
        severity_map = {"紧急": "🔴 紧急", "建议": "🟡 建议", "可选": "🟢 可选"}

        return {
            "severity": severity_map.get(bottleneck.get("severity", "建议"), "🟡 建议"),
            "issue_type": bottleneck_type,
            **suggestion_data
        }

    def _generate_hint_suggestions(self, issues: List[Dict], bottlenecks: List[Dict] = None) -> List[Dict]:
        """生成 HINT 建议"""
        hints = []

        issue_types = [i.get("type", "") for i in issues]

        # 多表 JOIN 建议使用 LEADING
        if "多表 JOIN" in issue_types:
            hints.append({
                "type": "连接顺序",
                "hint": HINT_KNOWLEDGE["leading"]["hint"],
                "example": "/*+ LEADING(t1 t2 t3) */",
                "description": "指定连接顺序，小表先连接"
            })

        # 全表扫描建议使用索引或并行
        if bottlenecks:
            bottleneck_types = [b.get("type", "") for b in bottlenecks]
            if "全表扫描" in bottleneck_types:
                hints.append({
                    "type": "索引访问",
                    "hint": HINT_KNOWLEDGE["index"]["hint"],
                    "example": "/*+ INDEX(t index_name) */",
                    "description": "强制使用指定索引"
                })
                hints.append({
                    "type": "并行执行",
                    "hint": HINT_KNOWLEDGE["parallel"]["hint"],
                    "example": "/*+ PARALLEL(table_name, 4) */",
                    "description": "并行执行加速大表扫描"
                })

        # 嵌套循环建议使用 HASH JOIN
        if bottlenecks and "嵌套循环" in [b.get("type", "") for b in bottlenecks]:
            hints.append({
                "type": "哈希连接",
                "hint": HINT_KNOWLEDGE["use_hash"]["hint"],
                "example": "/*+ USE_HASH(t1 t2) */",
                "description": "改用哈希连接可能更快"
            })

        return hints

    def _collect_knowledge(self, issues: List[Dict], bottlenecks: List[Dict] = None) -> Dict:
        """收集相关的 Oracle 知识"""
        knowledge = {
            "indexes": [],
            "joins": [],
            "subqueries": [],
            "hints": [],
            "performance": PERFORMANCE_REFERENCE
        }

        issue_types = [i.get("type", "") for i in issues]

        # 索引知识
        if "函数作用于列" in issue_types:
            knowledge["indexes"].append(INDEX_KNOWLEDGE["function_based"])
        if "前导通配符" in issue_types:
            knowledge["indexes"].append(INDEX_KNOWLEDGE["index_hint"])
        if "不等于操作符" in issue_types or "NOT NULL 条件" in issue_types:
            knowledge["indexes"].append(INDEX_KNOWLEDGE["b_tree"])

        # JOIN 知识
        if "多表 JOIN" in issue_types:
            for join_type in ["nested_loop", "hash_join", "sort_merge"]:
                knowledge["joins"].append(JOIN_KNOWLEDGE[join_type])

        # 子查询知识
        if "NOT IN 大表" in issue_types:
            knowledge["subqueries"].append(SUBQUERY_KNOWLEDGE["not_in_issue"])
            knowledge["subqueries"].append(SUBQUERY_KNOWLEDGE["exists_vs_in"])
        if "标子公司查询" in issue_types or "相关子查询" in issue_types:
            knowledge["subqueries"].append(SUBQUERY_KNOWLEDGE["scalar_subquery"])

        # 性能参考
        knowledge["access_methods"] = PERFORMANCE_REFERENCE["access_methods"]

        return knowledge
