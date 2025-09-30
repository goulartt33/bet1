@echo off
REM ==================================================
REM Deploy automático do bot no Render (Windows)
REM ==================================================

REM 1. Atualiza o repositório Git
echo Atualizando repositório Git...
git add .
git commit -m "Atualização do bot"
git push origin main

REM 2. Chama o deploy no Render via CLI
echo Iniciando deploy no Render...
render deploy service --service-id YOUR_SERVICE_ID --api-key YOUR_API_KEY

REM 3. Aguarda 10 segundos para garantir que o deploy começou
timeout /t 10

REM 4. Abre o navegador no serviço
echo Abrindo o link do bot no navegador...
start https://bet-2-3uvv.onrender.com

echo Deploy finalizado!
pause
