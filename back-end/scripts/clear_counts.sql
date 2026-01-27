-- back-end/scripts/clear_counts.sql
-- ATENÇÃO: Este script apaga TODOS os registros de contagem.

TRUNCATE TABLE pizza_counts RESTART IDENTITY;

-- Opcional: Adicionar um log no banco para registrar a limpeza
INSERT INTO system_logs (level, message, source) VALUES ('INFO', 'All count records were manually deleted.', 'maintenance_script');
```    *   **`TRUNCATE TABLE`**: Apaga todos os dados da tabela de forma rápida.
*   **`RESTART IDENTITY`**: Reinicia o contador de `id` para 1.
*   **`INSERT INTO system_logs`**: (Opcional, mas recomendado) Deixa um rastro no log do sistema de que a limpeza foi executada.