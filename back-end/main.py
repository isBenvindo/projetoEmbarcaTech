from fastapi import FastAPI, HTTPException
import psycopg2
from psycopg2 import Error
import os
import time

from mqtt_client import start_mqtt_client

app = FastAPI()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "terelina_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "caclopool")
DB_PORT = os.getenv("DB_PORT", "5432")

mqtt_client_instance = None 

def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        return conn
    except Error as e:
        print(f"Erro ao conectar ao PostgreSQL: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno do servidor ao conectar ao DB: {e}")

@app.on_event("startup")
async def startup_event():
    global mqtt_client_instance
    print("Iniciando aplicação FastAPI e cliente MQTT...")
    mqtt_client_instance = start_mqtt_client(get_db_connection)
    print("Cliente MQTT iniciado.")

@app.on_event("shutdown")
async def shutdown_event():
    global mqtt_client_instance
    print("Encerrando aplicação FastAPI e cliente MQTT...")
    if mqtt_client_instance:
        mqtt_client_instance.loop_stop()
        mqtt_client_instance.disconnect()
        print("Cliente MQTT encerrado.")

@app.get("/")
async def read_root():
    return {"message": "Bem-vindo ao Backend de Contagem de Pizzas da Terelina!"}

@app.get("/test_db_connection")
async def test_db_connection():
    conn = None
    try:
        conn = get_db_connection()
        if conn:
            return {"status": "success", "message": "Conexão com o PostgreSQL estabelecida com sucesso!"}
        else: 
            return {"status": "error", "message": "Falha ao estabelecer conexão com o PostgreSQL."}
    except HTTPException as e:
        return {"status": "error", "message": e.detail}
    except Exception as e:
        return {"status": "error", "message": f"Um erro inesperado ocorreu: {str(e)}"}
    finally:
        if conn:
            conn.close()

@app.get("/contagens")
async def get_contagens():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, timestamp, quantidade_pizzas FROM contagens_pizzas ORDER BY timestamp DESC LIMIT 100")
        results = cursor.fetchall()
        
        contagens_list = []
        for row in results:
            contagens_list.append({
                "id": row[0],
                "timestamp": row[1].isoformat(),
                "quantidade_pizzas": row[2]
            })
        return contagens_list
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar contagens: {str(e)}")
    finally:
        if conn:
            conn.close()