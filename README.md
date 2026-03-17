# SQL优化助手

基于 AI 的 Oracle SQL 优化工具，帮助 DBA 和开发人员快速诊断和优化 SQL 查询。

## 功能特点

- **SQL 诊断分析**：自动识别反模式和性能问题
- **执行计划解读**：AI 自动解读 Oracle 执行计划
- **优化建议生成**：分级提供优化建议和风险提示
- **SQL 改写**：输出优化后的 SQL 及详细说明

## 技术栈

- **前端**：Streamlit
- **数据库**：Supabase (PostgreSQL + pgvector)
- **AI**：Claude API (Anthropic)
- **部署**：Streamlit Cloud

## 本地开发

### 环境要求

- Python 3.10+
- Git

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置环境变量

创建 `.env` 文件：

```env
# Supabase 配置
SUPABASE_URL=你的Supabase项目URL
SUPABASE_KEY=你的Supabase匿名密钥

# Anthropic Claude API
ANTHROPIC_API_KEY=你的Claude API密钥
```

### 运行应用

```bash
streamlit run app.py
```

## 部署

项目配置为自动部署到 Streamlit Cloud：

1. 将代码推送到 GitHub 私有仓库
2. 访问 [Streamlit Cloud](https://streamlit.io/cloud)
3. 连接 GitHub 仓库并配置环境变量
4. 部署完成

## 项目结构

```
SQLtuning/
├── app.py                 # Streamlit 主应用
├── requirements.txt       # Python 依赖
├── .env.example          # 环境变量示例
├── .gitignore            # Git 忽略配置
├── supabase/
│   └── init.sql          # Supabase 初始化脚本
├── modules/
│   ├── __init__.py
│   ├── sql_analyzer.py   # SQL 分析模块
│   ├── plan_parser.py    # 执行计划解析
│   ├── optimizer.py      # 优化建议生成
│   ├── sql_rewriter.py   # SQL 改写
│   └── claude_client.py  # Claude API 客户端
└── utils/
    ├── __init__.py
    ├── formatter.py      # SQL 格式化
    └── supabase_client.py # Supabase 客户端
```

## 使用说明

### SQL 诊断分析

1. 在左侧菜单选择 "SQL 诊断"
2. 粘贴你的 SQL 查询
3. 点击"分析"按钮
4. 查看识别的问题和建议

### 执行计划解读

1. 选择 "执行计划解读"
2. 粘贴 Oracle 执行计划（EXPLAIN PLAN 或 DBMS_XPLAN 输出）
3. AI 自动解读瓶颈和优化点

### SQL 改写

1. 选择 "SQL 改写"
2. 输入原始 SQL
3. 获取优化后的 SQL 及详细说明

## 许可证

MIT License
