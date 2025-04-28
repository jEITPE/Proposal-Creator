import os
import sys
from dotenv import load_dotenv
from flask import Flask
from models import db
from sqlalchemy import create_engine, text
import psycopg2
import traceback

# Carregar variáveis de ambiente
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Obter configurações do banco de dados
    db_user = os.environ.get('DATABASE_USER', 'postgres')
    db_password = os.environ.get('DATABASE_PASSWORD', 'postgres')
    db_host = os.environ.get('DATABASE_HOST', 'localhost')
    db_name = os.environ.get('DATABASE_NAME', 'proposal_creator')
    db_port = os.environ.get('DATABASE_PORT', '5432')
    
    # Construir a URI usando parâmetros
    # Solução para o problema de codificação: criar o engine diretamente
    engine = create_engine(
        f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}",
        client_encoding='utf8'
    )
    
    app.config['SQLALCHEMY_DATABASE_URI'] = str(engine.url)
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE'] = engine
    
    db.init_app(app)
    return app, engine

def verificar_conexao_psycopg2():
    """Verificar se conseguimos conectar diretamente via psycopg2"""
    try:
        # Obter configurações
        db_user = os.environ.get('DATABASE_USER', 'postgres')
        db_password = os.environ.get('DATABASE_PASSWORD', 'postgres')
        db_host = os.environ.get('DATABASE_HOST', 'localhost')
        db_name = os.environ.get('DATABASE_NAME', 'proposal_creator')
        db_port = os.environ.get('DATABASE_PORT', '5432')
        
        # Tentar conexão
        print("Testando conexão direta via psycopg2...")
        
        # Alternativamente, se a senha tiver caracteres problemáticos, 
        # use uma senha temporária simples para teste
        # db_password = "senha_temporaria"  # APENAS PARA TESTE
        
        # Tentar conexão direta com parâmetros
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port
        )
        print("Conexão psycopg2 bem-sucedida!")
        conn.close()
        return True
    except Exception as e:
        print(f"Erro na conexão psycopg2: {e}")
        return False

def criar_banco_manual():
    """Criar o banco de dados manualmente, incluindo tabelas via SQL"""
    try:
        # Obter configurações
        db_user = os.environ.get('DATABASE_USER', 'postgres')
        db_password = os.environ.get('DATABASE_PASSWORD', 'postgres')
        db_host = os.environ.get('DATABASE_HOST', 'localhost')
        db_name = os.environ.get('DATABASE_NAME', 'proposal_creator')
        db_port = os.environ.get('DATABASE_PORT', '5432')
        
        # Conectar ao banco PostgreSQL sem especificar o banco (para verificar/criar)
        conn = psycopg2.connect(
            user=db_user,
            password=db_password,
            host=db_host,
            port=db_port,
            dbname='postgres'
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Verificar se o banco de dados existe
        cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{db_name}'")
        if not cursor.fetchone():
            print(f"Criando banco de dados '{db_name}'...")
            cursor.execute(f"CREATE DATABASE {db_name} WITH ENCODING 'UTF8' LC_COLLATE 'en_US.UTF-8' LC_CTYPE 'en_US.UTF-8'")
            print(f"Banco de dados '{db_name}' criado com sucesso!")
        else:
            print(f"Banco de dados '{db_name}' já existe.")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Erro ao criar banco de dados: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Iniciando criação do banco de dados...")
    
    # Tentar criar o banco de dados manualmente primeiro
    db_criado = criar_banco_manual()
    if not db_criado:
        print("Aviso: Não foi possível criar o banco de dados manualmente.")
    
    # Verificar conexão direta
    conexao_ok = verificar_conexao_psycopg2()
    if not conexao_ok:
        print("AVISO IMPORTANTE: Falha ao conectar diretamente ao banco de dados.")
        print("Sugestões:")
        print("1. Verifique se o banco PostgreSQL está em execução")
        print("2. Verifique as credenciais no arquivo .env")
        print("3. Temporariamente, troque a senha para uma contendo apenas caracteres ASCII simples")
        sys.exit(1)
    
    # Criar app e obter engine
    app, engine = create_app()
    
    # Imprimir a string de conexão (sem mostrar a senha)
    connection_string = str(engine.url)
    safe_connection = connection_string.replace(os.environ.get('DATABASE_PASSWORD', ''), '****')
    print(f"Conexão configurada: {safe_connection}")
    
    with app.app_context():
        try:
            print("Criando tabelas no banco de dados...")
            
            # Usar o engine diretamente
            db.metadata.create_all(engine)
            print("Tabelas criadas com sucesso!")
        except Exception as e:
            print(f"Erro ao criar tabelas: {e}")
            traceback.print_exc()
            sys.exit(1) 