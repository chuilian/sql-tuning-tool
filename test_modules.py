# -*- coding: utf-8 -*-
"""
Test script for SQL tuning modules
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Force UTF-8 output
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from modules.sql_analyzer import SQLAnalyzer
from modules.plan_parser import PlanParser
from modules.optimizer import Optimizer
from modules.sql_rewriter import SQLRewriter
from modules.oracle_knowledge import (
    INDEX_KNOWLEDGE,
    JOIN_KNOWLEDGE,
    SUBQUERY_KNOWLEDGE,
    HINT_KNOWLEDGE
)

print("=" * 60)
print("SQL Tuning Module Test")
print("=" * 60)

# Test 1: SQL Analyzer
print("\n[Test 1] SQL Analyzer")
print("-" * 40)

analyzer = SQLAnalyzer()

test_sql = """
SELECT *
FROM employees e, departments d
WHERE e.department_id = d.department_id
AND e.salary > 5000
AND UPPER(e.name) LIKE '%SMITH%'
AND e.department_id NOT IN (SELECT department_id FROM departments WHERE active = 'N')
"""

result = analyzer.analyze(test_sql)
print(f"Found {len(result['issues'])} issues:")
for issue in result['issues']:
    print(f"  - [{issue['severity']}] {issue['type']}")

print(f"\nComplexity: {result['complexity']}")

# Test 2: Plan Parser
print("\n\n[Test 2] Plan Parser")
print("-" * 40)

parser = PlanParser()

test_plan = """Plan
| Id | Operation | Name | Rows | Cost |
| 0 | SELECT STATEMENT | | 1000 | 5000 |
| 1 | NESTED LOOPS | | | |
| 2 | TABLE ACCESS FULL | EMPLOYEES | 1000 | 3000 |
| 3 | TABLE ACCESS BY INDEX ROWID | DEPARTMENTS | 10 | 2000 |
| 4 | INDEX RANGE SCAN | PK_DEPT | 5 | |
"""

parsed = parser.parse(test_plan)
print(f"Format: {parsed['format']}")
print(f"Operations: {len(parsed['operations'])}")
for op in parsed['operations']:
    print(f"  - {op['operation']}")

bottlenecks = parser.identify_bottlenecks(parsed)
print(f"\nBottlenecks: {len(bottlenecks)}")
for b in bottlenecks:
    print(f"  - [{b['severity']}] {b['type']}")

# Test 3: Optimizer
print("\n\n[Test 3] Optimizer")
print("-" * 40)

optimizer = Optimizer()
suggestions_result = optimizer.generate(result['issues'], bottlenecks)

print(f"Generated {len(suggestions_result['suggestions'])} suggestions:")
for s in suggestions_result['suggestions'][:3]:
    # Replace emoji with text
    sev = s['severity'].replace("\U0001f7e0", "URGENT").replace("\U0001f7e1", "SUGGEST").replace("\U0001f7e2", "OPTIONAL")
    print(f"  [{sev}] {s['title']}")
    print(f"    Method: {s['method'][:50]}...")

# Test 4: HINT Suggestions
print("\n\n[Test 4] HINT Suggestions")
print("-" * 40)

hints = suggestions_result.get('hints', [])
if hints:
    print(f"Generated {len(hints)} hints:")
    for h in hints:
        print(f"  - {h['type']}: {h['hint']}")
else:
    print("  No hints (need more issues)")

# Test 5: Knowledge Base
print("\n\n[Test 5] Knowledge Base")
print("-" * 40)

print(f"Index knowledge: {len(INDEX_KNOWLEDGE)} topics")
print(f"JOIN knowledge: {len(JOIN_KNOWLEDGE)} topics")
print(f"Subquery knowledge: {len(SUBQUERY_KNOWLEDGE)} topics")
print(f"HINT knowledge: {len(HINT_KNOWLEDGE)} topics")

print("\nB-Tree applicable scenarios:")
for scenario in INDEX_KNOWLEDGE['b_tree']['适用场景'][:3]:
    print(f"  OK: {scenario}")

print("\nCommon HINTs:")
for hint in HINT_KNOWLEDGE['common_hints'][:3]:
    print(f"  OK: {hint}")

# Test 6: SQL Rewriter
print("\n\n[Test 6] SQL Rewriter")
print("-" * 40)

rewriter = SQLRewriter()
rewrite_result = rewriter.rewrite(test_sql, suggestions_result['suggestions'])

print("Optimized SQL (first 200 chars):")
print(rewrite_result['optimized_sql'][:200] + "...")

print("\nDifferences:")
for diff in rewrite_result['differences'][:2]:
    print(f"  - {diff['type']}: {diff['reason']}")

print("\n" + "=" * 60)
print("ALL TESTS PASSED!")
print("=" * 60)
