from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import psycopg2
from psycopg2 import Error
import os
import time
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from dotenv import load_dotenv

from mqtt_client import start_mqtt_client

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('terelina_backend.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Terelina Pizza Counter API",
    description="API para contagem automática de pizzas da Terelina - Otimizada para Grafana",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Banco de dados
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "terelina_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "caclopool")
DB_PORT = os.getenv("DB_PORT", "5432")

# Modelos Pydantic
class ContagemResponse(BaseModel):
    id: int
    timestamp: str

class HealthResponse(BaseModel):
    status: str
    message: str
    timestamp: str
    database_connected: bool

class ErrorResponse(BaseModel):
    error: str
    detail: str
    timestamp: str

class EstatisticasResponse(BaseModel):
    total_contagens: int
    contagens_hoje: int
    ultima_contagem: str | None
    timestamp_consulta: str

class GrafanaTimeSeriesResponse(BaseModel):
    target: str
    datapoints: List[List[Any]]

mqtt_client_instance = None

def get_db_connection():
    """Estabelece conexão com o banco PostgreSQL"""
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        logger.info("Conexão com PostgreSQL estabelecida com sucesso")
        return conn
    except Error as e:
        logger.error(f"Erro ao conectar ao PostgreSQL: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro interno do servidor ao conectar ao DB: {e}"
        )

def get_db():
    """Dependency para injeção de conexão com banco"""
    conn = get_db_connection()
    try:
        yield conn
    finally:
        conn.close()

def log_system_event(nivel: str, mensagem: str, origem: str = "backend"):
    """Registra evento no log do sistema"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO logs_sistema (nivel, mensagem, origem) VALUES (%s, %s, %s)",
            (nivel, mensagem, origem)
        )
        conn.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Erro ao registrar log no banco: {e}")
    finally:
        if conn:
            conn.close()

@app.on_event("startup")
async def startup_event():
    """Evento executado na inicialização da aplicação"""
    global mqtt_client_instance
    logger.info("Iniciando aplicação FastAPI e cliente MQTT...")
    log_system_event("INFO", "Aplicação FastAPI iniciada", "backend")
    
    try:
        mqtt_client_instance = start_mqtt_client(get_db_connection)
        logger.info("Cliente MQTT iniciado com sucesso")
        log_system_event("INFO", "Cliente MQTT iniciado com sucesso", "mqtt")
    except Exception as e:
        logger.error(f"Erro ao iniciar cliente MQTT: {e}")
        log_system_event("ERROR", f"Erro ao iniciar cliente MQTT: {e}", "mqtt")
        # Não falha a aplicação se MQTT não conectar

@app.on_event("shutdown")
async def shutdown_event():
    """Evento executado no encerramento da aplicação"""
    global mqtt_client_instance
    logger.info("Encerrando aplicação FastAPI e cliente MQTT...")
    log_system_event("INFO", "Aplicação FastAPI encerrada", "backend")
    
    if mqtt_client_instance:
        try:
            mqtt_client_instance.loop_stop()
            mqtt_client_instance.disconnect()
            logger.info("Cliente MQTT encerrado com sucesso")
            log_system_event("INFO", "Cliente MQTT encerrado", "mqtt")
        except Exception as e:
            logger.error(f"Erro ao encerrar cliente MQTT: {e}")
            log_system_event("ERROR", f"Erro ao encerrar cliente MQTT: {e}", "mqtt")

@app.get("/", response_model=Dict[str, str])
async def read_root():
    """Endpoint raiz da API"""
    return {
        "message": "Bem-vindo ao Backend de Contagem de Pizzas da Terelina!",
        "version": "1.0.0",
        "status": "online",
        "grafana_ready": "true"
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Endpoint de verificação de saúde da aplicação"""
    db_connected = False
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        cursor.close()
        conn.close()
        db_connected = True
        message = f"Aplicação funcionando normalmente - PostgreSQL {version[0]}"
    except Exception as e:
        message = f"Problema na conexão com banco: {str(e)}"
    
    return HealthResponse(
        status="healthy" if db_connected else "unhealthy",
        message=message,
        timestamp=datetime.now().isoformat(),
        database_connected=db_connected
    )

@app.get("/test_db_connection", response_model=HealthResponse)
async def test_db_connection():
    """Testa conexão com o banco de dados"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()
        cursor.close()
        
        return HealthResponse(
            status="success",
            message=f"Conexão com o PostgreSQL estabelecida com sucesso! Versão: {version[0]}",
            timestamp=datetime.now().isoformat(),
            database_connected=True
        )
    except HTTPException as e:
        return HealthResponse(
            status="error",
            message=e.detail,
            timestamp=datetime.now().isoformat(),
            database_connected=False
        )
    except Exception as e:
        logger.error(f"Erro inesperado no teste de conexão: {e}")
        return HealthResponse(
            status="error",
            message=f"Um erro inesperado ocorreu: {str(e)}",
            timestamp=datetime.now().isoformat(),
            database_connected=False
        )
    finally:
        if conn:
            conn.close()

@app.get("/contagens", response_model=List[ContagemResponse])
async def get_contagens(limit: int = 100, offset: int = 0):
    """Retorna lista de contagens de pizzas"""
    if limit > 1000:
        raise HTTPException(status_code=400, detail="Limite máximo é 1000 registros")
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Paginação
        cursor.execute(
            "SELECT id, timestamp FROM contagens_pizzas ORDER BY timestamp DESC LIMIT %s OFFSET %s",
            (limit, offset)
        )
        results = cursor.fetchall()
        
        contagens_list = []
        for row in results:
            contagens_list.append(ContagemResponse(
                id=row[0],
                timestamp=row[1].isoformat()
            ))
        
        logger.info(f"Retornadas {len(contagens_list)} contagens")
        return contagens_list
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Erro ao buscar contagens: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar contagens: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.get("/contagens/estatisticas", response_model=EstatisticasResponse)
async def get_estatisticas():
    """Retorna estatísticas das contagens"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Total de contagens
        cursor.execute("SELECT COUNT(*) FROM contagens_pizzas")
        total_contagens = cursor.fetchone()[0]
        
        # Contagens hoje
        cursor.execute(
            "SELECT COUNT(*) FROM contagens_pizzas WHERE DATE(timestamp) = CURRENT_DATE"
        )
        contagens_hoje = cursor.fetchone()[0]
        
        # Última contagem
        cursor.execute(
            "SELECT timestamp FROM contagens_pizzas ORDER BY timestamp DESC LIMIT 1"
        )
        ultima_contagem = cursor.fetchone()
        ultima_contagem = ultima_contagem[0].isoformat() if ultima_contagem else None
        
        return EstatisticasResponse(
            total_contagens=total_contagens,
            contagens_hoje=contagens_hoje,
            ultima_contagem=ultima_contagem,
            timestamp_consulta=datetime.now().isoformat()
        )
        
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar estatísticas: {str(e)}")
    finally:
        if conn:
            conn.close()

# Grafana: endpoints

@app.get("/grafana/contagens-por-hora")
async def get_contagens_por_hora():
    """Endpoint para Grafana - Contagens por hora"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                EXTRACT(EPOCH FROM hora) as timestamp_unix,
                total_contagens
            FROM contagens_por_hora 
            WHERE hora >= CURRENT_DATE - INTERVAL '7 days'
            ORDER BY hora
        """)
        
        results = cursor.fetchall()
        
        datapoints = []
        for row in results:
            datapoints.append([row[1], row[0] * 1000])  # Grafana espera timestamp em ms
        
        return [{
            "target": "Pizzas por Hora",
            "datapoints": datapoints
        }]
        
    except Exception as e:
        logger.error(f"Erro ao buscar contagens por hora: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar contagens por hora: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.get("/grafana/contagens-por-dia")
async def get_contagens_por_dia():
    """Endpoint para Grafana - Contagens por dia"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                EXTRACT(EPOCH FROM data) as timestamp_unix,
                total_contagens
            FROM contagens_por_dia 
            WHERE data >= CURRENT_DATE - INTERVAL '30 days'
            ORDER BY data
        """)
        
        results = cursor.fetchall()
        
        datapoints = []
        for row in results:
            datapoints.append([row[1], row[0] * 1000])  # Grafana espera timestamp em ms
        
        return [{
            "target": "Pizzas por Dia",
            "datapoints": datapoints
        }]
        
    except Exception as e:
        logger.error(f"Erro ao buscar contagens por dia: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar contagens por dia: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.get("/grafana/velocidade-producao")
async def get_velocidade_producao():
    """Endpoint para Grafana - Velocidade de produção (pizzas por hora)"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                EXTRACT(EPOCH FROM hora) as timestamp_unix,
                pizzas_por_hora
            FROM velocidade_producao 
            ORDER BY hora
        """)
        
        results = cursor.fetchall()
        
        datapoints = []
        for row in results:
            datapoints.append([row[1], row[0] * 1000])  # Grafana espera timestamp em ms
        
        return [{
            "target": "Velocidade de Produção (pizzas/hora)",
            "datapoints": datapoints
        }]
        
    except Exception as e:
        logger.error(f"Erro ao buscar velocidade de produção: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar velocidade de produção: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.get("/grafana/estatisticas-hoje")
async def get_estatisticas_hoje():
    """Endpoint para Grafana - Estatísticas do dia atual"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM estatisticas_hoje")
        result = cursor.fetchone()
        
        if result:
            return {
                "total_contagens": result[0],
                "primeiro_horario": str(result[1]) if result[1] else None,
                "ultimo_horario": str(result[2]) if result[2] else None,
                "data": str(result[3]),
                "timestamp_unix": result[4] * 1000
            }
        else:
            return {
                "total_contagens": 0,
                "primeiro_horario": None,
                "ultimo_horario": None,
                "data": datetime.now().date().isoformat(),
                "timestamp_unix": int(datetime.now().timestamp() * 1000)
            }
        
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas do dia: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar estatísticas do dia: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.get("/grafana/ultimas-contagens")
async def get_ultimas_contagens(limit: int = Query(100, le=1000)):
    """Endpoint para Grafana - Últimas contagens em tempo real"""
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                EXTRACT(EPOCH FROM timestamp) as timestamp_unix,
                1 as contagem
            FROM contagens_pizzas 
            WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
            ORDER BY timestamp DESC 
            LIMIT %s
        """, (limit,))
        
        results = cursor.fetchall()
        
        datapoints = []
        for row in results:
            datapoints.append([row[1], row[0] * 1000])  # Grafana espera timestamp em ms
        
        return [{
            "target": "Contagens em Tempo Real",
            "datapoints": datapoints
        }]
        
    except Exception as e:
        logger.error(f"Erro ao buscar últimas contagens: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar últimas contagens: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.get("/grafana/metrics")
async def get_grafana_metrics():
    """Endpoint para listar métricas disponíveis no Grafana"""
    return {
        "metrics": [
            {
                "name": "contagens-por-hora",
                "description": "Contagens de pizzas agrupadas por hora",
                "type": "time_series",
                "url": "/grafana/contagens-por-hora"
            },
            {
                "name": "contagens-por-dia", 
                "description": "Contagens de pizzas agrupadas por dia",
                "type": "time_series",
                "url": "/grafana/contagens-por-dia"
            },
            {
                "name": "velocidade-producao",
                "description": "Velocidade de produção em pizzas por hora",
                "type": "time_series", 
                "url": "/grafana/velocidade-producao"
            },
            {
                "name": "estatisticas-hoje",
                "description": "Estatísticas do dia atual",
                "type": "single_stat",
                "url": "/grafana/estatisticas-hoje"
            },
            {
                "name": "ultimas-contagens",
                "description": "Últimas contagens em tempo real",
                "type": "time_series",
                "url": "/grafana/ultimas-contagens"
            }
        ],
        "database": "PostgreSQL",
        "views_available": [
            "contagens_por_hora",
            "contagens_por_dia", 
            "estatisticas_hoje",
            "velocidade_producao",
            "ultimas_contagens_24h"
        ]
    }

@app.get("/logs")
async def get_logs(limit: int = 100, nivel: str = None):
    """Retorna logs do sistema"""
    if limit > 500:
        raise HTTPException(status_code=400, detail="Limite máximo é 500 registros")
    
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if nivel:
            cursor.execute(
                "SELECT nivel, mensagem, origem, timestamp FROM logs_sistema WHERE nivel = %s ORDER BY timestamp DESC LIMIT %s",
                (nivel.upper(), limit)
            )
        else:
            cursor.execute(
                "SELECT nivel, mensagem, origem, timestamp FROM logs_sistema ORDER BY timestamp DESC LIMIT %s",
                (limit,)
            )
        
        results = cursor.fetchall()
        
        logs_list = []
        for row in results:
            logs_list.append({
                "nivel": row[0],
                "mensagem": row[1],
                "origem": row[2],
                "timestamp": row[3].isoformat()
            })
        
        return logs_list
        
    except Exception as e:
        logger.error(f"Erro ao buscar logs: {e}")
        raise HTTPException(status_code=500, detail=f"Erro ao buscar logs: {str(e)}")
    finally:
        if conn:
            conn.close()

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Handler global para exceções não tratadas"""
    logger.error(f"Erro não tratado: {exc}")
    log_system_event("ERROR", f"Erro não tratado: {exc}", "backend")
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Erro interno do servidor",
            detail=str(exc),
            timestamp=datetime.now().isoformat()
        ).dict()
    )