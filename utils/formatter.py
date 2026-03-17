"""
SQL 格式化工具
"""
import sqlparse


def format_sql(sql: str, indent: int = 4, uppercase: bool = True) -> str:
    """
    格式化 SQL 语句

    Args:
        sql: 原始 SQL
        indent: 缩进空格数
        uppercase: 是否将关键字转为大写

    Returns:
        格式化后的 SQL
    """
    return sqlparse.format(
        sql,
        reindent=True,
        keyword_case='upper' if uppercase else 'lower',
        identifier_case='lower',
        indent_width=indent,
        comma_first=False
    )


def highlight_keywords(sql: str) -> str:
    """
    为 SQL 关键字添加高亮标记（用于显示）
    """
    keywords = [
        'SELECT', 'FROM', 'WHERE', 'AND', 'OR', 'NOT', 'IN', 'EXISTS',
        'JOIN', 'LEFT', 'RIGHT', 'INNER', 'OUTER', 'FULL', 'CROSS',
        'ON', 'AS', 'ORDER', 'BY', 'GROUP', 'HAVING', 'LIMIT', 'OFFSET',
        'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'ALTER', 'DROP', 'TABLE',
        'INDEX', 'VIEW', 'UNION', 'ALL', 'DISTINCT', 'CASE', 'WHEN', 'THEN',
        'ELSE', 'END', 'NULL', 'IS', 'BETWEEN', 'LIKE', 'ASC', 'DESC',
        'WITH', 'RECURSIVE', 'OVER', 'PARTITION', 'ROW_NUMBER', 'RANK'
    ]

    result = sql
    for keyword in keywords:
        pattern = r'\b' + keyword + r'\b'
        result = result.replace(keyword, f"**{keyword}**")

    return result


def extract_tables(sql: str) -> list:
    """提取 SQL 中的表名"""
    import re

    # 简单实现，可能不完整
    tables = []

    # FROM 子句
    from_pattern = r'FROM\s+(\w+)(?:\s+(?:AS\s+)?(\w+))?'
    tables.extend(re.findall(from_pattern, sql, re.IGNORECASE))

    # JOIN 子句
    join_pattern = r'JOIN\s+(\w+)(?:\s+(?:AS\s+)?(\w+))?'
    tables.extend(re.findall(join_pattern, sql, re.IGNORECASE))

    return list(set([t[0] for t in tables]))


def extract_columns(sql: str) -> list:
    """提取 SQL 中的列名"""
    import re

    # SELECT 后的列
    select_pattern = r'SELECT\s+(.+?)\s+FROM'
    match = re.search(select_pattern, sql, re.IGNORECASE | re.DOTALL)

    if match:
        columns_str = match.group(1)
        # 分割列
        columns = re.split(r',\s*(?![^()]*\))', columns_str)

        result = []
        for col in columns:
            col = col.strip()
            # 提取列名或别名
            col_match = re.match(r'(?:(\w+)\.)?(\w+)(?:\s+(?:AS\s+)?(\w+))?', col, re.IGNORECASE)
            if col_match:
                result.append(col_match.group(2))

        return result

    return []


def count_keywords(sql: str, keyword: str) -> int:
    """统计关键字出现次数"""
    import re
    pattern = r'\b' + keyword + r'\b'
    return len(re.findall(pattern, sql, re.IGNORECASE))
