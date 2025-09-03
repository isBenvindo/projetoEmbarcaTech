import psycopg2
import os
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações do banco de dados (as mesmas do seu main.py)
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "terelina_db")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "caclopool")
DB_PORT = os.getenv("DB_PORT", "5432")

def populate_db():
    conn = None
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        cursor = conn.cursor()

        print("Populando o banco de dados com 300 registros de teste...")
        base_timestamp = datetime.now() - timedelta(days=30) # Inicia 30 dias atrás

        for i in range(300):
            # Cria um timestamp aleatório dentro de uma janela de tempo
            random_hours = random.randint(0, 23)
            random_minutes = random.randint(0, 59)
            random_seconds = random.randint(0, 59)
            timestamp = base_timestamp + timedelta(days=i // 10, hours=random_hours, minutes=random_minutes, seconds=random_seconds)

            cursor.execute("INSERT INTO contagens_pizzas (timestamp) VALUES (%s)", (timestamp,))
        
        conn.commit()
        cursor.close()
        print("Banco de dados populado com sucesso!")

    except psycopg2.Error as e:
        print(f"Erro ao popular o banco de dados: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    populate_db()