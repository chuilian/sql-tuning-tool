# 部署指南

## 步骤 1: 创建 GitHub 仓库

1. 访问 https://github.com/new
2. 仓库名称: `sql-tuning-tool` (或其他名称)
3. 选择 **Private** (私有)
4. 点击 "Create repository"

## 步骤 2: 初始化 Git 并推送代码

在本地执行：

```bash
cd W:/AI/work/SQLtuning

# 初始化 git
git init

# 添加所有文件
git add .

# 创建初始提交
git commit -m "Initial commit: SQL 优化工具"

# 添加远程仓库 (替换为你的仓库 URL)
git remote add origin https://github.com/你的用户名/sql-tuning-tool.git

# 推送到 GitHub
git push -u origin main
```

## 步骤 3: 部署到 Streamlit Cloud

1. 访问 https://streamlit.io/cloud
2. 点击 "New app"
3. 选择你的 GitHub 仓库
4. 选择分支: `main`
5. 主程序文件: `app.py`
6. 点击 "Deploy"

## 步骤 4: 配置环境变量

部署完成后：

1. 在 Streamlit Cloud 控制台，点击你的应用
2. 进入 **Settings** → **Secrets**
3. 添加以下环境变量：

```toml
# MiniMax API (可选)
MINIMAX_API_KEY = "你的密钥"

# 或者使用 Claude
# ANTHROPIC_API_KEY = "你的密钥"
```

4. 点击 "Save"
5. 应用会自动重启

## 步骤 5: 分享给团队

部署完成后，你会获得一个类似这样的 URL：
```
https://sql-tuning-tool.streamlit.app
```

把 URL 发给团队成员即可访问！

---

## 注意事项

- **代码更新**: 推送到 GitHub 后，Streamlit Cloud 会自动重新部署
- **免费额度**: Streamlit Cloud 免费版足够小团队使用
- **API 费用**: AI 功能产生的 API 调用费用需要你在对应服务商(Claude/MiniMax)账户中充值
