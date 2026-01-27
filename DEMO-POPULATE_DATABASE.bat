@echo off
echo.
echo =================================================================
echo    !! AVISO !! ESTA ACAO IRA APAGAR TODOS OS DADOS ATUAIS
echo          E PREENCHER O BANCO COM DADOS DE DEMONSTRACAO.
echo =================================================================
echo.
echo    Use este script apenas para demonstrar o potencial dos
echo    dashboards com um ano de dados simulados.
echo.

set /p "confirm=Voce tem CERTEZA que deseja continuar? (s/n): "

if /i not "%confirm%"=="s" (
    echo Acao cancelada.
    goto :eof
)

echo Populando o banco de dados com dados de demonstracao...
echo (Este processo pode levar alguns segundos)

rem O comando abaixo executa o script SQL para popular o banco.
powershell -Command "Get-Content back-end/scripts/populate_db.sql | docker-compose exec -T db psql -U postgres -d terelina_db"

echo.
echo Banco de dados populado com sucesso para demonstracao!
echo Atualize seus dashboards no Grafana para ver os novos dados.
echo.
pause

:eof