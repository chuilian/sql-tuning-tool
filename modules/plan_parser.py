"""
执行计划解析模块
集成 Oracle 执行计划知识库
"""
import re
import os
import sys
from typing import Dict, List, Tuple

# 确保模块路径正确
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from oracle_knowledge import PERFORMANCE_REFERENCE, INDEX_KNOWLEDGE


class PlanParser:
    """Oracle 执行计划解析器"""

    # 执行计划操作的知识参考
    OPERATION_KNOWLEDGE = {
        "TABLE ACCESS FULL": {
            "description": "全表扫描，读取表中所有行",
            "severity": "紧急",
            "suggestion": "考虑创建合适的索引",
            "cost_level": "高",
            "reference": PERFORMANCE_REFERENCE["access_methods"]["TABLE ACCESS FULL"]
        },
        "TABLE ACCESS BY INDEX ROWID": {
            "description": "通过索引 ROWID 回表访问",
            "severity": "建议",
            "suggestion": "索引列选择是否最优",
            "cost_level": "中",
            "reference": PERFORMANCE_REFERENCE["access_methods"]["TABLE ACCESS BY INDEX ROWID"]
        },
        "INDEX UNIQUE SCAN": {
            "description": "唯一索引扫描，最多返回一行",
            "severity": "正常",
            "suggestion": "最佳访问方式",
            "cost_level": "低",
            "reference": PERFORMANCE_REFERENCE["access_methods"]["INDEX UNIQUE SCAN"]
        },
        "INDEX RANGE SCAN": {
            "description": "索引范围扫描",
            "severity": "正常",
            "suggestion": "通常是最优选择",
            "cost_level": "低-中",
            "reference": PERFORMANCE_REFERENCE["access_methods"]["INDEX RANGE SCAN"]
        },
        "INDEX FULL SCAN": {
            "description": "全索引扫描，按索引顺序返回",
            "severity": "建议",
            "suggestion": "可用于避免排序",
            "cost_level": "中",
            "reference": PERFORMANCE_REFERENCE["access_methods"]["INDEX FULL SCAN"]
        },
        "INDEX FAST FULL SCAN": {
            "description": "快速全索引扫描，多块读取",
            "severity": "建议",
            "suggestion": "比 INDEX FULL SCAN 更快",
            "cost_level": "中",
            "reference": PERFORMANCE_REFERENCE["access_methods"]["INDEX FAST FULL SCAN"]
        },
        "INDEX SKIP SCAN": {
            "description": "跳跃扫描，跳过索引前导列",
            "severity": "建议",
            "suggestion": "考虑创建复合索引覆盖前导列",
            "cost_level": "中",
            "reference": PERFORMANCE_REFERENCE["access_methods"]["INDEX SKIP SCAN"]
        },
        "NESTED LOOPS": {
            "description": "嵌套循环连接",
            "severity": "建议",
            "suggestion": "确保内部表有高效索引，小表驱动大表",
            "cost_level": "变化大",
            "reference": "Oracle SQL Tuning Guide - Nested Loop Join"
        },
        "HASH JOIN": {
            "description": "哈希连接",
            "severity": "正常",
            "suggestion": "适合大表连接，无索引情况",
            "cost_level": "中-高",
            "reference": "Oracle SQL Tuning Guide - Hash Join"
        },
        "MERGE JOIN": {
            "description": "排序合并连接",
            "severity": "正常",
            "suggestion": "适合非等值连接或已排序数据",
            "cost_level": "中-高",
            "reference": "Oracle SQL Tuning Guide - Sort Merge Join"
        },
        "SORT": {
            "description": "排序操作",
            "severity": "建议",
            "suggestion": "考虑使用索引消除排序",
            "cost_level": "高",
            "reference": "Oracle Database Performance Tuning Guide"
        },
        "SORT AGGREGATE": {
            "description": "聚合排序",
            "severity": "正常",
            "suggestion": "用于聚合函数",
            "cost_level": "低"
        },
        "SORT GROUP BY": {
            "description": "分组排序",
            "severity": "建议",
            "suggestion": "考虑使用索引避免排序",
            "cost_level": "中"
        },
        "SORT ORDER BY": {
            "description": "ORDER BY 排序",
            "severity": "建议",
            "suggestion": "考虑使用索引避免排序",
            "cost_level": "中"
        },
        "VIEW": {
            "description": "视图访问",
            "severity": "建议",
            "suggestion": "检查视图是否被合并",
            "cost_level": "变化大"
        },
        "SUBQUERY": {
            "description": "子查询",
            "severity": "建议",
            "suggestion": "考虑改写为 JOIN",
            "cost_level": "变化大"
        },
        "CARTESIAN": {
            "description": "笛卡尔积",
            "severity": "紧急",
            "suggestion": "立即修复，添加 JOIN 条件",
            "cost_level": "极高",
            "reference": "Oracle SQL Tuning Guide - Cartesian Product"
        },
        "BUFFER": {
            "description": "缓冲区操作",
            "severity": "正常",
            "suggestion": "内存操作",
            "cost_level": "低"
        },
        "SEQUENCE": {
            "description": "序列访问",
            "severity": "正常",
            "suggestion": "用于获取序列值",
            "cost_level": "低"
        },
        "PARTITION": {
            "description": "分区操作",
            "severity": "正常",
            "suggestion": "检查是否使用分区裁剪",
            "cost_level": "变化大",
            "reference": "Oracle Partitioning Guide"
        }
    }

    def __init__(self):
        pass

    def parse(self, plan_text: str) -> Dict:
        """解析执行计划"""
        # 尝试识别不同的执行计划格式
        if "PLAN_TABLE_OUTPUT" in plan_text or "Plan hash value" in plan_text:
            return self._parse_dbms_xplan(plan_text)
        elif "Explain" in plan_text or "EXPLAIN PLAN" in plan_text:
            return self._parse_explain_plan(plan_text)
        else:
            return self._parse_generic_plan(plan_text)

    def _parse_dbms_xplan(self, plan_text: str) -> Dict:
        """解析 DBMS_XPLAN 输出"""
        operations = []
        warnings = []
        predicates = []

        lines = plan_text.split("\n")
        in_plan = False
        in_predicate = False
        plan_started = False

        for line in lines:
            # 检测计划输出开始
            if "PLAN_TABLE_OUTPUT" in line or "Plan hash value" in line:
                in_plan = True
                plan_started = True
                continue

            # 检测谓词信息开始
            if "Predicate Information" in line:
                in_predicate = True
                in_plan = False
                continue

            # 检测 Note/Warning 信息
            if line.strip().startswith("Note") or line.strip().startswith("Warning"):
                warnings.append(line.strip())
                continue

            # 收集谓词信息
            if in_predicate and line.strip() and not line.strip().startswith("-"):
                predicates.append(line.strip())

            # 跳过空行和分隔线
            if not line.strip() or (line.strip().startswith("-") and "---" in line):
                # 如果还没有开始解析计划，设置标志
                if plan_started and not in_plan and not in_predicate:
                    in_plan = True
                continue

            # 解析操作行 - 支持带 | 分隔符的格式
            if in_plan and "|" in line:
                parts = [p.strip() for p in line.split("|")]

                # 跳过表头，检查是否是有效数据行
                # 表头通常包含 Id, Operation, Name 等
                if len(parts) >= 3:
                    # 检查第一列是否是数字（ID）
                    first_col = parts[1].strip()
                    if first_col.isdigit() or (first_col == "0"):
                        op = self._parse_operation_line(parts)
                        if op:
                            # 添加知识参考
                            op["knowledge"] = self._get_operation_knowledge(op.get("operation", ""))
                            operations.append(op)

                # 跳过表头
                if parts[1].isdigit() or (len(parts) > 2 and parts[2].strip()):
                    op = self._parse_operation_line(parts)
                    if op:
                        # 添加知识参考
                        op["knowledge"] = self._get_operation_knowledge(op.get("operation", ""))
                        operations.append(op)

            # 收集警告信息
            if "Warning" in line or "WARNING" in line:
                warnings.append(line.strip())

        return {
            "format": "DBMS_XPLAN",
            "operations": operations,
            "warnings": warnings,
            "predicates": predicates,
            "raw_plan": plan_text,
            "access_methods": self._extract_access_methods(operations)
        }

    def _parse_explain_plan(self, plan_text: str) -> Dict:
        """解析 EXPLAIN PLAN 输出"""
        operations = []

        lines = plan_text.split("\n")

        for line in lines:
            # 跳过表头
            if "Statement Id" in line or "Plan" in line:
                continue

            # 解析 ID 和操作
            match = re.match(r"\s*(\d+)\s+([^\s].+)", line)
            if match:
                op_id = match.group(1)
                operation = match.group(2).strip()

                operations.append({
                    "id": op_id,
                    "operation": operation,
                    "object": self._extract_object_name(operation),
                    "cost": None,
                    "cardinality": None,
                    "bytes": None,
                    "knowledge": self._get_operation_knowledge(operation)
                })

        return {
            "format": "EXPLAIN PLAN",
            "operations": operations,
            "warnings": [],
            "predicates": [],
            "raw_plan": plan_text,
            "access_methods": self._extract_access_methods(operations)
        }

    def _parse_generic_plan(self, plan_text: str) -> Dict:
        """解析通用格式的执行计划"""
        operations = []

        lines = plan_text.split("\n")

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # 尝试提取操作信息
            # 常见格式: TABLE ACCESS FULL TABLENAME
            # 或者: NESTED LOOPS
            op_match = re.match(r"(\d+)?\s*([A-Z][A-Z\s]+)\s*(.*)", line)
            if op_match:
                operation = op_match.group(2).strip()
                details = op_match.group(3).strip()

                # 提取 Cost、Cardinality、Bytes
                cost_match = re.search(r"Cost[:\s]+(\d+)", details, re.IGNORECASE)
                card_match = re.search(r"Card[:\s]+(\d+)", details, re.IGNORECASE)
                bytes_match = re.search(r"Bytes[:\s]+(\d+)", details, re.IGNORECASE)

                operations.append({
                    "id": op_match.group(1) if op_match.group(1) else None,
                    "operation": operation,
                    "object": self._extract_object_name(details),
                    "cost": cost_match.group(1) if cost_match else None,
                    "cardinality": card_match.group(1) if card_match else None,
                    "bytes": bytes_match.group(1) if bytes_match else None,
                    "knowledge": self._get_operation_knowledge(operation)
                })

        return {
            "format": "Generic",
            "operations": operations,
            "warnings": self._extract_warnings(plan_text),
            "predicates": [],
            "raw_plan": plan_text,
            "access_methods": self._extract_access_methods(operations)
        }

    def _parse_operation_line(self, parts: List[str]) -> Dict:
        """解析 DBMS_XPLAN 的操作行"""
        if len(parts) < 3:
            return None

        # 格式: | Id | Operation | Name | Rows | Bytes | Cost (%CPU)| Time |
        try:
            return {
                "id": parts[1] if parts[1] else None,
                "operation": parts[2] if len(parts) > 2 else None,
                "object": parts[3] if len(parts) > 3 else None,
                "rows": parts[4] if len(parts) > 4 else None,
                "bytes": parts[5] if len(parts) > 5 else None,
                "cost": self._extract_cost(parts[6] if len(parts) > 6 else ""),
                "time": parts[7] if len(parts) > 7 else None
            }
        except:
            return {
                "id": parts[1] if len(parts) > 1 else None,
                "operation": parts[2] if len(parts) > 2 else " ".join(parts[2:])
            }

    def _extract_cost(self, cost_str: str) -> str:
        """提取 Cost 值"""
        match = re.search(r"(\d+)", cost_str)
        return match.group(1) if match else None

    def _extract_object_name(self, text: str) -> str:
        """从文本中提取对象名"""
        # 常见模式: TABLE ACCESS FULL TABLE_NAME
        # 或者: INDEX RANGE SCAN IDX_NAME
        match = re.search(r"(TABLE|INDEX|MATERIALIZED VIEW)\s+(\w+)", text, re.IGNORECASE)
        if match:
            return match.group(2)
        return None

    def _extract_warnings(self, plan_text: str) -> List[str]:
        """提取警告信息"""
        warnings = []

        warning_patterns = [
            r"Warning[:\s]*(.+)",
            r"WARNING[:\s]*(.+)",
            r"Note[:\s]*(.+)",
            r".*does not have statistics.*",
            r".*estimated rows.*"
        ]

        for pattern in warning_patterns:
            matches = re.findall(pattern, plan_text, re.IGNORECASE)
            warnings.extend(matches)

        return list(set(warnings))

    def _get_operation_knowledge(self, operation: str) -> Dict:
        """获取操作的知识参考"""
        op_upper = operation.upper()

        for key, knowledge in self.OPERATION_KNOWLEDGE.items():
            if key in op_upper:
                return knowledge

        return {
            "description": "未知操作",
            "severity": "正常",
            "suggestion": "需要进一步分析",
            "cost_level": "未知"
        }

    def _extract_access_methods(self, operations: List[Dict]) -> List[str]:
        """提取使用的访问方法"""
        methods = []
        for op in operations:
            op_name = op.get("operation", "").upper()
            if "FULL" in op_name:
                methods.append("全表扫描")
            elif "INDEX" in op_name:
                if "UNIQUE" in op_name:
                    methods.append("索引唯一扫描")
                elif "RANGE" in op_name:
                    methods.append("索引范围扫描")
                elif "FULL" in op_name:
                    methods.append("全索引扫描")
                elif "FAST" in op_name:
                    methods.append("快速全索引扫描")
                elif "SKIP" in op_name:
                    methods.append("索引跳跃扫描")
                else:
                    methods.append("索引扫描")
        return list(set(methods))

    def identify_bottlenecks(self, parsed_plan: Dict) -> List[Dict]:
        """识别执行计划中的瓶颈"""
        bottlenecks = []

        operations = parsed_plan.get("operations", [])
        warnings = parsed_plan.get("warnings", [])
        access_methods = parsed_plan.get("access_methods", [])

        # 基于操作类型识别瓶颈
        for op in operations:
            operation = op.get("operation", "").upper()
            obj = op.get("object", "")
            cost = op.get("cost")
            rows = op.get("rows", "0")

            # 全表扫描
            if "FULL" in operation and "TABLE" in operation:
                knowledge = op.get("knowledge", {})
                bottlenecks.append({
                    "type": "全表扫描",
                    "operation": op.get("operation"),
                    "object": obj,
                    "severity": knowledge.get("severity", "紧急"),
                    "description": knowledge.get("description", "表执行全表扫描"),
                    "suggestion": knowledge.get("suggestion", "考虑创建合适的索引"),
                    "cost": cost,
                    "rows": rows,
                    "reference": knowledge.get("reference", "")
                })

            # 嵌套循环
            if "NESTED LOOPS" in operation:
                bottlenecks.append({
                    "type": "嵌套循环",
                    "operation": op.get("operation"),
                    "object": obj,
                    "severity": "建议",
                    "description": "嵌套循环可能在大表上性能较差",
                    "suggestion": "确保驱动表小且有合适索引，或改用 HASH JOIN",
                    "cost": cost,
                    "rows": rows,
                    "reference": "Oracle SQL Tuning Guide - Nested Loop Join"
                })

            # 排序操作
            if "SORT" in operation:
                bottlenecks.append({
                    "type": "排序操作",
                    "operation": op.get("operation"),
                    "object": obj,
                    "severity": "建议",
                    "description": "排序操作消耗内存和时间",
                    "suggestion": "考虑创建索引避免排序",
                    "cost": cost,
                    "rows": rows,
                    "reference": "Oracle Database Performance Tuning Guide"
                })

            # 高成本操作
            if cost:
                try:
                    cost_value = int(cost)
                    if cost_value > 10000:
                        bottlenecks.append({
                            "type": "高成本",
                            "operation": op.get("operation"),
                            "object": obj,
                            "cost": cost,
                            "severity": "紧急",
                            "description": f"成本值 {cost_value} 过高",
                            "suggestion": "需要重点优化此操作",
                            "reference": PERFORMANCE_REFERENCE["cost_threshold"]["very_high"]
                        })
                except ValueError:
                    pass

            # 笛卡尔积
            if "CARTESIAN" in operation:
                bottlenecks.append({
                    "type": "笛卡尔积",
                    "operation": op.get("operation"),
                    "object": obj,
                    "severity": "紧急",
                    "description": "存在笛卡尔积，会产生大量数据",
                    "suggestion": "检查 JOIN 条件是否完整",
                    "cost": cost,
                    "rows": rows,
                    "reference": "Oracle SQL Tuning Guide - Cartesian Product"
                })

        # 处理warnings
        for warning in warnings:
            bottlenecks.append({
                "type": "警告",
                "operation": "N/A",
                "object": "N/A",
                "severity": "建议",
                "description": warning,
                "suggestion": "查看 Oracle 官方文档了解详情",
                "reference": "Oracle Database SQL Tuning Guide"
            })

        # 检查是否缺少索引
        if "全表扫描" in access_methods:
            bottlenecks.append({
                "type": "索引缺失建议",
                "operation": "N/A",
                "object": "N/A",
                "severity": "建议",
                "description": "执行计划中存在全表扫描",
                "suggestion": "考虑为频繁查询的列创建 B-Tree 索引",
                "reference": INDEX_KNOWLEDGE["b_tree"]["示例"] if 'INDEX_KNOWLEDGE' in dir() else ""
            })

        return bottlenecks

    def get_performance_summary(self, parsed_plan: Dict) -> Dict:
        """获取性能摘要"""
        operations = parsed_plan.get("operations", [])

        total_cost = 0
        max_cost = 0
        total_rows = 0

        for op in operations:
            try:
                cost = int(op.get("cost", 0) or 0)
                total_cost += cost
                max_cost = max(max_cost, cost)
            except (ValueError, TypeError):
                pass

            try:
                rows = int(op.get("rows", 0) or 0)
                total_rows += rows
            except (ValueError, TypeError):
                pass

        # 评估成本级别
        cost_level = "低"
        if max_cost > 100000:
            cost_level = "极高"
        elif max_cost > 10000:
            cost_level = "高"
        elif max_cost > 1000:
            cost_level = "中"

        return {
            "total_cost": total_cost,
            "max_cost": max_cost,
            "cost_level": cost_level,
            "estimated_rows": total_rows,
            "operation_count": len(operations),
            "access_methods": parsed_plan.get("access_methods", [])
        }
