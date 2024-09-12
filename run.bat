@echo off
REM 打开命令行窗口并切换到GUI目录，然后运行python服务器

start cmd /c call open.bat

REM 切换到GUI目录
cd GUI

REM 如果GUI目录不存在，尝试切换到gui目录
cd gui


REM 运行Python服务器
python manage.py runserver

pause
