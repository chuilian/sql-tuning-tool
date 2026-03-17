# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

这是一个基于 AI 的 Oracle SQL 优化工具，采用零运维架构：
- **前端**: Streamlit
- **部署**: Streamlit Cloud（免费托管）
- **数据库**: Supabase（免费 PostgreSQL）
- **AI 引擎**: Claude API (Anthropic)

## 常用命令

### 安装依赖
```bash
pip install -r requirements.txt
```

### 运行应用（本地开发）
```bash
streamlit run app.py
```

### 环境变量配置
在项目根目录创建 `.env` 文件：
```
SUPABASE_URL=你的Supabase项目URL
SUPABASE_KEY=你的Supabase匿名密钥
ANTHROPIC_API_KEY=你的Claude API密钥
```

## 项目架构

```
SQLtuning/
├── app.py                    # Streamlit 主应用入口
├── modules/
│   ├── claude_client.py      # Claude API 客户端
│   ├── oracle_knowledge.py  # Oracle 优化知识库（核心）
│   ├── sql_analyzer.py       # SQL 本地规则分析（识别反模式）
│   ├── plan_parser.py        # Oracle 执行计划解析
│   ├── optimizer.py          # 优化建议生成
│   └── sql_rewriter.py       # SQL 改写工具
├── utils/
│   ├── formatter.py          # SQL 格式化工具
│   └── supabase_client.py   # Supabase 客户端
├── supabase/
│   └── init.sql             # 数据库初始化脚本
└── .streamlit/
    └── config.toml          # Streamlit 配置
```

## Oracle 优化知识库 (`modules/oracle_knowledge.py`)

知识库包含以下核心内容，在 SQL 优化过程中会自动调用：

### 1. 索引优化知识
- **B-Tree 索引**: 适用场景、不适用场景、最佳实践
- **位图索引**: 适用场景、OLAP 环境
- **函数索引**: 基于 UPPER/LOWER/TRUNC 等函数的索引
- **复合索引**: 列顺序原则、索引跳跃扫描

### 2. JOIN 优化知识
- **Nested Loop**: 原理、适用场景、成本计算、优化建议
- **Hash Join**: 原理、适用场景、HASH_AREA_SIZE
- **Sort Merge Join**: 原理、适用场景、非等值连接
- **选择原则**: 根据数据量和索引情况选择最优 JOIN 方式

### 3. 子查询优化知识
- **EXISTS vs IN**: 各自适用场景
- **标量子查询**: 问题诊断、改写为 JOIN
- **NOT IN 问题**: NULL 处理、改写方案

### 4. 分区表优化知识
- **分区裁剪**: 静态裁剪、动态裁剪
- **分区类型**: 范围分区、列表分区、哈希分区、复合分区

### 5. HINT 知识
- `PARALLEL`: 并行执行 Hint
- `INDEX`: 强制使用索引
- `LEADING`: 指定连接顺序
- `USE_NL/USE_HASH/USE_MERGE`: 连接方式 Hint

### 6. 常见反模式
- 隐式类型转换
- OR 展开
- 前导通配符
- 函数包裹索引列
- SELECT *
- 笛卡尔积
- 不必要的排序

### 7. 性能指标参考
- Cost 阈值划分
- 基数估算
- 访问方法对比

## 核心模块

### 1. SQL 分析 (`modules/sql_analyzer.py`)
- 基于规则识别反模式：SELECT *、NOT IN、隐式转换、笛卡尔积等
- 计算 SQL 复杂度：JOIN 数量、子查询层级、WHERE 复杂度
- 集成知识库：自动关联相关 Oracle 优化知识

### 2. 执行计划解析 (`modules/plan_parser.py`)
- 支持多种格式：DBMS_XPLAN、EXPLAIN PLAN、通用格式
- 识别性能瓶颈：全表扫描、嵌套循环、排序操作
- 集成知识库：每个操作都有 Oracle 官方参考

### 3. 优化建议 (`modules/optimizer.py`)
- 生成分级建议：🔴 紧急、🟡 建议、🟢 可选
- 包含 Oracle 官方最佳实践引用
- 自动生成 HINT 建议
- 提供相关知识参考

### 4. SQL 改写 (`modules/sql_rewriter.py`)
- 应用改写规则
- 生成替代方案

## 部署流程

1. **GitHub**: 将代码推送到私有仓库
2. **Supabase**: 创建项目并执行 `supabase/init.sql`
3. **Streamlit Cloud**: 连接 GitHub 仓库，配置环境变量
4. 访问生成的 URL 即可使用

## 注意事项

- 本地分析使用规则引擎 + Oracle 知识库，无需 API 密钥
- AI 增强功能（Claude API）需要配置 `ANTHROPIC_API_KEY`
- 首次使用建议先在本地测试，配置好环境变量后再部署
- 知识库会持续更新，包含 Oracle 官方最佳实践
