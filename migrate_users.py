import os
import json
from flask import Flask
from models import db, Usuario, Perfil
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

# Carregar variáveis de ambiente
load_dotenv()

# Criar aplicação Flask
app = Flask(__name__)

# Configuração para PostgreSQL
db_user = os.environ.get('DATABASE_USER', 'postgres')
db_password = os.environ.get('DATABASE_PASSWORD', 'postgres')
db_host = os.environ.get('DATABASE_HOST', 'localhost')
db_name = os.environ.get('DATABASE_NAME', 'proposal_creator')
db_port = os.environ.get('DATABASE_PORT', '5432')

# URL de conexão com opcões explícitas de codificação
db_url = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Adicionar opções de engine específicas para codificação
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {
        'client_encoding': 'UTF8',
        'options': '-c client_encoding=UTF8 -c standard_conforming_strings=on'
    },
    'echo': True,  # Para debug
    'isolation_level': 'READ COMMITTED'
}

# Inicializar o banco de dados
db.init_app(app)

def migrar_usuarios():
    # Arquivo JSON de usuários
    USUARIOS_FILE = os.path.join('data', 'usuarios.json')
    
    if not os.path.exists(USUARIOS_FILE):
        print(f"Arquivo {USUARIOS_FILE} não encontrado. Nenhum usuário para migrar.")
        return
    
    try:
        with open(USUARIOS_FILE, 'r', encoding='utf-8') as f:
            usuarios_json = json.load(f)
            
        with app.app_context():
            # Criar tabelas se não existirem
            db.create_all()
            
            # Garantir que os perfis existam
            perfil_admin = Perfil.query.filter_by(nome="Governança").first()
            if not perfil_admin:
                perfil_admin = Perfil(nome="Governança")
                db.session.add(perfil_admin)
                db.session.commit()
                print("Perfil Governança criado com sucesso")
            
            perfil_usuario = Perfil.query.filter_by(nome="SE").first()
            if not perfil_usuario:
                perfil_usuario = Perfil(nome="SE")
                db.session.add(perfil_usuario)
                db.session.commit()
                print("Perfil SE criado com sucesso")
            
            # Criar outros perfis para cada tipo de usuário
            tipos_perfis = {
                'am': 'AM',
                'comercialpr': 'COMERCIALPR',
                'comercialrj': 'COMERCIALRJ',
                'comercialrs': 'COMERCIALRS',
                'comercialsp': 'COMERCIALSP',
                'se': 'SE'
            }
            
            perfis = {}
            for tipo, nome in tipos_perfis.items():
                perfil = Perfil.query.filter_by(nome=nome).first()
                if not perfil:
                    perfil = Perfil(nome=nome)
                    db.session.add(perfil)
                    db.session.commit()
                    print(f"Perfil {nome} criado com sucesso")
                perfis[tipo] = perfil.id
            
            # Adicionar perfil admin ao dicionário
            perfis['admin'] = perfil_admin.id
            
            # Migrar usuários
            usuarios_migrados = 0
            usuarios_existentes = 0
            usuarios_atualizados = 0
            
            for login, dados in usuarios_json.items():
                # Verificar se o usuário já existe
                usuario = Usuario.query.filter_by(login=login).first()
                
                # Verificar tipo de usuário e determinar perfil
                tipo = dados.get("tipo", "usuario").lower()
                id_perfil = perfis.get(tipo, perfil_usuario.id)  # Se tipo não existir, usa perfil de usuário comum
                
                # Aplicar hash à senha
                senha_texto = dados.get("senha", "")
                senha_hash = generate_password_hash(senha_texto)
                
                if not usuario:
                    # Criar novo usuário
                    novo_usuario = Usuario(
                        nome=dados.get("nome", login),
                        login=login,
                        senha=senha_hash,
                        status=dados.get("status", 1),
                        id_perfil=id_perfil
                    )
                    db.session.add(novo_usuario)
                    usuarios_migrados += 1
                    print(f"Usuário {login} migrado com sucesso")
                else:
                    # Atualizar usuário existente com hash de senha
                    if not usuario.senha.startswith('pbkdf2:sha256:'):
                        usuario.senha = senha_hash
                        usuarios_atualizados += 1
                        print(f"Senha do usuário {login} atualizada para formato hash")
                    
                    # Atualizar perfil se necessário
                    if usuario.id_perfil != id_perfil:
                        usuario.id_perfil = id_perfil
                        print(f"Perfil do usuário {login} atualizado")
                    
                    usuarios_existentes += 1
                    print(f"Usuário {login} já existe no banco de dados")
            
            db.session.commit()
            print(f"\nMigração concluída:")
            print(f"- {usuarios_migrados} usuários migrados")
            print(f"- {usuarios_existentes} usuários já existiam")
            print(f"- {usuarios_atualizados} senhas atualizadas para formato hash")
            
    except Exception as e:
        print(f"Erro ao migrar usuários: {e}")

def migrar_usuarios_do_json():
    """
    Função que pode ser importada e chamada diretamente para migrar usuários.
    Esta função é utilizada pelo agendador para sincronização periódica.
    """
    print("Iniciando migração periódica de usuários do JSON para o banco de dados...")
    
    try:
        # Arquivo JSON de usuários
        USUARIOS_FILE = os.path.join('data', 'usuarios.json')
        
        if not os.path.exists(USUARIOS_FILE):
            print(f"Arquivo {USUARIOS_FILE} não encontrado. Nenhum usuário para migrar.")
            return
        
        with open(USUARIOS_FILE, 'r', encoding='utf-8') as f:
            usuarios_json = json.load(f)
            
        # Garantir que os perfis existam
        perfil_admin = Perfil.query.filter_by(nome="Governança").first()
        if not perfil_admin:
            perfil_admin = Perfil(nome="Governança")
            db.session.add(perfil_admin)
            db.session.commit()
            print("Perfil Governança criado com sucesso")
        
        perfil_usuario = Perfil.query.filter_by(nome="SE").first()
        if not perfil_usuario:
            perfil_usuario = Perfil(nome="SE")
            db.session.add(perfil_usuario)
            db.session.commit()
            print("Perfil SE criado com sucesso")
        
        # Criar outros perfis para cada tipo de usuário
        tipos_perfis = {
            'am': 'AM',
            'comercialpr': 'COMERCIALPR',
            'comercialrj': 'COMERCIALRJ',
            'comercialrs': 'COMERCIALRS',
            'comercialsp': 'COMERCIALSP',
            'se': 'SE'
        }
        
        perfis = {}
        for tipo, nome in tipos_perfis.items():
            perfil = Perfil.query.filter_by(nome=nome).first()
            if not perfil:
                perfil = Perfil(nome=nome)
                db.session.add(perfil)
                db.session.commit()
                print(f"Perfil {nome} criado com sucesso")
            perfis[tipo] = perfil.id
        
        # Adicionar perfil admin ao dicionário
        perfis['admin'] = perfil_admin.id
        
        # Migrar usuários
        usuarios_migrados = 0
        usuarios_existentes = 0
        usuarios_atualizados = 0
        
        for login, dados in usuarios_json.items():
            # Verificar se o usuário já existe
            usuario = Usuario.query.filter_by(login=login).first()
            
            # Verificar tipo de usuário e determinar perfil
            tipo = dados.get("tipo", "usuario").lower()
            id_perfil = perfis.get(tipo, perfil_usuario.id)  # Se tipo não existir, usa perfil de usuário comum
            
            # Aplicar hash à senha
            senha_texto = dados.get("senha", "")
            senha_hash = generate_password_hash(senha_texto)
            
            if not usuario:
                # Criar novo usuário
                novo_usuario = Usuario(
                    nome=dados.get("nome", login),
                    login=login,
                    senha=senha_hash,
                    status=dados.get("status", 1),
                    id_perfil=id_perfil
                )
                db.session.add(novo_usuario)
                usuarios_migrados += 1
                print(f"Usuário {login} migrado com sucesso")
            else:
                # Atualizar usuário existente com hash de senha
                if not usuario.senha.startswith('pbkdf2:sha256:'):
                    usuario.senha = senha_hash
                    usuarios_atualizados += 1
                    print(f"Senha do usuário {login} atualizada para formato hash")
                
                # Atualizar perfil se necessário
                if usuario.id_perfil != id_perfil:
                    usuario.id_perfil = id_perfil
                    print(f"Perfil do usuário {login} atualizado")
                
                usuarios_existentes += 1
                print(f"Usuário {login} já existe no banco de dados")
        
        db.session.commit()
        print(f"\nMigração de usuários concluída:")
        print(f"- {usuarios_migrados} usuários migrados")
        print(f"- {usuarios_existentes} usuários já existiam")
        print(f"- {usuarios_atualizados} senhas atualizadas para formato hash")
            
    except Exception as e:
        print(f"Erro ao migrar usuários: {e}")
        # Em caso de erro, fazer rollback
        db.session.rollback()
        raise

if __name__ == "__main__":
    migrar_usuarios() 