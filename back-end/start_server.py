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

# Adicionar diretório atual ao path
sys.path.append(str(Path(__file__).parent))

def setup_environment():
    """Configura variáveis de ambiente e logging"""
    
    # Carregar variáveis de ambiente
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
        print(f"Arquivo .env carregado: {env_file}")
    else:
        print(f"Arquivo .env não encontrado: {env_file}")
        print("Usando variáveis de ambiente padrão")
    
    # Configurar logging
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('terelina_backend.log'),
            logging.StreamHandler()
        ]
    )
    
    print(f"Nível de log configurado: {log_level}")

def check_dependencies():
    """Verifica se todas as dependências estão instaladas"""
    required_packages = [
        'fastapi',
        'uvicorn',
        'paho-mqtt',
        'psycopg2-binary',
        'python-dotenv',
        'pydantic'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Dependências faltando: {', '.join(missing_packages)}")
        print("Execute: pip install -r requirements.txt")
        return False
    
    print("Todas as dependências estão instaladas")
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
        
        print(f"Conexão com banco OK: {version[0]}")
        return True
        
    except Exception as e:
        print(f"Erro na conexão com banco: {e}")
        return False

def main():
    """Função principal"""
    print("Iniciando servidor Terelina...")
    print("=" * 50)
    
    # Configurar ambiente
    setup_environment()
    
    # Verificar dependências
    if not check_dependencies():
        sys.exit(1)
    
    # Verificar banco de dados
    if not check_database_connection():
        print("Continuando sem conexão com banco...")
    
    # Configurações do servidor
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '8000'))
    reload = os.getenv('RELOAD', 'true').lower() == 'true'
    
    print(f"Servidor configurado para: {host}:{port}")
    print(f"Auto-reload: {'Sim' if reload else 'Não'}")
    print("=" * 50)
    
    # Importar e iniciar servidor
    try:
        import uvicorn
        from main import app
        
        print("Iniciando servidor FastAPI...")
        uvicorn.run(
            "main:app",
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
        
    except KeyboardInterrupt:
        print("\nServidor interrompido pelo usuário")
    except Exception as e:
        print(f"Erro ao iniciar servidor: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
