from datetime import datetime
import logging
import uuid
from flask import current_app
from models import db, Usuario, Perfil, BlocoProposta, Oferta, BlocoPropostaOferta, Proposta, Rascunho

logger = logging.getLogger(__name__)

# ============= FUNÇÕES DE ACESSO DIRETO AO BANCO DE DADOS =============

# ==================== USUÁRIOS ====================
def obter_usuarios_db():
    """
    Obtém todos os usuários diretamente do banco de dados.
    Retorna um dicionário de usuários no mesmo formato que era retornado pelo JSON.
    """
    usuarios = {}
    try:
        for usuario in Usuario.query.all():
            # Obter perfil do usuário
            perfil_nome = usuario.perfil.nome if usuario.perfil else "SE"
            
            # Verificar status de expiração
            status_texto = "Ativo" if usuario.status == 1 else "Inativo"
            if usuario.data_expiracao and datetime.utcnow() > usuario.data_expiracao:
                status_texto = "Expirado"
            
            # Obter blocos permitidos
            blocos_permitidos = []
            for bloco in usuario.blocos_permitidos:
                blocos_permitidos.append(bloco.nome)
            
            # Montar dicionário de usuário
            usuarios[usuario.login] = {
                "nome": usuario.nome,
                "senha": usuario.senha,
                "tipo": "admin" if perfil_nome == "Governança" else "usuario",
                "perfil": perfil_nome,
                "status": usuario.status,
                "status_texto": status_texto,
                "superusuario": usuario.superusuario,
                "data_expiracao": usuario.data_expiracao.strftime('%d/%m/%Y %H:%M:%S') if usuario.data_expiracao else None,
                "blocos_permitidos": blocos_permitidos
            }
        return usuarios
    except Exception as e:
        logger.error(f"Erro ao obter usuários do banco: {e}")
        return {}

def salvar_usuario_db(login, dados):
    """
    Salva um usuário no banco de dados.
    """
    try:
        # Verificar se o usuário já existe
        usuario = Usuario.query.filter_by(login=login).first()
        
        # Converter data de expiração se existir
        data_expiracao = None
        if "data_expiracao" in dados and dados["data_expiracao"]:
            try:
                data_expiracao = datetime.strptime(dados["data_expiracao"], '%d/%m/%Y %H:%M:%S')
            except:
                pass
        
        # Obter perfil
        tipo = dados.get("tipo", "usuario")
        perfil_nome = "Governança" if tipo == "admin" else tipo.upper()
        perfil = Perfil.query.filter_by(nome=perfil_nome).first()
        
        # Criar perfil se não existir
        if not perfil:
            perfil = Perfil(nome=perfil_nome)
            db.session.add(perfil)
            db.session.flush()
        
        if usuario:
            # Atualizar usuário existente
            usuario.nome = dados.get("nome", login)
            if "senha" in dados:
                usuario.senha = dados["senha"]
            usuario.status = dados.get("status", 1)
            usuario.id_perfil = perfil.id
            usuario.superusuario = dados.get("superusuario", False)
            usuario.data_expiracao = data_expiracao
            
            # Atualizar blocos permitidos
            if "blocos_permitidos" in dados:
                usuario.blocos_permitidos = []
                for nome_bloco in dados["blocos_permitidos"]:
                    bloco = BlocoProposta.query.filter_by(nome=nome_bloco).first()
                    if bloco:
                        usuario.blocos_permitidos.append(bloco)
        else:
            # Criar novo usuário
            novo_usuario = Usuario(
                nome=dados.get("nome", login),
                login=login,
                senha=dados["senha"],
                status=dados.get("status", 1),
                id_perfil=perfil.id,
                superusuario=dados.get("superusuario", False),
                data_expiracao=data_expiracao
            )
            
            # Adicionar blocos permitidos
            for nome_bloco in dados.get("blocos_permitidos", []):
                bloco = BlocoProposta.query.filter_by(nome=nome_bloco).first()
                if bloco:
                    novo_usuario.blocos_permitidos.append(bloco)
            
            db.session.add(novo_usuario)
        
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar usuário no banco: {e}")
        db.session.rollback()
        return False

# ==================== BLOCOS ====================
def obter_blocos_db():
    """
    Obtém todos os blocos de proposta diretamente do banco de dados.
    Retorna um dicionário de blocos no mesmo formato que era retornado pelo JSON.
    """
    blocos = {}
    try:
        for bloco in BlocoProposta.query.all():
            # Obter usuários permitidos
            usuarios_permitidos = []
            for usuario in bloco.usuarios_com_acesso:
                usuarios_permitidos.append(usuario.login)
                
            # Montar dicionário de bloco
            blocos[bloco.nome] = {
                "titulo": bloco.titulo or bloco.nome.replace('_', ' '),
                "texto": bloco.texto or "",
                "imagem": bloco.imagem,
                "obrigatorio": bloco.obrigatorio,
                "criado_por": bloco.criado_por,
                "data_criacao": bloco.data_criacao.strftime('%d/%m/%Y %H:%M:%S') if bloco.data_criacao else "",
                "usuarios_permitidos": usuarios_permitidos
            }
        return blocos
    except Exception as e:
        logger.error(f"Erro ao obter blocos do banco: {e}")
        return {}

def salvar_bloco_db(nome_bloco, dados):
    """
    Salva um bloco no banco de dados.
    """
    try:
        # Verificar se o bloco já existe
        bloco = BlocoProposta.query.filter_by(nome=nome_bloco).first()
        
        # Converter data de criação se existir
        data_criacao = None
        if "data_criacao" in dados:
            try:
                data_criacao = datetime.strptime(dados["data_criacao"], '%d/%m/%Y %H:%M:%S')
            except:
                data_criacao = datetime.utcnow()
        
        if bloco:
            # Atualizar bloco existente
            bloco.titulo = dados.get("titulo", nome_bloco.replace('_', ' '))
            bloco.texto = dados.get("texto", "")
            bloco.imagem = dados.get("imagem")
            bloco.obrigatorio = dados.get("obrigatorio", False)
            
            # Só atualizar criador se não existir
            if not bloco.criado_por and "criado_por" in dados:
                bloco.criado_por = dados["criado_por"]
                
            # Só atualizar data se não existir
            if not bloco.data_criacao and data_criacao:
                bloco.data_criacao = data_criacao
        else:
            # Criar novo bloco
            novo_bloco = BlocoProposta(
                nome=nome_bloco,
                titulo=dados.get("titulo", nome_bloco.replace('_', ' ')),
                texto=dados.get("texto", ""),
                imagem=dados.get("imagem"),
                obrigatorio=dados.get("obrigatorio", False),
                criado_por=dados.get("criado_por"),
                data_criacao=data_criacao or datetime.utcnow()
            )
            db.session.add(novo_bloco)
            db.session.flush()
            bloco = novo_bloco
        
        # Atualizar usuários permitidos se indicado
        if "usuarios_permitidos" in dados:
            # Limpar permissões existentes
            for usuario in bloco.usuarios_com_acesso:
                usuario.blocos_permitidos.remove(bloco)
                
            # Adicionar novas permissões
            for login in dados["usuarios_permitidos"]:
                usuario = Usuario.query.filter_by(login=login).first()
                if usuario:
                    usuario.blocos_permitidos.append(bloco)
        
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar bloco no banco: {e}")
        db.session.rollback()
        return False

# ==================== OFERTAS ====================
def obter_ofertas_db():
    """
    Obtém todas as ofertas diretamente do banco de dados.
    Retorna um dicionário de ofertas no mesmo formato que era retornado pelo JSON.
    """
    ofertas = {}
    try:
        for oferta in Oferta.query.all():
            # Obter blocos associados à oferta
            blocos_oferta = {}
            obrigatorios = []
            
            # Obter associações bloco-oferta
            associacoes = BlocoPropostaOferta.query.filter_by(id_oferta=oferta.id).all()
            for assoc in associacoes:
                bloco = BlocoProposta.query.get(assoc.id_bloco)
                if bloco:
                    blocos_oferta[bloco.nome] = {
                        "titulo": bloco.titulo or bloco.nome.replace('_', ' '),
                        "texto": bloco.texto
                    }
                    if assoc.obrigatorio:
                        obrigatorios.append(bloco.nome)
            
            # Montar dicionário da oferta
            ofertas[oferta.tipo_oferta] = {
                "blocos": blocos_oferta,
                "obrigatorios": obrigatorios
            }
        
        return ofertas
    except Exception as e:
        logger.error(f"Erro ao obter ofertas do banco: {e}")
        return {}

def salvar_oferta_db(tipo_oferta, dados):
    """
    Salva uma oferta no banco de dados.
    """
    try:
        # Verificar se a oferta já existe
        oferta = Oferta.query.filter_by(tipo_oferta=tipo_oferta).first()
        
        if not oferta:
            # Criar nova oferta
            oferta = Oferta(tipo_oferta=tipo_oferta)
            db.session.add(oferta)
            db.session.flush()  # Para obter o ID da oferta
        
        # Processar blocos da oferta
        for nome_bloco, dados_bloco in dados.get('blocos', {}).items():
            # Verificar se o bloco já existe
            bloco = BlocoProposta.query.filter_by(nome=nome_bloco).first()
            if not bloco:
                # Criar o bloco se não existir
                bloco = BlocoProposta(
                    nome=nome_bloco,
                    titulo=dados_bloco.get('titulo', nome_bloco.replace('_', ' ')),
                    texto=dados_bloco.get('texto', ''),
                    obrigatorio=nome_bloco in dados.get('obrigatorios', []),
                    criado_por='sistema',
                    data_criacao=datetime.utcnow()
                )
                db.session.add(bloco)
                db.session.flush()
            
            # Verificar se o bloco já está associado à oferta
            associacao = BlocoPropostaOferta.query.filter_by(
                id_bloco=bloco.id, id_oferta=oferta.id
            ).first()
            
            if not associacao:
                # Criar a associação se não existir
                associacao = BlocoPropostaOferta(
                    id_bloco=bloco.id,
                    id_oferta=oferta.id,
                    obrigatorio=nome_bloco in dados.get('obrigatorios', [])
                )
                db.session.add(associacao)
        
        db.session.commit()
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar oferta no banco: {e}")
        db.session.rollback()
        return False

# ==================== PROPOSTAS ====================
def obter_propostas_db():
    """
    Obtém todas as propostas diretamente do banco de dados.
    Retorna um dicionário de propostas no mesmo formato que era retornado pelo JSON.
    """
    propostas = {}
    try:
        for proposta in Proposta.query.all():
            # Converter data para string
            data_str = proposta.data_geracao.strftime('%d/%m/%Y %H:%M:%S') if proposta.data_geracao else ""
            
            # Obter blocos utilizados
            blocos_utilizados = []
            for bloco in proposta.blocos_utilizados:
                blocos_utilizados.append(bloco.nome)
            
            # Obter oferta selecionada
            oferta_selecionada = None
            if proposta.ofertas_selecionadas and len(proposta.ofertas_selecionadas) > 0:
                oferta_selecionada = proposta.ofertas_selecionadas[0].tipo_oferta
            
            # Montar dicionário da proposta
            propostas[proposta.id] = {
                "nome_cliente": proposta.nome_cliente,
                "data_geracao": data_str,
                "gerado_por": proposta.gerado_por,
                "arquivo": proposta.arquivo,
                "blocos_utilizados": blocos_utilizados,
                "oferta_selecionada": oferta_selecionada
            }
        
        return propostas
    except Exception as e:
        logger.error(f"Erro ao obter propostas do banco: {e}")
        return {}

def salvar_proposta_db(id_proposta, dados):
    """
    Salva uma proposta no banco de dados.
    """
    try:
        # Verificar se a proposta já existe
        proposta = Proposta.query.get(id_proposta)
        
        # Converter data para datetime
        data_geracao = None
        if "data_geracao" in dados:
            try:
                data_geracao = datetime.strptime(dados["data_geracao"], '%d/%m/%Y %H:%M:%S')
            except:
                data_geracao = datetime.utcnow()
        
        if proposta:
            # Atualizar proposta existente
            proposta.nome_cliente = dados.get("nome_cliente", "")
            proposta.data_geracao = data_geracao or datetime.utcnow()
            proposta.gerado_por = dados.get("gerado_por", "")
            proposta.arquivo = dados.get("arquivo", "")
            
            # Atualizar blocos utilizados
            proposta.blocos_utilizados.clear()
            for nome_bloco in dados.get("blocos_utilizados", []):
                bloco = BlocoProposta.query.filter_by(nome=nome_bloco).first()
                if bloco:
                    proposta.blocos_utilizados.append(bloco)
            
            # Atualizar oferta selecionada
            proposta.ofertas_selecionadas.clear()
            oferta_nome = dados.get("oferta_selecionada")
            if oferta_nome:
                oferta = Oferta.query.filter_by(tipo_oferta=oferta_nome).first()
                if oferta:
                    proposta.ofertas_selecionadas.append(oferta)
        else:
            # Criar nova proposta
            nova_proposta = Proposta(
                id=id_proposta,
                nome_cliente=dados.get("nome_cliente", ""),
                data_geracao=data_geracao or datetime.utcnow(),
                gerado_por=dados.get("gerado_por", ""),
                arquivo=dados.get("arquivo", "")
            )
            
            # Adicionar blocos utilizados
            for nome_bloco in dados.get("blocos_utilizados", []):
                bloco = BlocoProposta.query.filter_by(nome=nome_bloco).first()
                if bloco:
                    nova_proposta.blocos_utilizados.append(bloco)
            
            # Adicionar oferta selecionada
            oferta_nome = dados.get("oferta_selecionada")
            if oferta_nome:
                oferta = Oferta.query.filter_by(tipo_oferta=oferta_nome).first()
                if oferta:
                    nova_proposta.ofertas_selecionadas.append(oferta)
            
            db.session.add(nova_proposta)
        
        db.session.commit()
        return id_proposta
    except Exception as e:
        logger.error(f"Erro ao salvar proposta no banco: {e}")
        db.session.rollback()
        return None

def criar_proposta_db(nome_cliente, arquivo, gerado_por, blocos_selecionados, oferta_selecionada=None):
    """
    Cria uma nova proposta no banco de dados.
    Retorna o ID da proposta criada.
    """
    try:
        # Gerar ID único
        proposta_id = str(uuid.uuid4())
        
        dados = {
            "nome_cliente": nome_cliente,
            "data_geracao": datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            "gerado_por": gerado_por,
            "arquivo": arquivo,
            "blocos_utilizados": blocos_selecionados,
            "oferta_selecionada": oferta_selecionada
        }
        
        return salvar_proposta_db(proposta_id, dados)
    except Exception as e:
        logger.error(f"Erro ao criar proposta no banco: {e}")
        return None

# ==================== RASCUNHOS ====================
def obter_rascunhos_db():
    """
    Obtém todos os rascunhos diretamente do banco de dados.
    Retorna um dicionário de rascunhos no mesmo formato que era retornado pelo JSON.
    """
    rascunhos = {}
    try:
        for rascunho in Rascunho.query.all():
            # Converter data para string
            data_str = rascunho.data_atualizacao.strftime('%d/%m/%Y %H:%M:%S') if rascunho.data_atualizacao else ""
            
            # Montar dicionário do rascunho
            rascunhos[rascunho.id] = {
                "nome_cliente": rascunho.nome_cliente,
                "logo_cliente": rascunho.logo_cliente,
                "modelo_proposta": rascunho.modelo_proposta,
                "blocos_selecionados": rascunho.blocos_selecionados if rascunho.blocos_selecionados else [],
                "blocos_temporarios": rascunho.blocos_temporarios if rascunho.blocos_temporarios else {},
                "usuario": rascunho.usuario,
                "data_atualizacao": data_str
            }
        
        return rascunhos
    except Exception as e:
        logger.error(f"Erro ao obter rascunhos do banco: {e}")
        return {}

def salvar_rascunho_db(id_rascunho, dados):
    """
    Salva um rascunho no banco de dados.
    """
    try:
        # Verificar se o rascunho já existe
        rascunho = Rascunho.query.get(id_rascunho)
        
        # Converter data para datetime
        data_atualizacao = None
        if "data_atualizacao" in dados:
            try:
                data_atualizacao = datetime.strptime(dados["data_atualizacao"], '%d/%m/%Y %H:%M:%S')
            except:
                data_atualizacao = datetime.utcnow()
        
        if rascunho:
            # Atualizar rascunho existente
            rascunho.nome_cliente = dados.get("nome_cliente", "")
            rascunho.logo_cliente = dados.get("logo_cliente", "")
            rascunho.modelo_proposta = dados.get("modelo_proposta", "")
            rascunho.usuario = dados.get("usuario", "")
            rascunho.data_atualizacao = data_atualizacao or datetime.utcnow()
            rascunho.blocos_selecionados = dados.get("blocos_selecionados", [])
            rascunho.blocos_temporarios = dados.get("blocos_temporarios", {})
        else:
            # Criar novo rascunho
            novo_rascunho = Rascunho(
                id=id_rascunho,
                nome_cliente=dados.get("nome_cliente", ""),
                logo_cliente=dados.get("logo_cliente", ""),
                modelo_proposta=dados.get("modelo_proposta", ""),
                usuario=dados.get("usuario", ""),
                data_atualizacao=data_atualizacao or datetime.utcnow(),
                blocos_selecionados=dados.get("blocos_selecionados", []),
                blocos_temporarios=dados.get("blocos_temporarios", {})
            )
            db.session.add(novo_rascunho)
        
        db.session.commit()
        return id_rascunho
    except Exception as e:
        logger.error(f"Erro ao salvar rascunho no banco: {e}")
        db.session.rollback()
        return None 