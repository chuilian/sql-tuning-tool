"""
SQL 优化助手 - 主应用
基于 Streamlit + Claude API
"""
import os
import sys
import streamlit as st
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.sql_analyzer import SQLAnalyzer
from modules.plan_parser import PlanParser
from modules.optimizer import Optimizer
from modules.sql_rewriter import SQLRewriter
from modules.claude_client import ClaudeClient
from utils.formatter import format_sql
from utils.supabase_client import SupabaseClient


# 页面配置
st.set_page_config(
    page_title="SQL 优化助手",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 样式配置 - 简洁科技感深色主题
st.markdown("""
<style>
    /* ===== 全局样式 ===== */
    .stApp {
        background: linear-gradient(180deg, #0a0a0f 0%, #12121a 50%, #0d0d14 100%);
        min-height: 100vh;
    }

    /* 隐藏默认header */
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* ===== 主标题 ===== */
    .main-header {
        font-size: 2.8rem;
        font-weight: 700;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #00d4ff 0%, #7c3aed 50%, #00d4ff 100%);
        background-size: 200% auto;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: shine 3s linear infinite;
        text-align: center;
        padding: 1.5rem 0;
        margin-bottom: 0.5rem;
    }

    @keyframes shine {
        to { background-position: 200% center; }
    }

    /* ===== 副标题 ===== */
    .sub-header {
        font-size: 0.95rem;
        color: #64748b;
        text-align: center;
        margin-bottom: 2rem;
        letter-spacing: 0.05em;
    }

    /* ===== 卡片样式 ===== */
    .card {
        background: linear-gradient(135deg, rgba(30, 30, 45, 0.9) 0%, rgba(20, 20, 35, 0.9) 100%);
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        border: 1px solid rgba(100, 100, 150, 0.15);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(10px);
    }

    /* ===== 标签样式 ===== */
    .tag {
        display: inline-flex;
        align-items: center;
        padding: 0.35rem 0.85rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.03em;
        text-transform: uppercase;
    }
    .tag-urgent {
        color: #ff6b6b;
        background: rgba(255, 107, 107, 0.12);
        border: 1px solid rgba(255, 107, 107, 0.25);
    }
    .tag-suggest {
        color: #ffd43b;
        background: rgba(255, 212, 59, 0.1);
        border: 1px solid rgba(255, 212, 59, 0.2);
    }
    .tag-optional {
        color: #69db7c;
        background: rgba(105, 219, 124, 0.1);
        border: 1px solid rgba(105, 219, 124, 0.2);
    }

    /* ===== 代码输入框 ===== */
    .stTextArea textarea {
        font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
        font-size: 13px;
        background: linear-gradient(135deg, #0d0d14 0%, #1a1a24 100%);
        color: #e2e8f0;
        border: 1px solid rgba(100, 100, 150, 0.2);
        border-radius: 12px;
        padding: 1rem;
        line-height: 1.6;
    }
    .stTextArea textarea:focus {
        border-color: #7c3aed;
        box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.15);
    }

    /* ===== 按钮样式 ===== */
    .stButton > button {
        background: linear-gradient(135deg, #7c3aed 0%, #4f46e5 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 0.9rem;
        letter-spacing: 0.02em;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 15px rgba(124, 58, 237, 0.3);
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(124, 58, 237, 0.4);
        background: linear-gradient(135deg, #8b5cf6 0%, #6366f1 100%);
    }

    /* ===== 侧边栏 ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0d0d14 0%, #12121a 100%);
        border-right: 1px solid rgba(100, 100, 150, 0.1);
    }

    /* ===== 指标卡片 ===== */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, rgba(30, 30, 45, 0.6) 0%, rgba(20, 20, 35, 0.6) 100%);
        padding: 1rem 1.25rem;
        border-radius: 12px;
        border: 1px solid rgba(100, 100, 150, 0.1);
    }
    [data-testid="stMetricLabel"] {
        color: #64748b !important;
        font-size: 0.75rem !important;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    [data-testid="stMetricValue"] {
        color: #f1f5f9 !important;
        font-size: 1.5rem !important;
        font-weight: 600;
    }

    /* ===== 折叠面板 ===== */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, rgba(30, 30, 45, 0.6) 0%, rgba(20, 20, 35, 0.6) 100%);
        border-radius: 12px !important;
        border: 1px solid rgba(100, 100, 150, 0.1);
        color: #e2e8f0;
        font-weight: 500;
    }
    .streamlit-expanderHeader:hover {
        background: linear-gradient(135deg, rgba(40, 40, 60, 0.6) 0%, rgba(25, 25, 40, 0.6) 100%);
    }

    /* ===== 分隔线 ===== */
    hr {
        border: none;
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(100, 100, 150, 0.2), transparent);
        margin: 2rem 0;
    }

    /* ===== 表格 ===== */
    .dataframe {
        border: none !important;
    }

    /* ===== 选项卡 ===== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
    }
    .stTabs [data-baseweb="tab"] {
        background: transparent;
        border-radius: 10px 10px 0 0;
        padding: 0.75rem 1.5rem;
        color: #64748b;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(124, 58, 237, 0.2) 0%, rgba(79, 70, 229, 0.2) 100%);
        color: #a78bfa;
        border-bottom: 2px solid #7c3aed;
    }

    /* ===== 滚动条 ===== */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    ::-webkit-scrollbar-track {
        background: rgba(30, 30, 45, 0.5);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb {
        background: rgba(100, 100, 150, 0.3);
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(100, 100, 150, 0.5);
    }

    /* ===== 代码高亮 ===== */
    .sql-code {
        background: linear-gradient(135deg, #0d0d14 0%, #1a1a24 100%);
        color: #a78bfa;
        padding: 1.25rem;
        border-radius: 12px;
        font-family: 'JetBrains Mono', 'Fira Code', monospace;
        font-size: 13px;
        border: 1px solid rgba(100, 100, 150, 0.15);
        overflow-x: auto;
    }

    /* ===== 成功/警告/错误 ===== */
    .success-box {
        background: rgba(105, 219, 124, 0.08);
        border: 1px solid rgba(105, 219, 124, 0.2);
        border-radius: 12px;
        padding: 1rem;
        color: #69db7c;
    }
    .warning-box {
        background: rgba(255, 212, 59, 0.08);
        border: 1px solid rgba(255, 212, 59, 0.2);
        border-radius: 12px;
        padding: 1rem;
        color: #ffd43b;
    }
    .error-box {
        background: rgba(255, 107, 107, 0.08);
        border: 1px solid rgba(255, 107, 107, 0.2);
        border-radius: 12px;
        padding: 1rem;
        color: #ff6b6b;
    }

    /* ===== 导航radio ===== */
    [data-testid="stRadio"] > div {
        gap: 0.5rem;
    }
    [data-testid="stRadio"] label {
        background: rgba(30, 30, 45, 0.5);
        border-radius: 10px;
        padding: 0.75rem 1rem;
        color: #94a3b8;
        transition: all 0.2s;
    }
    [data-testid="stRadio"] label:hover {
        background: rgba(40, 40, 60, 0.6);
        color: #e2e8f0;
    }
    [data-testid="stRadio"] [data-testid="stRadio"] > div > div:first-child > div:first-child > div:first-child {
        accent-color: #7c3aed;
    }
</style>
""", unsafe_allow_html=True)



# 初始化客户端
@st.cache_resource
def init_clients():
    """初始化各个客户端"""
    return {
        "analyzer": SQLAnalyzer(),
        "parser": PlanParser(),
        "optimizer": Optimizer(),
        "rewriter": SQLRewriter(),
        "claude": ClaudeClient(),
        "supabase": SupabaseClient()
    }


def check_api_keys():
    """检查 API 密钥配置"""
    # 检查任意一个 AI API 即可
    has_any_api = any([
        os.getenv("ANTHROPIC_API_KEY"),
        os.getenv("MINIMAX_API_KEY"),
        os.getenv("OPENAI_API_KEY")
    ])

    if has_any_api:
        return []  # 至少配置了一个
    else:
        return ["ANTHROPIC_API_KEY 或 MINIMAX_API_KEY 或 OPENAI_API_KEY"]


# 侧边栏
def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        st.title("🔧 SQL 优化助手")

        st.markdown("---")

        # API 状态检查
        missing = check_api_keys()
        if missing:
            st.warning(f"⚠️ 缺少环境变量: {', '.join(missing)}")
            st.info("请在 .env 文件中配置")

        st.markdown("---")

        # 功能导航
        st.subheader("功能导航")
        page = st.radio(
            "选择功能",
            ["SQL 诊断分析", "执行计划解读", "SQL 改写"]
        )

        st.markdown("---")

        # 使用说明
        st.subheader("使用说明")
        st.markdown("""
        1. 选择功能模块
        2. 输入 SQL 或执行计划
        3. 点击分析按钮
        4. 查看结果和建议
        """)

        return page


def render_sql_diagnosis(clients):
    """SQL 诊断分析页面"""
    st.header("🔍 SQL 诊断分析")
    st.markdown("自动识别 SQL 中的反模式和性能问题")

    # 输入区域
    col1, col2 = st.columns([3, 2])

    with col1:
        sql_input = st.text_area(
            "输入 SQL 语句",
            height=200,
            placeholder="SELECT * FROM employees e WHERE e.salary > 50000"
        )

    with col2:
        st.markdown("### 复杂度指标")
        if sql_input:
            analysis = clients["analyzer"].analyze(sql_input)
            complexity = analysis.get("complexity", {})

            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("JOIN 数量", complexity.get("join_count", 0))
            with col_b:
                st.metric("子查询层级", complexity.get("subquery_level", 0))

            st.metric("WHERE 复杂度", complexity.get("where_complexity", "低"))

            has_functions = complexity.get("has_functions", False)
            has_subqueries = complexity.get("has_subqueries", False)

            if has_functions:
                st.warning("⚠️ 包含函数运算")
            if has_subqueries:
                st.info("ℹ️ 包含子查询")

    # 分析按钮
    if st.button("🚀 开始分析", type="primary", disabled=not sql_input):
        with st.spinner("分析中..."):
            # 本地规则分析
            local_analysis = clients["analyzer"].analyze(sql_input)

            # AI 增强分析（可选）
            ai_analysis = None
            if os.getenv("ANTHROPIC_API_KEY"):
                try:
                    ai_analysis = clients["claude"].analyze_sql(sql_input)
                except Exception as e:
                    st.error(f"AI 分析失败: {e}")

            # 显示结果
            st.markdown("---")
            st.subheader("📊 分析结果")

            # 问题列表
            issues = local_analysis.get("issues", [])

            if issues:
                for issue in issues:
                    severity = issue.get("severity", "建议")
                    severity_emoji = "🔴" if severity == "紧急" else "🟡" if severity == "建议" else "🟢"

                    with st.expander(f"{severity_emoji} {severity}: {issue.get('type', '未知问题')}"):
                        st.markdown(f"**描述**: {issue.get('description', '')}")
                        st.markdown(f"**位置**: {issue.get('location', '未知')}")
                        st.markdown(f"**建议**: {issue.get('suggestion', '')}")

                st.markdown(f"**总计**: 发现 {len(issues)} 个问题")
            else:
                st.success("✅ 暂未发现明显问题")

            # AI 分析结果
            if ai_analysis and not ai_analysis.get("error"):
                with st.expander("🤖 AI 智能分析结果"):
                    st.markdown(ai_analysis.get("summary", ""))
                    if ai_analysis.get("issues"):
                        for ai_issue in ai_analysis["issues"]:
                            st.markdown(f"- {ai_issue.get('description', '')}")

            # 保存到历史记录
            if clients["supabase"].client:
                clients["supabase"].save_analysis(sql_input, local_analysis)


def render_plan_explanation(clients):
    """执行计划解读页面"""
    st.header("📋 执行计划解读")
    st.markdown("解读 Oracle 执行计划，识别性能瓶颈")

    col1, col2 = st.columns([3, 2])

    with col1:
        plan_input = st.text_area(
            "输入执行计划",
            height=300,
            placeholder="""Plan
----------------------------------------------------------
| Id | Operation          | Name    | Rows | Cost |
|----|--------------------|----------|------|------|
| 0  | SELECT STATEMENT   |          | 1000 | 5000 |
| 1  | TABLE ACCESS FULL | EMPLOYEES| 1000 | 5000 |
----------------------------------------------------------"""
        )

    sql_input_plan = st.text_area(
        "（可选）原始 SQL 语句",
        height=100,
        placeholder="如果有原始 SQL，可以一并输入"
    )

    with col2:
        st.markdown("### 解析结果")
        if plan_input:
            try:
                parsed_plan = clients["parser"].parse(plan_input)
                st.success(f"✅ 识别格式: {parsed_plan.get('format', 'Unknown')}")

                operations = parsed_plan.get("operations", [])
                st.metric("操作数量", len(operations))

                warnings = parsed_plan.get("warnings", [])
                if warnings:
                    st.warning(f"⚠️ 包含 {len(warnings)} 个警告")
            except Exception as e:
                st.error(f"解析失败: {e}")

    # 分析按钮
    if st.button("🔍 解读执行计划", type="primary", disabled=not plan_input):
        with st.spinner("解读中..."):
            # 解析执行计划
            parsed_plan = clients["parser"].parse(plan_input)

            # 识别瓶颈
            bottlenecks = clients["parser"].identify_bottlenecks(parsed_plan)

            # AI 增强解读（可选）
            ai_analysis = None
            if os.getenv("ANTHROPIC_API_KEY"):
                try:
                    ai_analysis = clients["claude"].explain_plan(plan_input, sql_input_plan)
                except Exception as e:
                    st.error(f"AI 解读失败: {e}")

            # 显示结果
            st.markdown("---")
            st.subheader("📊 解读结果")

            if bottlenecks:
                for bottleneck in bottlenecks:
                    severity = bottleneck.get("severity", "建议")
                    severity_emoji = "🔴" if severity == "紧急" else "🟡" if severity == "建议" else "🟢"

                    with st.expander(f"{severity_emoji} {bottleneck.get('type', '问题')}"):
                        st.markdown(f"**操作**: {bottleneck.get('operation', 'N/A')}")
                        st.markdown(f"**对象**: {bottleneck.get('object', 'N/A')}")
                        if bottleneck.get("cost"):
                            st.markdown(f"**成本**: {bottleneck.get('cost')}")
                        st.markdown(f"**描述**: {bottleneck.get('description', '')}")
                        st.markdown(f"**建议**: {bottleneck.get('suggestion', '')}")
            else:
                st.success("✅ 暂未发现明显瓶颈")

            # AI 解读结果
            if ai_analysis and not ai_analysis.get("error"):
                with st.expander("🤖 AI 智能解读"):
                    st.markdown(ai_analysis.get("summary", ""))
                    if ai_analysis.get("bottlenecks"):
                        for b in ai_analysis["bottlenecks"]:
                            st.markdown(f"- {b.get('problem', '')}")


def render_sql_rewrite(clients):
    """SQL 改写页面"""
    st.header("✏️ SQL 改写")
    st.markdown("基于优化建议改写 SQL")

    col1, col2 = st.columns(2)

    with col1:
        sql_to_rewrite = st.text_area(
            "原始 SQL",
            height=200,
            placeholder="SELECT * FROM employees WHERE department_id NOT IN (SELECT department_id FROM departments)"
        )

    with col2:
        st.markdown("### 优化建议")
        if sql_to_rewrite:
            analysis = clients["analyzer"].analyze(sql_to_rewrite)
            issues = analysis.get("issues", [])

            optimizer = Optimizer()
            suggestions = optimizer.generate(issues)

            if suggestions.get("suggestions"):
                for suggestion in suggestions["suggestions"][:5]:
                    st.markdown(f"- {suggestion.get('title', '')}")

    # 改写按钮
    if st.button("🔄 改写 SQL", type="primary", disabled=not sql_to_rewrite):
        with st.spinner("改写中..."):
            # 分析问题
            analysis = clients["analyzer"].analyze(sql_to_rewrite)
            issues = analysis.get("issues", [])

            # 生成优化建议
            optimizer = Optimizer()
            suggestions_result = optimizer.generate(issues)
            suggestions = suggestions_result.get("suggestions", [])

            # SQL 改写
            rewriter = SQLRewriter()
            rewrite_result = rewriter.rewrite(sql_to_rewrite, suggestions)

            # AI 增强改写（可选）
            ai_rewrite = None
            if os.getenv("ANTHROPIC_API_KEY") and suggestions:
                try:
                    ai_rewrite = clients["claude"].rewrite_sql(sql_to_rewrite, suggestions)
                except Exception as e:
                    st.error(f"AI 改写失败: {e}")

            # 显示结果
            st.markdown("---")
            st.subheader("✏️ 改写结果")

            # 优化后的 SQL
            st.markdown("#### 优化后的 SQL")
            optimized_sql = rewrite_result.get("optimized_sql", sql_to_rewrite)

            if ai_rewrite and not ai_rewrite.get("error"):
                optimized_sql = ai_rewrite.get("optimized_sql", optimized_sql)

            st.code(optimized_sql, language="sql")

            # 差异对比
            if rewrite_result.get("differences"):
                st.markdown("#### 改写说明")
                for diff in rewrite_result["differences"]:
                    with st.expander(f"修改: {diff.get('type', '')}"):
                        st.markdown(f"**原始**: {diff.get('original', '')}")
                        st.markdown(f"**优化**: {diff.get('optimized', '')}")
                        st.markdown(f"**理由**: {diff.get('reason', '')}")

            # 替代方案
            alternatives = rewrite_result.get("alternatives", [])
            if ai_rewrite and ai_rewrite.get("alternatives"):
                alternatives.extend(ai_rewrite.get("alternatives"))

            if alternatives:
                st.markdown("#### 替代方案")
                for i, alt in enumerate(alternatives[:3], 1):
                    with st.expander(f"方案 {i}: {alt.get('description', '')}"):
                        st.code(alt.get("sql", ""), language="sql")


# 主函数
def main():
    """主函数"""
    # 初始化客户端
    clients = init_clients()

    # 渲染侧边栏并获取当前页面
    page = render_sidebar()

    # 渲染当前页面
    if page == "SQL 诊断分析":
        render_sql_diagnosis(clients)
    elif page == "执行计划解读":
        render_plan_explanation(clients)
    elif page == "SQL 改写":
        render_sql_rewrite(clients)


if __name__ == "__main__":
    main()
