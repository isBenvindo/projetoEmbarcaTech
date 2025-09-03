#!/usr/bin/env python3
"""
Script de inicialização do servidor Terelina
Configura e inicia o servidor FastAPI com logging e configurações otimizadas
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Adicionar diretório atual ao path - geralmente melhor evitar se possível
sys.path.append(str(Path(__file__).parent))

def setup_environment():
    """Configura variáveis de ambiente e logging"""
    try:
        env_file = Path(__file__).parent / '.env'
        if env_file.exists():
            load_dotenv(env_file)
            print(f"Arquivo .env carregado: {env_file}")
        else:
            print(f"Arquivo .env não encontrado: {env_file}")
            print("Usando variáveis de ambiente padrão")

        # Definir log level como DEBUG se variável estiver com valor inválido
        raw_log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        log_level = getattr(logging, raw_log_level, None)
        if not isinstance(log_level, int):
            print(f"Valor inválido para LOG_LEVEL: {raw_log_level}. Usando INFO")
            log_level = logging.INFO

        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('terelina_backend.log', encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        logging.info(f"Nível de log configurado: {raw_log_level}")
        return True

    except Exception as e:
        print(f"Falha ao configurar ambiente: {e}")
        return False

def check_dependencies():
    """Verifica se todas as dependências estão instaladas"""
    required_packages = {
        'fastapi': 'fastapi',
        'uvicorn[standard]': 'uvicorn',
        'paho-mqtt': 'paho.mqtt.client',
        'psycopg2-binary': 'psycopg2',
        'python-dotenv': 'dotenv',
        'pydantic': 'pydantic'
    }
    
    missing_packages = []
    
    print("Verificando dependências...")
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        logging.error(f"Dependências faltando: {', '.join(missing_packages)}")
        print(f"Dependências faltando: {', '.join(missing_packages)}")
        print("Execute: pip install -r requirements.txt")
        return False
    
    logging.info("Todas as dependências estão instaladas")
    return True

def check_database_connection():
    """Testa conexão com o banco de dados"""
    try:
        import psycopg2
        from main import get_db_connection
        
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        
        logging.info(f"Conexão com banco OK: {version[0]}")
        return True
        
    except Exception as e:
        logging.warning(f"Erro na conexão com banco: {e}")
        return False

def validate_env_vars():
    """Valida as variáveis de ambiente essenciais para o servidor"""
    errors = []

    host = os.getenv('HOST')
    port = os.getenv('PORT')

    if host is None or host.strip() == '':
        errors.append("Variável HOST não definida ou vazia.")
    if port is None:
        errors.append("Variável PORT não definida.")
    else:
        try:
            port_num = int(port)
            if not (0 < port_num < 65536):
                errors.append("Porta fora do intervalo válido (1-65535).")
        except ValueError:
            errors.append("Variável PORT deve ser um número inteiro.")

    if errors:
        for err in errors:
            logging.error(err)
        print("Erros nas variáveis de ambiente detectados. Veja o log para detalhes.")
        return False

    return True

def main():
    """Função principal"""
    print("Iniciando servidor Terelina...")
    print("=" * 50)

    if not setup_environment():
        print("Erro ao configurar ambiente, abortando...")
        sys.exit(1)

    if not validate_env_vars():
        sys.exit(1)

    if not check_dependencies():
        sys.exit(1)

    if not check_database_connection():
        print("Continuando sem conexão com banco...")

    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8000'))
    reload = os.getenv('RELOAD', 'true').lower() in ('true', '1', 'yes')

    print(f"Servidor configurado para: {host}:{port}")
    print(f"Auto-reload: {'Sim' if reload else 'Não'}")
    print("=" * 50)

    try:
        import uvicorn
        from main import app

        logging.info(f"Iniciando servidor FastAPI em {host}:{port} (reload={reload})")
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info",
            access_log=True
        )

    except KeyboardInterrupt:
        logging.info("Servidor interrompido pelo usuário")
        print("\nServidor interrompido pelo usuário")
    except Exception as e:
        logging.error(f"Erro ao iniciar servidor: {e}", exc_info=True)
        print(f"Erro ao iniciar servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()