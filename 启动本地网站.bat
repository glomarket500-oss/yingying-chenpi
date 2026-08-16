@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================
echo 溢丰堂陈皮网站 - 本地服务器
echo ========================================
echo.
echo 本地地址：http://localhost:8080
echo.
echo 启动中...
echo.
python -m http.server 8080
echo.
echo 服务器已停止。
pause
