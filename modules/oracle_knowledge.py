"""
Oracle 优化知识库
包含索引、JOIN、子查询、分区表、Hint 等优化知识
"""

# ============== 索引优化知识 ==============

INDEX_KNOWLEDGE = {
    "b_tree": {
        "name": "B-Tree 索引",
        "description": "Oracle 默认索引类型，适合高基数字段（唯一值多）",
        "适用场景": [
            "WHERE 条件中经常使用的列",
            "ORDER BY 排序列",
            "主键和唯一键",
            "表连接 JOIN 列"
        ],
        "不适用场景": [
            "低基数字段（唯一值少，如性别、状态）",
            "经常更新的列",
            "包含大量 NULL 值的列",
            "使用函数或表达式包裹的列"
        ],
        "最佳实践": [
            "选择高基数的列创建",
            "避免在频繁更新的列上创建",
            "考虑使用复合索引减少回表",
            "定期重建碎片化的索引"
        ],
        "示例": "CREATE INDEX idx_emp_dept ON employees(department_id);"
    },

    "bitmap": {
        "name": "位图索引",
        "description": "适合低基数字段，在数据仓库中常用",
        "适用场景": [
            "低基数字段（唯一值少）",
            "只读或很少更新的表",
            "数据仓库环境",
            "需要多个位图索引组合查询"
        ],
        "不适用场景": [
            "高并发写入的 OLTP 系统",
            "经常更新的表",
            "唯一值多的列"
        ],
        "最佳实践": [
            "用于只读或低修改的表",
            "可与 B-Tree 索引组合使用",
            "适合星型查询"
        ],
        "示例": "CREATE BITMAP INDEX idx_status ON orders(status);"
    },

    "function_based": {
        "name": "函数索引",
        "description": "基于函数或表达式创建的索引",
        "适用场景": [
            "WHERE 子句中使用函数包裹列",
            "需要大小写不敏感搜索",
            "日期范围查询",
            "复杂表达式查询"
        ],
        "常见用法": [
            "UPPER/LOWER 函数索引",
            "日期函数索引",
            "算术表达式索引",
            "NVL/DECODE 函数索引"
        ],
        "示例": "CREATE INDEX idx_upper_name ON employees(UPPER(name));"
    },

    "composite": {
        "name": "复合索引",
        "description": "多列组合索引，列顺序至关重要",
        "列顺序原则": [
            "等值条件列放在前面",
            "高基数的列放在前面",
            "经常用于范围查询的列放最后"
        ],
        "索引跳跃扫描": "如果前导列基数低但后续列基数高，可能使用跳跃扫描",
        "示例": "CREATE INDEX idx_emp_dept_job ON employees(department_id, job_id);"
    },

    "index_hint": {
        "name": "索引使用场景",
        "使索引失效的情况": [
            "在索引列上使用函数",
            "使用 NOT NULL 以外的 NULL 比较",
            "前导通配符 LIKE '%xxx'",
            "使用不等于 (!=, <>)",
            "隐式类型转换"
        ],
        "示例": "-- 这些情况无法使用索引\nWHERE UPPER(name) = 'ABC'\nWHERE name LIKE '%abc'\nWHERE id != 10"
    }
}


# ============== JOIN 优化知识 ==============

JOIN_KNOWLEDGE = {
    "nested_loop": {
        "name": "嵌套循环连接 (Nested Loop Join)",
        "原理": "对驱动表的每一行，遍历内部表的匹配行",
        "适用场景": [
            "小表驱动大表",
            "有合适的索引",
            "返回少量数据",
            "OLTP 系统"
        ],
        "成本计算": "成本 ≈ 驱动表行数 × 内部表索引成本",
        "优化建议": [
            "确保内部表有高效索引",
            "选择小表作为驱动表",
            "确保连接条件有索引"
        ],
        "hint": "/*+ ORDERED USE_NL(t2) */",
        "示例": "SELECT /*+ ORDERED USE_NL(e d) */ * FROM employees e, departments d WHERE e.department_id = d.department_id"
    },

    "hash_join": {
        "name": "哈希连接 (Hash Join)",
        "原理": "小表构建哈希表，大表探测哈希桶",
        "适用场景": [
            "无合适索引",
            "大表连接大表",
            "等值连接",
            "返回大量数据"
        ],
        "限制": "只支持等值连接",
        "优化建议": [
            "确保 PGA 自动管理或足够大的 HASH_AREA_SIZE",
            "小表作为构建表（使用 BUILD 或 ORDERED hint）"
        ],
        "hint": "/*+ USE_HASH(e d) */",
        "示例": "SELECT /*+ USE_HASH(e d) */ * FROM employees e, departments d WHERE e.department_id = d.department_id"
    },

    "sort_merge": {
        "name": "排序合并连接 (Sort Merge Join)",
        "原理": "分别排序两个表，然后合并",
        "适用场景": [
            "无索引可用",
            "非等值连接（>, <, >=, <=）",
            "两个表都已排序"
        ],
        "缺点": "需要额外的排序内存",
        "优化建议": [
            "确保有足够内存进行排序",
            "如果数据已排序，可避免排序开销"
        ],
        "hint": "/*+ USE_MERGE(e d) */",
        "示例": "SELECT /*+ USE_MERGE(e d) */ * FROM employees e, departments d WHERE e.salary >= d.min_salary"
    },

    "join_choice": {
        "选择原则": {
            "nested_loop": "小表驱动 + 索引存在 = 最佳",
            "hash_join": "大表连接 + 无索引 + 等值 = 最佳",
            "sort_merge": "非等值连接 + 已排序 = 最佳"
        },
        "oracle_auto": "Oracle 默认会自动选择最优连接方式"
    }
}


# ============== 子查询优化知识 ==============

SUBQUERY_KNOWLEDGE = {
    "exists_vs_in": {
        "title": "EXISTS vs IN 优化",
        "exists": {
            "描述": "EXISTS 只要找到匹配就返回，适合相关子查询",
            "优势": "适合大表驱动小表",
            "特点": "遇到第一条匹配就终止"
        },
        "in": {
            "描述": "IN 先执行子查询，适合小表驱动大表",
            "优势": "适合子查询结果集小",
            "注意": "子查询结果大时性能差"
        },
        "优化建议": {
            "大表为主表": "EXISTS 通常更优",
            "子查询结果小": "IN 可能更优",
            "NOT IN": "始终用 NOT EXISTS 替代"
        },
        "示例": {
            "原始": "SELECT * FROM employees e WHERE department_id IN (SELECT d.department_id FROM departments d)",
            "exists改写": "SELECT * FROM employees e WHERE EXISTS (SELECT 1 FROM departments d WHERE d.department_id = e.department_id)"
        }
    },

    "scalar_subquery": {
        "title": "标量子查询优化",
        "问题": "在 SELECT/WHERE 中使用标量子查询，每行都会执行一次",
        "优化方案": [
            "改写为 JOIN",
            "使用 WITH 子句（CTE）",
            "使用窗口函数",
            "考虑物化视图"
        ],
        "示例": {
            "问题SQL": "SELECT e.name, (SELECT d.name FROM departments d WHERE d.id = e.dept_id) as dept_name FROM employees e",
            "优化SQL": "SELECT e.name, d.name as dept_name FROM employees e LEFT JOIN departments d ON d.id = e.dept_id"
        }
    },

    "correlated_subquery": {
        "title": "相关子查询优化",
        "描述": "子查询引用外层查询的列",
        "问题": "外层每行执行一次子查询",
        "优化方案": [
            "改写为 JOIN",
            "使用窗口函数",
            "使用 WITH 子句"
        ]
    },

    "not_in_issue": {
        "title": "NOT IN 问题",
        "问题": [
            "子查询包含 NULL 值时，结果为空",
            "性能通常较差"
        ],
        "解决方案": [
            "使用 NOT EXISTS",
            "使用 LEFT JOIN + IS NULL",
            "确保子查询无 NULL（使用 NVL）"
        ],
        "示例": {
            "原始": "SELECT * FROM employees WHERE department_id NOT IN (SELECT department_id FROM departments)",
            "not_exists": "SELECT * FROM employees e WHERE NOT EXISTS (SELECT 1 FROM departments d WHERE d.department_id = e.department_id)",
            "left_join": "SELECT e.* FROM employees e LEFT JOIN departments d ON d.department_id = e.department_id WHERE d.department_id IS NULL"
        }
    }
}


# ============== 分区表优化知识 ==============

PARTITION_KNOWLEDGE = {
    "partition_pruning": {
        "name": "分区裁剪",
        "描述": "优化器只扫描相关分区，排除不相关分区",
        "分类": {
            "静态裁剪": "WHERE 条件使用常量，分区在解析时已知",
            "动态裁剪": "WHERE 条件使用变量，需要运行时判断"
        },
        "启用条件": [
            "WHERE 子句使用分区键",
            "使用分区键的函数/表达式与分区方案匹配"
        ],
        "示例": {
            "按日期分区": "WHERE order_date >= '2024-01-01' AND order_date < '2024-02-01'",
            "按范围分区": "WHERE region_id BETWEEN 1 AND 10"
        }
    },

    "partition_types": {
        "范围分区": {
            "适用": "日期、数字、字符串范围",
            "示例": "PARTITION BY RANGE (order_date)"
        },
        "列表分区": {
            "适用": "有限的离散值",
            "示例": "PARTITION BY LIST (region_id)"
        },
        "哈希分区": {
            "适用": "均匀分布，数据量均匀",
            "示例": "PARTITION BY HASH (customer_id)"
        },
        "复合分区": {
            "适用": "组合条件，如日期+地区",
            "示例": "PARTITION BY RANGE (order_date) SUBPARTITION BY LIST (region)"
        }
    },

    "partition_optimizer": {
        "优化建议": [
            "确保统计信息最新",
            "使用分区键作为过滤条件",
            "避免使用函数包裹分区键",
            "考虑使用分区交换"
        ]
    }
}


# ============== HINT 知识 ==============

HINT_KNOWLEDGE = {
    "parallel": {
        "name": "并行执行 HINT",
        "描述": "启用并行查询加速大数据量操作",
        "hint": "PARALLEL(table_name, degree)",
        "简化写法": "PARALLEL(table_name)",
        "示例": "SELECT /*+ PARALLEL(employees, 8) */ * FROM employees",
        "适用场景": [
            "大表全表扫描",
            "大表排序",
            "大表连接",
            "批量 DML 操作"
        ],
        "注意事项": [
            "并行度不应超过 CPU 核心数",
            "小表不建议使用",
            "高并发时慎用"
        ]
    },

    "index": {
        "name": "索引 HINT",
        "描述": "强制使用指定索引",
        "hint": "INDEX(table index_name)",
        "示例": "SELECT /*+ INDEX(e idx_emp_dept) */ * FROM employees e WHERE department_id = 10",
        "变体": [
            "INDEX_ASC - 升序扫描",
            "INDEX_DESC - 降序扫描",
            "INDEX_COMBINE - 位图索引组合",
            "NO_INDEX - 禁止使用索引"
        ]
    },

    "leading": {
        "name": "连接顺序 HINT",
        "描述": "指定多表连接的顺序",
        "hint": "LEADING(t1 t2 t3 ...)",
        "示例": "SELECT /*+ LEADING(e d l) */ * FROM employees e, departments d, locations l WHERE e.dept_id = d.id AND d.loc_id = l.id",
        "说明": "t1 首先连接 t2，结果再连接 t3"
    },

    "ordered": {
        "name": "FROM 顺序 HINT",
        "描述": "按照 FROM 子句顺序进行连接",
        "hint": "ORDERED",
        "示例": "SELECT /*+ ORDERED */ * FROM employees e, departments d WHERE e.dept_id = d.id"
    },

    "use_nl": {
        "name": "嵌套循环 HINT",
        "描述": "强制使用嵌套循环连接",
        "hint": "USE_NL(table1 table2 ...)",
        "示例": "SELECT /*+ USE_NL(e d) */ * FROM employees e, departments d WHERE e.dept_id = d.id"
    },

    "use_hash": {
        "name": "哈希连接 HINT",
        "描述": "强制使用哈希连接",
        "hint": "USE_HASH(table1 table2 ...)",
        "示例": "SELECT /*+ USE_HASH(e d) */ * FROM employees e, departments d WHERE e.dept_id = d.id"
    },

    "use_merge": {
        "name": "排序合并 HINT",
        "描述": "强制使用排序合并连接",
        "hint": "USE_MERGE(table1 table2 ...)",
        "示例": "SELECT /*+ USE_MERGE(e d) */ * FROM employees e, departments d WHERE e.salary >= d.min_salary"
    },

    "full": {
        "name": "全表扫描 HINT",
        "hint": "FULL(table_name)",
        "示例": "SELECT /*+ FULL(e) */ * FROM employees e WHERE substr(name, 1, 1) = 'A'",
        "适用": "需要全表扫描且优化器未选择时"
    },

    "append": {
        "name": "直接路径加载 HINT",
        "描述": "INSERT 时使用直接路径绕过 buffer cache",
        "hint": "APPEND",
        "示例": "INSERT /*+ APPEND */ INTO emp_new SELECT * FROM employees",
        "注意": "会导致表锁和重做日志模式变化"
    },

    "common_hints": [
        "/*+ PARALLEL(table, degree) */",
        "/*+ INDEX(table index) */",
        "/*+ FULL(table) */",
        "/*+ LEADING(t1 t2) */",
        "/*+ ORDERED */",
        "/*+ USE_NL(t1 t2) */",
        "/*+ USE_HASH(t1 t2) */",
        "/*+ USE_MERGE(t1 t2) */",
        "/*+ APPEND */",
        "/*+ NO_INDEX(table index) */"
    ]
}


# ============== 常见反模式 ==============

ANTI_PATTERN_KNOWLEDGE = {
    "implicit_conversion": {
        "name": "隐式类型转换",
        "问题": "Oracle 自动转换数据类型，可能导致索引失效",
        "示例": {
            "问题": "WHERE name = 123 -- 数字与字符串比较",
            "问题2": "WHERE id = '123' -- 字符串与数字比较（id是NUMBER）"
        },
        "影响": "索引列上的隐式转换会导致全表扫描",
        "解决": "确保比较的两边类型一致"
    },

    "or_expansion": {
        "name": "OR 展开",
        "问题": "OR 条件可能导致优化器无法有效使用索引",
        "示例": "WHERE dept_id = 10 OR salary > 5000",
        "优化方案": [
            "改写为 UNION ALL/UNION",
            "使用 IN 替代 OR",
            "使用 DECODE 或 CASE"
        ],
        "示例改写": "SELECT * FROM emp WHERE dept_id = 10 UNION ALL SELECT * FROM emp WHERE salary > 5000"
    },

    "leading_wildcard": {
        "name": "前导通配符",
        "问题": "LIKE '%xxx' 无法使用索引",
        "示例": "WHERE name LIKE '%SMITH'",
        "解决方案": [
            "避免前导通配符",
            "使用 Oracle Text 全文索引",
            "使用反向键索引（有限场景）",
            "考虑数据库搜索功能"
        ]
    },

    "function_on_indexed_column": {
        "name": "函数包裹索引列",
        "问题": "在索引列上使用函数会导致索引失效",
        "示例": [
            "WHERE UPPER(name) = 'SMITH'",
            "WHERE TRUNC(create_date) = TRUNC(SYSDATE)",
            "WHERE salary * 1.1 > 10000"
        ],
        "解决方案": [
            "使用函数索引",
            "将函数移到常量侧",
            "使用 CASE 表达式"
        ],
        "函数索引示例": "CREATE INDEX idx_upper_name ON employees(UPPER(name));"
    },

    "select_star": {
        "name": "SELECT *",
        "问题": [
            "读取不必要的列，增加 I/O",
            "网络传输更多数据",
            "如果表结构变化可能导致错误"
        ],
        "解决": "明确列出需要的列"
    },

    "cartesian_product": {
        "name": "笛卡尔积",
        "问题": "多表连接缺少 JOIN 条件",
        "后果": "返回行数 = 表1行数 × 表2行数 × ...",
        "解决": "确保所有表都有正确的 ON 条件"
    },

    "unnecessary_sort": {
        "name": "不必要的排序",
        "问题": "DISTINCT、GROUP BY、ORDER BY 会产生排序开销",
        "优化": [
            "确认是否真正需要排序",
            "使用索引避免排序",
            "考虑使用 DISTINCT vs GROUP BY 的区别"
        ]
    },

    "too_many_columns": {
        "name": "过多列",
        "问题": "SELECT 过多列可能导致回表次数增加",
        "优化": [
            "使用复合索引覆盖查询",
            "只选择必要的列"
        ]
    },

    "pagination_without_orderby": {
        "name": "分页无 ORDER BY",
        "问题": "无固定排序的分页结果不确定",
        "解决": "始终指定明确的 ORDER BY"
    }
}


# ============== 优化建议模板 ==============

OPTIMIZATION_TEMPLATES = {
    "index_recommendation": {
        "模板": "为 {table}.{column} 创建 B-Tree 索引",
        "理由": "该列在 WHERE 条件中高频使用，且基数较高",
        "SQL": "CREATE INDEX idx_{table}_{column} ON {table}({column});"
    },

    "function_index_recommendation": {
        "模板": "为 {table}.{function}({column}) 创建函数索引",
        "理由": "WHERE 子句中对列使用了函数，导致普通索引失效",
        "SQL": "CREATE INDEX idx_{table}_{func}_{column} ON {table}({function}({column}));"
    },

    "composite_index_recommendation": {
        "模板": "创建复合索引 ({columns})",
        "理由": "这些列经常一起出现在 WHERE 条件中",
        "SQL": "CREATE INDEX idx_{table}_{col1}_{col2} ON {table}({col1}, {col2});"
    },

    "rewrite_not_in": {
        "模板": "将 NOT IN 改写为 NOT EXISTS",
        "理由": "NOT IN 在子查询含 NULL 时结果为空，且性能较差",
        "SQL": "改写为 NOT EXISTS 或 LEFT JOIN + IS NULL"
    },

    "rewrite_or_to_union": {
        "模板": "将 OR 条件改写为 UNION",
        "理由": "OR 条件可能导致全表扫描，UNION 可以更好利用索引"
    }
}


# ============== 性能指标参考 ==============

PERFORMANCE_REFERENCE = {
    "cost_threshold": {
        "low": "0-1000",
        "medium": "1000-10000",
        "high": "10000-100000",
        "very_high": ">100000"
    },

    "cardinality_estimate": {
        "low": "<100 行",
        "medium": "100-10000 行",
        "high": "10000-1000000 行",
        "very_high": ">1000000 行"
    },

    "access_methods": {
        "TABLE ACCESS FULL": "最慢，适合大表全扫描",
        "TABLE ACCESS BY INDEX ROWID": "通过索引回表",
        "INDEX UNIQUE SCAN": "唯一索引，等值查找最快",
        "INDEX RANGE SCAN": "索引范围扫描",
        "INDEX FULL SCAN": "全索引扫描",
        "INDEX FAST FULL SCAN": "多块读，更快",
        "INDEX SKIP SCAN": "跳跃扫描，跳过前导列"
    },

    "join_order": {
        "最佳实践": "小表 → 中表 → 大表",
        "驱动表选择": "返回行数少的表作为驱动表"
    }
}


# ============== 知识库查询函数 ==============

def get_index_knowledge(index_type: str = None):
    """获取索引知识"""
    if index_type:
        return INDEX_KNOWLEDGE.get(index_type, {})
    return INDEX_KNOWLEDGE


def get_join_knowledge(join_type: str = None):
    """获取 JOIN 知识"""
    if join_type:
        return JOIN_KNOWLEDGE.get(join_type, {})
    return JOIN_KNOWLEDGE


def get_subquery_knowledge(topic: str = None):
    """获取子查询知识"""
    if topic:
        return SUBQUERY_KNOWLEDGE.get(topic, {})
    return SUBQUERY_KNOWLEDGE


def get_partition_knowledge(topic: str = None):
    """获取分区表知识"""
    if topic:
        return PARTITION_KNOWLEDGE.get(topic, {})
    return PARTITION_KNOWLEDGE


def get_hint_knowledge(hint_type: str = None):
    """获取 HINT 知识"""
    if hint_type:
        return HINT_KNOWLEDGE.get(hint_type, {})
    return HINT_KNOWLEDGE


def get_anti_pattern_knowledge(pattern: str = None):
    """获取反模式知识"""
    if pattern:
        return ANTI_PATTERN_KNOWLEDGE.get(pattern, {})
    return ANTI_PATTERN_KNOWLEDGE
