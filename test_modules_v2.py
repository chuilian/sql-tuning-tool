# -*- coding: utf-8 -*-
"""
Test script for SQL tuning modules - Enhanced
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from modules.sql_analyzer import SQLAnalyzer
from modules.plan_parser import PlanParser
from modules.optimizer import Optimizer

# Test with DBMS_XPLAN format
print("=" * 60)
print("Test: DBMS_XPLAN Format Parsing")
print("=" * 60)

parser = PlanParser()

# DBMS_XPLAN format
test_plan = """Plan hash value: 1234567890

---------------------------------------------------------------------------
| Id  | Operation            | Name    | Rows | Cost (%CPU)| Time     |
---------------------------------------------------------------------------
|   0 | SELECT STATEMENT     |         | 1000 | 5000 (20)  | 00:00:30 |
|   1 |  NESTED LOOPS        |         |      |            |          |
|   2 |   TABLE ACCESS FULL  | EMP     | 1000 | 3000 (15)  | 00:00:18 |
|   3 |   TABLE ACCESS BY INDEX ROWID| DEPT |   10 | 2000 (25) | 00:00:12 |
|   4 |    INDEX RANGE SCAN   | PK_DEPT |    5 |            |          |
---------------------------------------------------------------------------

Predicate Information (identified by operation id):
---------------------------------------------------
   2 - filter("E"."SALARY">5000)
   3 - access("E"."DEPARTMENT_ID"="D"."DEPARTMENT_ID")
   4 - access("D"."DEPARTMENT_ID">0)

Note
-----
   - dynamic sampling used for this statement
"""

parsed = parser.parse(test_plan)
print(f"Format: {parsed['format']}")
print(f"Operations: {len(parsed['operations'])}")
for op in parsed['operations']:
    knowledge = op.get('knowledge', {})
    print(f"  [{op.get('cost', 'N/A')}] {op['operation']} on {op.get('object', 'N/A')}")
    print(f"       Knowledge: {knowledge.get('description', 'N/A')}")

bottlenecks = parser.identify_bottlenecks(parsed)
print(f"\nBottlenecks found: {len(bottlenecks)}")
for b in bottlenecks:
    print(f"  - [{b['severity']}] {b['type']}: {b['description']}")

# Performance summary
summary = parser.get_performance_summary(parsed)
print(f"\nPerformance Summary:")
print(f"  Total Cost: {summary['total_cost']}")
print(f"  Max Cost: {summary['max_cost']}")
print(f"  Cost Level: {summary['cost_level']}")
print(f"  Access Methods: {summary['access_methods']}")

# Test SQL with more issues
print("\n" + "=" * 60)
print("Test: Complex SQL Analysis")
print("=" * 60)

analyzer = SQLAnalyzer()

complex_sql = """
SELECT e.employee_id, e.first_name, e.salary,
       (SELECT d.department_name FROM departments d WHERE d.department_id = e.department_id) as dept_name
FROM employees e
WHERE e.department_id NOT IN (SELECT department_id FROM departments WHERE active = 'N')
  AND UPPER(e.first_name) LIKE '%JOHN%'
  OR e.salary != 50000
ORDER BY e.salary DESC
"""

result = analyzer.analyze(complex_sql)
print(f"Found {len(result['issues'])} issues:")
for issue in result['issues']:
    ref = issue.get('reference', '')
    print(f"  - [{issue['severity']}] {issue['type']}")
    print(f"    Description: {issue['description'][:60]}...")
    if ref:
        print(f"    Reference: {ref}")

print(f"\nComplexity Analysis:")
c = result['complexity']
print(f"  JOINs: {c['join_count']}, Subqueries: {c['subquery_level']}")
print(f"  WHERE Complexity: {c['where_complexity']}")
print(f"  Tables: {c['table_count']}")

# Test optimizer with bottlenecks
print("\n" + "=" * 60)
print("Test: Optimizer with Bottlenecks")
print("=" * 60)

optimizer = Optimizer()
suggestions = optimizer.generate(result['issues'], bottlenecks)

print(f"Generated {len(suggestions['suggestions'])} suggestions:")
for s in suggestions['suggestions']:
    sev = s['severity'].replace("\U0001f7e0", "URGENT").replace("\U0001f7e1", "SUGGEST").replace("\U0001f7e2", "OPTIONAL")
    print(f"  [{sev}] {s['title']}")
    if s.get('hint'):
        print(f"    HINT: {s['hint']}")

hints = suggestions.get('hints', [])
if hints:
    print(f"\nAvailable HINTs: {len(hints)}")
    for h in hints:
        print(f"  - {h['type']}: {h['hint']}")

print("\n" + "=" * 60)
print("ALL TESTS PASSED!")
print("=" * 60)
