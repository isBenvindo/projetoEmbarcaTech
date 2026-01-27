@echo off
echo.
echo =================================================================
echo    !! AVISO !! ESTA ACAO IRA APAGAR PERMANENTEMENTE
echo             TODOS OS DADOS DE CONTAGEM DE PIZZAS.
echo =================================================================
echo.
echo    Os dados de teste serao removidos e o sistema sera
echo    zerado para o inicio da producao real.
echo.

set /p "confirm=Voce tem CERTEZA que deseja continuar? (s/n): "

if /i not "%confirm%"=="s" (
    echo Acao cancelada.
    goto :eof
)

echo Limpando o banco de dados...

rem O comando abaixo executa o script SQL dentro do container do banco de dados.
powershell -Command "Get-Content back-end/scripts/clear_counts.sql | docker-compose exec -T db psql -U postgres -d terelina_db"

echo.
echo Banco de dados limpo com sucesso! Todos os registros de contagem foram removidos.
echo.
pause

:eof