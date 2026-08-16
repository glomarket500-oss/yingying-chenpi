@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================
echo 溢丰堂陈皮网站 - 开启公网访问
echo ========================================
echo.
echo 正在连接 tunnelmole，请稍等...
echo 出现 https://xxx.tunnelmole.net 地址后，复制发给朋友
echo.
npx tunnelmole 8080
echo.
echo 公网隧道已断开。
pause
