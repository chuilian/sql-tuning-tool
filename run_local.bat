@echo off
echo ========================================
echo   SQL 优化工具 - 一键部署脚本
echo ========================================
echo.

echo [1/3] 检查 Git...
git --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未安装 Git，请先安装 Git
    pause
    exit /b 1
)

echo [2/3] 检查 Streamlit...
streamlit --version >nul 2>&1
if errorlevel 1 (
    echo 正在安装 Streamlit...
    pip install streamlit
)

echo.
echo [3/3] 启动应用...
echo.
echo 请访问: http://localhost:8501
echo.
echo 按 Ctrl+C 停止服务
echo.

cd /d "%~dp0"
streamlit run app.py --server.headless false
