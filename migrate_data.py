import os
import json
import uuid
from datetime import datetime
import sys
from dotenv import load_dotenv

# Adicione o diretório atual ao path do Python se necessário
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import db, Usuario, Perfil, BlocoProposta, Oferta, BlocoPropostaOferta, Proposta, Rascunho
from flask import Flask

def setup_app():
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Obter configurações do banco de dados
    db_user = os.environ.get('DATABASE_USER', 'postgres')
    db_password = os.environ.get('DATABASE_PASSWORD', 'postgres')
    db_host = os.environ.get('DATABASE_HOST', 'localhost')
    db_name = os.environ.get('DATABASE_NAME', 'proposal_creator')  # Nome correto do banco
    db_port = os.environ.get('DATABASE_PORT', '5432')
    
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app

def carregar_json(arquivo):
    try:
        if os.path.exists(arquivo):
            with open(arquivo, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Erro ao carregar arquivo {arquivo}: {e}")
        return {}

def migrar_perfis():
    # Criar perfis padrão
    perfis = [
        {"nome": "Governança"},
        {"nome": "AM"},
        {"nome": "SE"}
    ]
    
    for p in perfis:
        if not Perfil.query.filter_by(nome=p["nome"]).first():
            perfil = Perfil(nome=p["nome"])
            db.session.add(perfil)
    
    db.session.commit()
    print("Perfis migrados com sucesso!")

def migrar_usuarios():
    usuarios_json = carregar_json(os.path.join('data', 'usuarios.json'))
    
    # Obter perfil padrão para novos usuários
    perfil_governanca = Perfil.query.filter_by(nome="Governança").first()
    
    for login, dados in usuarios_json.items():
        # Verificar se o usuário já existe
        usuario_existente = Usuario.query.filter_by(login=login).first()
        if not usuario_existente:
            # Criar novo usuário
            usuario = Usuario(
                nome=login,
                login=login,
                senha=dados["senha"],
                status=1,  # Ativo
                id_perfil=perfil_governanca.id if perfil_governanca else 1
            )
            db.session.add(usuario)
    
    db.session.commit()
    print("Usuários migrados com sucesso!")

def migrar_ofertas():
    """
    Migra ofertas do JSON para o banco de dados.
    Esta função pode ser chamada diretamente pelo agendador.
    """
    try:
        ofertas_json = carregar_json(os.path.join('data', 'ofertas.json'))
        
        print(f"Iniciando migração periódica de {len(ofertas_json)} ofertas...")
        contador_novos = 0
        
        for tipo_oferta, dados_oferta in ofertas_json.items():
            oferta_existente = Oferta.query.filter_by(tipo_oferta=tipo_oferta).first()
            if not oferta_existente:
                # Criar nova oferta
                oferta = Oferta(tipo_oferta=tipo_oferta)
                db.session.add(oferta)
                contador_novos += 1
                
                # Após criar a oferta, podemos adicionar seus blocos associados
                db.session.flush()  # Para obter o ID da oferta
                
                # Se houver blocos específicos da oferta, processá-los
                blocos_oferta = dados_oferta.get('blocos', {})
                for nome_bloco, dados_bloco in blocos_oferta.items():
                    # Verificar se o bloco já existe
                    bloco = BlocoProposta.query.filter_by(nome=nome_bloco).first()
                    if not bloco:
                        # Criar o bloco se não existir
                        bloco = BlocoProposta(
                            nome=nome_bloco,
                            titulo=dados_bloco.get('titulo', nome_bloco.replace('_', ' ')),
                            texto=dados_bloco.get('texto', ''),
                            obrigatorio=nome_bloco in dados_oferta.get('obrigatorios', []),
                            criado_por='sistema',
                            data_criacao=datetime.utcnow()
                        )
                        db.session.add(bloco)
                        db.session.flush()
                    
                    # Associar o bloco à oferta
                    bloco_oferta = BlocoPropostaOferta.query.filter_by(
                        id_bloco=bloco.id, id_oferta=oferta.id
                    ).first()
                    
                    if not bloco_oferta:
                        bloco_oferta = BlocoPropostaOferta(
                            id_bloco=bloco.id,
                            id_oferta=oferta.id,
                            obrigatorio=nome_bloco in dados_oferta.get('obrigatorios', [])
                        )
                        db.session.add(bloco_oferta)
        
        db.session.commit()
        print(f"Migração de ofertas concluída: {contador_novos} novas ofertas adicionadas")
        return True
    except Exception as e:
        print(f"Erro ao migrar ofertas: {e}")
        db.session.rollback()
        return False

def migrar_blocos():
    """
    Migra blocos do JSON para o banco de dados.
    Esta função pode ser chamada diretamente pelo agendador.
    """
    try:
        blocos_json = carregar_json(os.path.join('data', 'blocos.json'))
        
        print(f"Iniciando migração periódica de {len(blocos_json)} blocos...")
        contador_novos = 0
        contador_atualizados = 0
        
        for nome_bloco, dados in blocos_json.items():
            # Verificar se o bloco já existe
            bloco_existente = BlocoProposta.query.filter_by(nome=nome_bloco).first()
            
            # Converter formato de data
            data_criacao = None
            if 'data_criacao' in dados:
                try:
                    data_criacao = datetime.strptime(dados['data_criacao'], '%d/%m/%Y %H:%M:%S')
                except:
                    data_criacao = datetime.utcnow()
            
            if not bloco_existente:
                # Criar novo bloco
                bloco = BlocoProposta(
                    nome=nome_bloco,
                    titulo=dados.get('titulo', nome_bloco.replace('_', ' ')),
                    texto=dados.get('texto', ''),
                    imagem=dados.get('imagem'),
                    obrigatorio=dados.get('obrigatorio', False),
                    criado_por=dados.get('criado_por'),
                    data_criacao=data_criacao or datetime.utcnow()
                )
                db.session.add(bloco)
                contador_novos += 1
            else:
                # Atualizar bloco existente se necessário
                atualizado = False
                
                # Atualizar título se necessário
                if 'titulo' in dados and bloco_existente.titulo != dados['titulo']:
                    bloco_existente.titulo = dados['titulo']
                    atualizado = True
                
                # Atualizar texto se necessário
                if 'texto' in dados and bloco_existente.texto != dados['texto']:
                    bloco_existente.texto = dados['texto']
                    atualizado = True
                
                # Atualizar obrigatoriedade se necessário
                if 'obrigatorio' in dados and bloco_existente.obrigatorio != dados['obrigatorio']:
                    bloco_existente.obrigatorio = dados['obrigatorio']
                    atualizado = True
                
                if atualizado:
                    contador_atualizados += 1
        
        db.session.commit()
        print(f"Migração de blocos concluída: {contador_novos} novos, {contador_atualizados} atualizados")
        return True
    except Exception as e:
        print(f"Erro ao migrar blocos: {e}")
        db.session.rollback()
        return False

def migrar_propostas():
    """
    Migra propostas do JSON para o banco de dados.
    Esta função pode ser chamada diretamente pelo agendador.
    """
    try:
        propostas_json = carregar_json(os.path.join('data', 'propostas.json'))
        
        print(f"Iniciando migração periódica de {len(propostas_json)} propostas...")
        contador_novos = 0
        
        for id_proposta, dados in propostas_json.items():
            # Verificar se a proposta já existe
            proposta_existente = Proposta.query.get(id_proposta)
            if not proposta_existente:
                # Converter formato de data
                data_geracao = None
                if 'data_geracao' in dados:
                    try:
                        data_geracao = datetime.strptime(dados['data_geracao'], '%d/%m/%Y %H:%M:%S')
                    except:
                        data_geracao = datetime.utcnow()
                
                # Criar nova proposta
                proposta = Proposta(
                    id=id_proposta,
                    nome_cliente=dados.get('nome_cliente', ''),
                    data_geracao=data_geracao or datetime.utcnow(),
                    gerado_por=dados.get('gerado_por', ''),
                    arquivo=dados.get('arquivo', '')
                )
                
                # Adicionar blocos utilizados
                blocos_utilizados = dados.get('blocos_utilizados', [])
                for nome_bloco in blocos_utilizados:
                    bloco = BlocoProposta.query.filter_by(nome=nome_bloco).first()
                    if bloco:
                        proposta.blocos_utilizados.append(bloco)
                
                # Adicionar oferta selecionada
                oferta_nome = dados.get('oferta_selecionada')
                if oferta_nome:
                    oferta = Oferta.query.filter_by(tipo_oferta=oferta_nome).first()
                    if oferta:
                        proposta.ofertas_selecionadas.append(oferta)
                
                db.session.add(proposta)
                contador_novos += 1
        
        db.session.commit()
        print(f"Migração de propostas concluída: {contador_novos} novas propostas adicionadas")
        return True
    except Exception as e:
        print(f"Erro ao migrar propostas: {e}")
        db.session.rollback()
        return False

def migrar_rascunhos():
    """
    Migra rascunhos do JSON para o banco de dados.
    Esta função pode ser chamada diretamente pelo agendador.
    """
    try:
        rascunhos_json = carregar_json(os.path.join('data', 'rascunhos.json'))
        
        print(f"Iniciando migração periódica de {len(rascunhos_json)} rascunhos...")
        contador_novos = 0
        
        for id_rascunho, dados in rascunhos_json.items():
            # Verificar se o rascunho já existe
            rascunho_existente = Rascunho.query.get(id_rascunho)
            if not rascunho_existente:
                # Converter formato de data
                data_atualizacao = None
                if 'data_atualizacao' in dados:
                    try:
                        data_atualizacao = datetime.strptime(dados['data_atualizacao'], '%d/%m/%Y %H:%M:%S')
                    except:
                        data_atualizacao = datetime.utcnow()
                
                # Criar novo rascunho
                blocos_selecionados = dados.get('blocos_selecionados', [])
                blocos_temporarios = dados.get('blocos_temporarios', {})
                
                rascunho = Rascunho(
                    id=id_rascunho,
                    nome_cliente=dados.get('nome_cliente', ''),
                    logo_cliente=dados.get('logo_cliente', ''),
                    modelo_proposta=dados.get('modelo_proposta', ''),
                    usuario=dados.get('usuario', ''),
                    data_atualizacao=data_atualizacao or datetime.utcnow(),
                    blocos_selecionados=blocos_selecionados,
                    blocos_temporarios=blocos_temporarios
                )
                
                db.session.add(rascunho)
                contador_novos += 1
        
        db.session.commit()
        print(f"Migração de rascunhos concluída: {contador_novos} novos rascunhos adicionados")
        return True
    except Exception as e:
        print(f"Erro ao migrar rascunhos: {e}")
        db.session.rollback()
        return False

def main():
    print("Iniciando migração dos dados JSON para o PostgreSQL...")
    
    app = setup_app()
    with app.app_context():
        # Criar todas as tabelas
        db.create_all()
        
        # Migrar dados em ordem apropriada
        migrar_perfis()
        migrar_usuarios()
        migrar_ofertas()
        migrar_blocos()
        migrar_propostas()
        migrar_rascunhos()
    
    print("Migração concluída com sucesso!")

if __name__ == "__main__":
    main() 