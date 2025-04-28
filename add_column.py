from app import app, db
import sqlite3

with app.app_context():
    try:
        # Verificar se a coluna existe (método SQLite)
        cursor = db.session.connection().connection.cursor()
        cursor.execute("PRAGMA table_info(usuario)")
        colunas = cursor.fetchall()
        
        # Verificar se a coluna data_criacao existe
        coluna_existe = any(coluna[1] == 'data_criacao' for coluna in colunas)
        
        if not coluna_existe:
            # Adicionar a coluna se não existir
            from sqlalchemy import text
            alter_query = text("ALTER TABLE usuario ADD COLUMN data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL")
            db.session.execute(alter_query)
            db.session.commit()
            print("Coluna data_criacao adicionada com sucesso!")
        else:
            print("A coluna data_criacao já existe na tabela usuario.")
    except Exception as e:
        print(f"Erro ao adicionar coluna: {e}") 