@echo off
chcp 65001 >nul
title WareArcadeBot - Parar Bot
color 0C
echo.
echo ============================================================
echo   WareArcadeBot - Parando todas as instancias do bot
echo ============================================================
echo.
echo Isso vai fechar TODOS os processos python.exe que estejam
echo rodando o WareArcadeBot (ou outros scripts Python).
echo.
echo Se voce tiver outro programa Python aberto, ele tambem sera fechado.
echo.
pause
echo.
echo Procurando processos python.exe...
taskkill /F /IM python.exe /T 2>nul
taskkill /F /IM py.exe /T 2>nul
taskkill /F /IM pythonw.exe /T 2>nul
echo.
echo ============================================================
echo   Todas as instancias foram encerradas!
echo ============================================================
echo.
echo Agora voce pode dar UM CLIQUE apenas em INICIAR_BOT.bat
echo.
pause
