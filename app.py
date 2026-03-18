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
from modules.user_config import load_user_config, save_user_config, get_user_api_keys, apply_user_env
from utils.formatter import format_sql
from utils.supabase_client import SupabaseClient

# 应用启动时加载用户配置
apply_user_env()


# 页面配置
st.set_page_config(
    page_title="SQL Optimizer",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 样式配置 - 精致终端科技感
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --bg-primary: #0a0e14;
        --bg-secondary: #111820;
        --bg-tertiary: #1a222d;
        --bg-card: rgba(22, 33, 48, 0.8);
        --accent-cyan: #00d9ff;
        --accent-teal: #00bfa5;
        --accent-purple: #7c3aed;
        --text-primary: #e6edf3;
        --text-secondary: #8b949e;
        --text-muted: #484f58;
        --border-color: rgba(0, 217, 255, 0.1);
        --border-active: rgba(0, 217, 255, 0.3);
        --success: #00e676;
        --warning: #ffab00;
        --error: #ff5252;
    }

    /* 全局样式 */
    .stApp {
        background: var(--bg-primary);
        min-height: 100vh;
        font-family: 'IBM Plex Sans', sans-serif;
    }

    /* 隐藏默认header和footer */
    header[data-testid="stHeader"] {
        background: transparent !important;
        border-bottom: 1px solid var(--border-color);
    }
    footer {
        display: none;
    }

    /* 主标题区 */
    .hero-section {
        padding: 2rem 1rem;
        text-align: center;
        position: relative;
    }

    .hero-title {
        font-size: 2.2rem;
        font-weight: 600;
        letter-spacing: -0.03em;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }

    .hero-title .accent {
        color: var(--accent-cyan);
        text-shadow: 0 0 20px rgba(0, 217, 255, 0.4);
    }

    .hero-subtitle {
        font-size: 0.9rem;
        color: var(--text-secondary);
        letter-spacing: 0.02em;
    }

    /* 侧边栏 */
    [data-testid="stSidebar"] {
        background: var(--bg-secondary) !important;
        border-right: 1px solid var(--border-color);
        width: 260px !important;
        min-width: 260px !important;
    }

    [data-testid="stSidebar"] .stTitle {
        color: var(--text-primary);
        font-size: 1.1rem;
        font-weight: 600;
        padding: 1rem 0.5rem;
        border-bottom: 1px solid var(--border-color);
    }

    /* 导航按钮 */
    .nav-item {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        color: var(--text-secondary);
        cursor: pointer;
        transition: all 0.2s ease;
        margin: 0.25rem 0;
        border: 1px solid transparent;
    }

    .nav-item:hover {
        background: var(--bg-tertiary);
        color: var(--text-primary);
    }

    .nav-item.active {
        background: linear-gradient(135deg, rgba(0, 217, 255, 0.15), rgba(0, 191, 165, 0.1));
        color: var(--accent-cyan);
        border-color: var(--border-active);
    }

    .nav-icon {
        font-size: 1.1rem;
    }

    /* 卡片 */
    .card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
        transition: border-color 0.2s ease;
    }

    .card:hover {
        border-color: var(--border-active);
    }

    .card-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid var(--border-color);
    }

    .card-title {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-primary);
    }

    /* 输入区域 */
    .stTextArea textarea {
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 13px !important;
        background: var(--bg-secondary) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        padding: 1rem !important;
        line-height: 1.6 !important;
    }

    .stTextArea textarea:focus {
        border-color: var(--accent-cyan) !important;
        box-shadow: 0 0 0 3px rgba(0, 217, 255, 0.1) !important;
        outline: none !important;
    }

    .stTextArea textarea::placeholder {
        color: var(--text-muted) !important;
    }

    /* 按钮 */
    .stButton > button {
        background: linear-gradient(135deg, var(--accent-cyan), var(--accent-teal)) !important;
        color: #000 !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.7rem 1.75rem !important;
        font-weight: 600 !important;
        font-size: 0.85rem !important;
        letter-spacing: 0.02em !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: 0 4px 15px rgba(0, 217, 255, 0.25) !important;
    }

    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 25px rgba(0, 217, 255, 0.35) !important;
    }

    .stButton > button:disabled {
        background: var(--bg-tertiary) !important;
        color: var(--text-muted) !important;
        box-shadow: none !important;
    }

    /* 指标卡片 */
    [data-testid="stMetric"] {
        background: var(--bg-secondary);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 1rem;
    }

    [data-testid="stMetricLabel"] {
        color: var(--text-secondary) !important;
        font-size: 0.7rem !important;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }

    [data-testid="stMetricValue"] {
        color: var(--accent-cyan) !important;
        font-size: 1.5rem !important;
        font-weight: 600;
        font-family: 'JetBrains Mono', monospace;
    }

    /* 折叠面板 */
    .streamlit-expanderHeader {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
        color: var(--text-primary) !important;
        font-weight: 500;
        padding: 0.75rem 1rem !important;
    }

    .streamlit-expanderHeader:hover {
        border-color: var(--border-active) !important;
    }

    /* 分隔线 */
    hr {
        border: none;
        height: 1px;
        background: var(--border-color);
        margin: 1.5rem 0;
    }

    /* 表格 */
    .dataframe {
        border: none !important;
        background: var(--bg-secondary);
    }

    /* 代码块 */
    .stCodeBlock {
        background: var(--bg-secondary) !important;
        border: 1px solid var(--border-color) !important;
        border-radius: 10px !important;
    }

    code {
        font-family: 'JetBrains Mono', monospace !important;
    }

    /* 标签/徽章 */
    .badge {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.6rem;
        border-radius: 6px;
        font-size: 0.7rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    .badge-urgent {
        background: rgba(255, 82, 82, 0.15);
        color: var(--error);
        border: 1px solid rgba(255, 82, 82, 0.3);
    }

    .badge-warning {
        background: rgba(255, 171, 0, 0.15);
        color: var(--warning);
        border: 1px solid rgba(255, 171, 0, 0.3);
    }

    .badge-success {
        background: rgba(0, 230, 118, 0.15);
        color: var(--success);
        border: 1px solid rgba(0, 230, 118, 0.3);
    }

    /* 成功/警告/错误提示 */
    .stSuccess, .stInfo, .stWarning, .stError {
        background: var(--bg-secondary);
        border-radius: 10px;
        padding: 1rem;
    }

    .stSuccess {
        border-left: 3px solid var(--success);
    }

    .stWarning {
        border-left: 3px solid var(--warning);
    }

    .stError {
        border-left: 3px solid var(--error);
    }

    /* 选择框 */
    .stSelectbox div[data-baseweb="select"] > div {
        background: var(--bg-secondary) !important;
        border-color: var(--border-color) !important;
        border-radius: 8px !important;
    }

    /* 进度条 */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, var(--accent-cyan), var(--accent-teal)) !important;
    }

    /* 滚动条 */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }

    ::-webkit-scrollbar-track {
        background: var(--bg-secondary);
    }

    ::-webkit-scrollbar-thumb {
        background: var(--border-color);
        border-radius: 3px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: var(--text-muted);
    }

    /* 动画 */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(10px); }
        to { opacity: 1; transform: translateY(0); }
    }

    .fade-in {
        animation: fadeIn 0.3s ease-out;
    }

    /* 副标题 */
    .section-header {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-primary);
        margin-bottom: 0.5rem;
    }

    .section-desc {
        font-size: 0.85rem;
        color: var(--text-secondary);
        margin-bottom: 1rem;
    }

    /* 信息卡片 */
    .info-row {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 0;
        color: var(--text-secondary);
        font-size: 0.85rem;
    }

    .info-row .icon {
        color: var(--accent-cyan);
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
    try:
        has_any_api = any([
            os.getenv("ANTHROPIC_API_KEY"),
            os.getenv("MINIMAX_API_KEY"),
            os.getenv("OPENAI_API_KEY")
        ])
        return [] if has_any_api else ["API_KEY"]
    except Exception:
        return ["API_KEY"]


# 侧边栏
def render_sidebar():
    """渲染侧边栏"""
    with st.sidebar:
        # Logo/标题
        st.markdown("""
        <div style="padding: 0.5rem 0;">
            <span style="font-size: 1.5rem;">⚡</span>
            <span style="font-size: 1.1rem; font-weight: 600; color: #e6edf3; margin-left: 0.5rem;">SQL Optimizer</span>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # 功能导航
        st.markdown('<div style="color: #8b949e; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem;">功能</div>', unsafe_allow_html=True)

        page = st.radio(
            "导航",
            ["SQL 诊断", "执行计划", "SQL 改写", "⚙️ 设置"],
            label_visibility="collapsed"
        )

        st.markdown("---")

        # API 状态
        st.markdown('<div style="color: #8b949e; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem;">AI 状态</div>', unsafe_allow_html=True)

        missing = check_api_keys()
        if missing:
            st.markdown(f"""
            <div class="badge badge-warning">
                ⚠️ 请先配置 API
            </div>
            <div style="font-size: 0.75rem; color: #484f58; margin-top: 0.5rem;">
                在"设置"中配置您的 API 密钥
            </div>
            """, unsafe_allow_html=True)
        else:
            provider = clients["claude"].get_provider_name()
            st.markdown(f"""
            <div class="badge badge-success">
                ✓ {provider}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # 快捷操作
        st.markdown('<div style="color: #8b949e; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.5rem;">快捷</div>', unsafe_allow_html=True)

        st.markdown("""
        <div style="font-size: 0.8rem; color: #8b949e; line-height: 1.8;">
            <div>📋 输入 SQL 语句</div>
            <div>🔍 分析反模式</div>
            <div>💡 获取优化建议</div>
            <div>✏️ 自动改写 SQL</div>
        </div>
        """, unsafe_allow_html=True)

        return page


def render_header():
    """渲染页面头部"""
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">
            <span class="accent">SQL</span> Optimizer
        </h1>
        <p class="hero-subtitle">Oracle SQL 智能诊断与优化工具</p>
    </div>
    """, unsafe_allow_html=True)


def render_sql_diagnosis(clients):
    """SQL 诊断分析页面"""
    render_header()

    st.markdown("### SQL 诊断")
    st.markdown('<p class="section-desc">自动识别 SQL 中的反模式和性能问题</p>', unsafe_allow_html=True)

    # 输入区域
    col1, col2 = st.columns([3, 1.5], gap="large")

    with col1:
        sql_input = st.text_area(
            "输入 SQL 语句",
            height=220,
            placeholder="SELECT * FROM employees e\nWHERE e.salary > 50000\nAND e.department_id = 10",
            label_visibility="collapsed"
        )

    with col2:
        if sql_input:
            analysis = clients["analyzer"].analyze(sql_input)
            complexity = analysis.get("complexity", {})

            st.markdown("""
            <div class="card">
                <div class="card-header">
                    <span class="card-title">复杂度分析</span>
                </div>
            """, unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                st.metric("JOIN", complexity.get("join_count", 0))
            with col_b:
                st.metric("子查询", complexity.get("subquery_level", 0))

            st.metric("WHERE 复杂度", complexity.get("where_complexity", "低"))

            st.markdown("</div>", unsafe_allow_html=True)

            # 状态提示
            if complexity.get("has_functions"):
                st.markdown('<span class="badge badge-warning">⚡ 含函数</span>', unsafe_allow_html=True)
            if complexity.get("has_subqueries"):
                st.markdown('<span class="badge badge-warning">🔄 含子查询</span>', unsafe_allow_html=True)

    # 分析按钮
    st.markdown("")
    if st.button("⚡ 开始分析", disabled=not sql_input):
        with st.spinner("分析中..."):
            local_analysis = clients["analyzer"].analyze(sql_input)

            ai_analysis = None
            if clients["claude"].is_available():
                try:
                    ai_analysis = clients["claude"].analyze_sql(sql_input)
                except:
                    pass

            # 结果展示
            st.markdown("---")
            st.markdown("### 分析结果")

            issues = local_analysis.get("issues", [])

            if issues:
                for issue in issues:
                    severity = issue.get("severity", "建议")
                    badge_class = "badge-urgent" if severity == "紧急" else "badge-warning" if severity == "建议" else "badge-success"

                    with st.expander(f"**{issue.get('type', '问题')}**"):
                        st.markdown(f"""
                        <div style="margin-bottom: 0.5rem;">
                            <span class="badge {badge_class}">{severity}</span>
                        </div>
                        <div class="info-row"><span class="icon">📍</span> {issue.get('location', '未知')}</div>
                        <div class="info-row"><span class="icon">📝</span> {issue.get('description', '')}</div>
                        <div class="info-row" style="color: #00d9ff;"><span class="icon">💡</span> {issue.get('suggestion', '')}</div>
                        """, unsafe_allow_html=True)

                st.markdown(f"**发现 {len(issues)} 个问题**")
            else:
                st.success("✓ 暂未发现明显问题")

            # AI 分析结果
            if ai_analysis and not ai_analysis.get("error"):
                with st.expander("🤖 AI 智能分析"):
                    st.markdown(ai_analysis.get("summary", ""))

            # 保存记录
            if clients["supabase"].client:
                clients["supabase"].save_analysis(sql_input, local_analysis)


def render_plan_explanation(clients):
    """执行计划解读页面"""
    render_header()

    st.markdown("### 执行计划")
    st.markdown('<p class="section-desc">解读 Oracle 执行计划，识别性能瓶颈</p>', unsafe_allow_html=True)

    col1, col2 = st.columns([3, 1.5], gap="large")

    with col1:
        plan_input = st.text_area(
            "输入执行计划",
            height=280,
            placeholder="""Plan
----------------------------------------------------------
| Id | Operation          | Name     | Rows | Cost |
|----|--------------------|----------|------|------|
| 0  | SELECT STATEMENT   |          | 1000 | 5000 |
| 1  | TABLE ACCESS FULL | EMPLOYEES| 1000 | 5000 |
----------------------------------------------------------""",
            label_visibility="collapsed"
        )

        sql_input_plan = st.text_area(
            "（可选）原始 SQL",
            height=80,
            placeholder="SELECT * FROM employees WHERE ...",
            label_visibility="collapsed"
        )

    with col2:
        if plan_input:
            try:
                parsed_plan = clients["parser"].parse(plan_input)

                st.markdown("""
                <div class="card">
                    <div class="card-header">
                        <span class="card-title">解析结果</span>
                    </div>
                """, unsafe_allow_html=True)

                st.success(f"✓ 识别格式: {parsed_plan.get('format', 'Unknown')}")
                st.metric("操作数量", len(parsed_plan.get("operations", [])))

                warnings = parsed_plan.get("warnings", [])
                if warnings:
                    st.warning(f"⚠️ 包含 {len(warnings)} 个警告")

                st.markdown("</div>", unsafe_allow_html=True)
            except Exception as e:
                st.error(f"解析失败: {e}")

    st.markdown("")
    if st.button("🔍 解读计划", disabled=not plan_input):
        with st.spinner("解读中..."):
            parsed_plan = clients["parser"].parse(plan_input)
            bottlenecks = clients["parser"].identify_bottlenecks(parsed_plan)

            ai_analysis = None
            if clients["claude"].is_available():
                try:
                    ai_analysis = clients["claude"].explain_plan(plan_input, sql_input_plan)
                except:
                    pass

            st.markdown("---")
            st.markdown("### 解读结果")

            if bottlenecks:
                for bottleneck in bottlenecks:
                    severity = bottleneck.get("severity", "建议")
                    badge_class = "badge-urgent" if severity == "紧急" else "badge-warning" if severity == "建议" else "badge-success"

                    with st.expander(f"**{bottleneck.get('type', '问题')}**"):
                        cost_html = f'<div class="info-row"><span class="icon">📈</span> 成本: {bottleneck.get("cost", "")}</div>' if bottleneck.get("cost") else ""
                        st.markdown(f"""
                        <span class="badge {badge_class}">{severity}</span>
                        <div class="info-row"><span class="icon">⚙️</span> {bottleneck.get('operation', 'N/A')}</div>
                        <div class="info-row"><span class="icon">📊</span> {bottleneck.get('object', 'N/A')}</div>
                        {cost_html}
                        <div class="info-row"><span class="icon">📝</span> {bottleneck.get('description', '')}</div>
                        <div class="info-row" style="color: #00d9ff;"><span class="icon">💡</span> {bottleneck.get('suggestion', '')}</div>
                        """, unsafe_allow_html=True)
            else:
                st.success("✓ 暂未发现明显瓶颈")

            if ai_analysis and not ai_analysis.get("error"):
                with st.expander("🤖 AI 智能解读"):
                    st.markdown(ai_analysis.get("summary", ""))


def render_sql_rewrite(clients):
    """SQL 改写页面"""
    render_header()

    st.markdown("### SQL 改写")
    st.markdown('<p class="section-desc">基于优化建议智能改写 SQL</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="large")

    with col1:
        sql_to_rewrite = st.text_area(
            "原始 SQL",
            height=200,
            placeholder="SELECT * FROM employees\nWHERE department_id NOT IN (\n    SELECT department_id FROM departments\n)",
            label_visibility="collapsed"
        )

    with col2:
        if sql_to_rewrite:
            analysis = clients["analyzer"].analyze(sql_to_rewrite)
            issues = analysis.get("issues", [])

            optimizer = Optimizer()
            suggestions = optimizer.generate(issues)

            st.markdown("""
            <div class="card">
                <div class="card-header">
                    <span class="card-title">优化建议</span>
                </div>
            """, unsafe_allow_html=True)

            if suggestions.get("suggestions"):
                for suggestion in suggestions["suggestions"][:5]:
                    st.markdown(f"• {suggestion.get('title', '')}")
            else:
                st.info("暂无优化建议")

            st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("")
    if st.button("🔄 改写 SQL", disabled=not sql_to_rewrite):
        with st.spinner("改写中..."):
            analysis = clients["analyzer"].analyze(sql_to_rewrite)
            issues = analysis.get("issues", [])

            optimizer = Optimizer()
            suggestions_result = optimizer.generate(issues)
            suggestions = suggestions_result.get("suggestions", [])

            rewriter = SQLRewriter()
            rewrite_result = rewriter.rewrite(sql_to_rewrite, suggestions)

            ai_rewrite = None
            if clients["claude"].is_available() and suggestions:
                try:
                    ai_rewrite = clients["claude"].rewrite_sql(sql_to_rewrite, suggestions)
                except:
                    pass

            st.markdown("---")
            st.markdown("### 改写结果")

            st.markdown("**优化后的 SQL**")
            optimized_sql = rewrite_result.get("optimized_sql", sql_to_rewrite)
            if ai_rewrite and not ai_rewrite.get("error"):
                optimized_sql = ai_rewrite.get("optimized_sql", optimized_sql)

            st.code(optimized_sql, language="sql")

            if rewrite_result.get("differences"):
                st.markdown("**改写说明**")
                for diff in rewrite_result["differences"]:
                    with st.expander(f"修改: {diff.get('type', '')}"):
                        st.markdown(f"**原始**: {diff.get('original', '')}")
                        st.markdown(f"**优化**: {diff.get('optimized', '')}")
                        st.markdown(f"**理由**: {diff.get('reason', '')}")

            alternatives = rewrite_result.get("alternatives", [])
            if ai_rewrite and ai_rewrite.get("alternatives"):
                alternatives.extend(ai_rewrite.get("alternatives"))

            if alternatives:
                st.markdown("**替代方案**")
                for i, alt in enumerate(alternatives[:3], 1):
                    with st.expander(f"方案 {i}: {alt.get('description', '')}"):
                        st.code(alt.get("sql", ""), language="sql")


def render_settings():
    """设置页面"""
    st.markdown("""
    <div class="hero-section">
        <h1 class="hero-title">
            <span class="accent">⚙️</span> API 设置
        </h1>
        <p class="hero-subtitle">配置您的个人 API 密钥，仅本地可用</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 选择 AI 服务商")

    provider = st.selectbox(
        "选择您要使用的 AI 服务商",
        ["MiniMax (推荐)", "Anthropic Claude", "OpenAI"],
        label_visibility="collapsed"
    )

    # 获取当前配置
    current_keys = get_user_api_keys()

    with st.form("api_key_form"):
        if "MiniMax" in provider:
            api_key = st.text_input(
                "MiniMax API Key",
                type="password",
                value=current_keys.get("minimax", ""),
                placeholder="输入您的 MiniMax API Key"
            )
            st.caption("""
            获取方式：
            1. 访问 [MiniMax 开放平台](https://platform.minimaxi.com/)
            2. 注册账号并创建 API Key
            3. 复制密钥粘贴到此处
            """)

        elif "Claude" in provider:
            api_key = st.text_input(
                "Anthropic Claude API Key",
                type="password",
                value=current_keys.get("anthropic", ""),
                placeholder="输入您的 Claude API Key"
            )
            st.caption("""
            获取方式：
            1. 访问 [Anthropic Console](https://console.anthropic.com/)
            2. 创建 API Key
            3. 复制密钥粘贴到此处
            """)

        else:
            api_key = st.text_input(
                "OpenAI API Key",
                type="password",
                value=current_keys.get("openai", ""),
                placeholder="输入您的 OpenAI API Key"
            )
            st.caption("""
            获取方式：
            1. 访问 [OpenAI Platform](https://platform.openai.com/)
            2. 创建 API Key
            3. 复制密钥粘贴到此处
            """)

        submitted = st.form_submit_button("💾 保存配置", type="primary")

        if submitted:
            provider_key = {
                "MiniMax (推荐)": "minimax",
                "Anthropic Claude": "anthropic",
                "OpenAI": "openai"
            }.get(provider, "minimax")

            # 保存配置
            save_user_config({
                "MINIMAX_API_KEY": api_key if provider_key == "minimax" else current_keys.get("minimax", ""),
                "ANTHROPIC_API_KEY": api_key if provider_key == "anthropic" else current_keys.get("anthropic", ""),
                "OPENAI_API_KEY": api_key if provider_key == "openai" else current_keys.get("openai", "")
            })

            # 重新加载环境变量
            apply_user_env()

            st.success("✓ 配置已保存！请手动刷新页面使配置生效。")

    st.markdown("---")
    st.markdown("### 当前配置状态")

    # 显示当前配置
    if current_keys and isinstance(current_keys, dict):
        has_any = any(v for v in current_keys.values() if v)
        if has_any:
            for name, key in [("MiniMax", "minimax"), ("Claude", "anthropic"), ("OpenAI", "openai")]:
                val = current_keys.get(key, "")
                if val:
                    masked = val[:8] + "..." + val[-4:] if len(val) > 12 else "***"
                    st.markdown(f"**{name}**: `{masked}`")
        else:
            st.info("暂未配置任何 API 密钥")
    else:
        st.info("暂未配置任何 API 密钥")

    st.markdown("---")
    st.markdown("""
    ### 🔒 隐私说明

    - 您的 API 密钥保存在本地：`~/.sql-optimizer/config.json`
    - 密钥仅在您的本地设备使用，不会上传到任何服务器
    - 每个用户需要单独配置自己的 API 密钥
    """)


# 主函数
def main():
    """主函数"""
    clients = init_clients()
    page = render_sidebar()

    if page == "SQL 诊断":
        render_sql_diagnosis(clients)
    elif page == "执行计划":
        render_plan_explanation(clients)
    elif page == "SQL 改写":
        render_sql_rewrite(clients)
    elif "设置" in page:
        render_settings()


if __name__ == "__main__":
    main()
