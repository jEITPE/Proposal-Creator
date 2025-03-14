import os
import re
import base64
import uuid
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from flask import Flask, render_template, request, redirect, url_for, send_file, abort, jsonify, session, flash
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_PARAGRAPH_ALIGNMENT, WD_ALIGN_PARAGRAPH
from docx.enum.section import WD_SECTION_START
from bs4 import BeautifulSoup
import json
from functools import wraps
import datetime
import shutil
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from docx.oxml.ns import nsdecls, qn
from docx.oxml import parse_xml
import html
import logging
from docxtpl import DocxTemplate, InlineImage  # Importar DocxTemplate e InlineImage

logging.basicConfig(level=logging.INFO)

app = Flask("Gerador de Propostas de Serviços Gerenciados Service IT")
app.config['IMAGE_FOLDER'] = 'static/img'
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')
app.config['SECRET_KEY'] = 'service_it_secret_key'  # Chave para sessões
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
os.makedirs(app.config['IMAGE_FOLDER'], exist_ok=True)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Arquivo para armazenar usuários
USUARIOS_FILE = os.path.join('data', 'usuarios.json')

# Arquivo para armazenar ofertas
OFERTAS_FILE = os.path.join('data', 'ofertas.json')

# Extensões permitidas para upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Função para carregar usuários
def carregar_usuarios():
    if os.path.exists(USUARIOS_FILE):
        try:
            with open(USUARIOS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {"admin": {"senha": "admin123", "tipo": "admin"}}
    else:
        # Criar arquivo de usuários com admin padrão
        usuarios = {"admin": {"senha": "admin123", "tipo": "admin"}}
        os.makedirs(os.path.dirname(USUARIOS_FILE), exist_ok=True)
        with open(USUARIOS_FILE, 'w', encoding='utf-8') as f:
            json.dump(usuarios, f, ensure_ascii=False, indent=4)
        return usuarios

# Função para salvar usuários
def salvar_usuarios(usuarios):
    os.makedirs(os.path.dirname(USUARIOS_FILE), exist_ok=True)
    with open(USUARIOS_FILE, 'w', encoding='utf-8') as f:
        json.dump(usuarios, f, ensure_ascii=False, indent=4)

# Arquivo para armazenar propostas
PROPOSTAS_FILE = os.path.join('data', 'propostas.json')

# Função para carregar propostas
def carregar_propostas():
    if os.path.exists(PROPOSTAS_FILE):
        try:
            with open(PROPOSTAS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    else:
        # Criar arquivo de propostas vazio
        propostas = {}
        os.makedirs(os.path.dirname(PROPOSTAS_FILE), exist_ok=True)
        with open(PROPOSTAS_FILE, 'w', encoding='utf-8') as f:
            json.dump(propostas, f, ensure_ascii=False, indent=4)
        return propostas

# Função para salvar propostas
def salvar_propostas(propostas):
    os.makedirs(os.path.dirname(PROPOSTAS_FILE), exist_ok=True)
    with open(PROPOSTAS_FILE, 'w', encoding='utf-8') as f:
        json.dump(propostas, f, ensure_ascii=False, indent=4)

# Arquivo para armazenar blocos
BLOCOS_FILE = os.path.join('data', 'blocos.json')

# Função para carregar blocos de conteúdo do arquivo JSON
def carregar_blocos():
    try:
        if os.path.exists(BLOCOS_FILE):
            with open(BLOCOS_FILE, "r", encoding="utf-8") as f:
                blocos = json.load(f)
                app.logger.info(f"Blocos carregados com sucesso: {len(blocos)} blocos encontrados")
                return blocos
        else:
            app.logger.warning(f"Arquivo de blocos não encontrado: {BLOCOS_FILE}")
            # Criar arquivo de blocos vazio
            blocos = {}
            os.makedirs(os.path.dirname(BLOCOS_FILE), exist_ok=True)
            with open(BLOCOS_FILE, "w", encoding="utf-8") as f:
                json.dump(blocos, f, ensure_ascii=False, indent=4)
            app.logger.info(f"Arquivo de blocos criado: {BLOCOS_FILE}")
            return blocos
    except json.JSONDecodeError as e:
        app.logger.error(f"Erro ao ler blocos.json: {e}")
        return {}
    except Exception as e:
        app.logger.error(f"Erro inesperado ao carregar blocos: {e}")
        return {}

# Função para salvar os blocos de conteúdo no arquivo JSON
def salvar_blocos(blocos):
    try:
        os.makedirs(os.path.dirname(BLOCOS_FILE), exist_ok=True)
        with open(BLOCOS_FILE, "w", encoding="utf-8") as f:
            json.dump(blocos, f, ensure_ascii=False, indent=4)
        app.logger.info(f"Blocos salvos com sucesso: {len(blocos)} blocos")
        return True
    except Exception as e:
        app.logger.error(f"Erro ao salvar blocos.json: {e}")
        return False

# Função para carregar rascunhos
def carregar_rascunhos():
    rascunhos_path = os.path.join(app.root_path, 'data', 'rascunhos.json')
    if not os.path.exists(rascunhos_path):
        return {}
    with open(rascunhos_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# Função para salvar rascunhos
def salvar_rascunhos(rascunhos):
    with open(os.path.join(app.root_path, 'data', 'rascunhos.json'), 'w', encoding='utf-8') as f:
        json.dump(rascunhos, f, ensure_ascii=False, indent=4)

# Decorator para verificar se o usuário está logado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_logado' not in session:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Decorator para verificar se o usuário é admin
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_logado' not in session:
            return redirect(url_for('login', next=request.url))
        
        usuarios = carregar_usuarios()
        if session['usuario_logado'] not in usuarios or usuarios[session['usuario_logado']]['tipo'] != 'admin':
            flash('Acesso negado. Você precisa ser administrador para acessar esta página.', 'danger')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

# Rota de login
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Se o usuário já estiver logado, redireciona para o dashboard
    if 'usuario_logado' in session:
        return redirect(url_for('dashboard'))
        
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        usuarios = carregar_usuarios()
        if username in usuarios and usuarios[username]['senha'] == password:
            session['usuario_logado'] = username
            session['tipo_usuario'] = usuarios[username]['tipo']
            return redirect(url_for('dashboard'))
        else:
            error = 'Usuário ou senha inválidos. Tente novamente.'
    
    return render_template('login.html', error=error)

# Rota de logout
@app.route('/logout')
def logout():
    session.pop('usuario_logado', None)
    session.pop('tipo_usuario', None)
    return redirect(url_for('login'))

# Rota para o dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    # Carregar propostas existentes
    propostas = carregar_propostas()
    
    # Carregar rascunhos do usuário
    rascunhos = carregar_rascunhos()
    rascunhos_usuario = {}
    
    # Filtrar rascunhos do usuário atual
    for rascunho_id, rascunho in rascunhos.items():
        if rascunho.get('usuario') == session.get('usuario_logado'):
            rascunhos_usuario[rascunho_id] = rascunho
    
    # Contar propostas de hoje
    hoje = datetime.datetime.now().strftime("%d/%m/%Y")
    propostas_hoje = 0
    for proposta in propostas.values():
        if hoje in proposta.get('data_geracao', ''):
            propostas_hoje += 1
    
    # Verificar tipo de usuário para permissões
    tipo_usuario = session.get('tipo_usuario', 'usuario')
    
    return render_template('dashboard.html', 
                          propostas=propostas, 
                          rascunhos_usuario=rascunhos_usuario, 
                          tipo_usuario=tipo_usuario,
                          propostas_hoje=propostas_hoje)

# Rota para visualizar uma proposta específica
@app.route('/visualizar_proposta/<proposta_id>')
@login_required
def visualizar_proposta(proposta_id):
    propostas = carregar_propostas()
    if proposta_id in propostas:
        proposta = propostas[proposta_id]
        
        # Carregar blocos específicos para este cliente
        blocos = carregar_blocos()
        blocos_cliente = []
        
        # Filtrar blocos específicos para este cliente
        for nome_bloco, info_bloco in blocos.items():
            if info_bloco.get('cliente_associado') == proposta['nome_cliente']:
                blocos_cliente.append(nome_bloco)
        
        return render_template('visualizar_proposta.html', 
                              proposta=proposta,
                              proposta_id=proposta_id,
                              blocos_cliente=blocos_cliente)
    else:
        flash('Proposta não encontrada.')
        return redirect(url_for('dashboard'))

# Rota para baixar uma proposta
@app.route('/baixar_proposta/<proposta_id>')
@login_required
def baixar_proposta(proposta_id):
    propostas = carregar_propostas()
    if proposta_id in propostas:
        proposta = propostas[proposta_id]
        arquivo = proposta.get('arquivo', '')
        if arquivo and os.path.exists(arquivo):
            return send_file(arquivo, as_attachment=True)
        else:
            flash('Arquivo da proposta não encontrado.')
    else:
        flash('Proposta não encontrada.')
    return redirect(url_for('dashboard'))

# Rota para excluir uma proposta
@app.route('/excluir_proposta/<proposta_id>')
@login_required
def excluir_proposta(proposta_id):
    propostas = carregar_propostas()
    if proposta_id in propostas:
        # Verificar se o usuário é admin ou o criador da proposta
        if session.get('tipo_usuario') == 'admin' or propostas[proposta_id].get('gerado_por') == session.get('usuario_logado'):
            # Remover o arquivo se existir
            arquivo = propostas[proposta_id].get('arquivo', '')
            if arquivo and os.path.exists(arquivo):
                try:
                    os.remove(arquivo)
                except:
                    pass
            # Remover a proposta do dicionário
            del propostas[proposta_id]
            # Salvar as alterações
            salvar_propostas(propostas)
            flash('Proposta excluída com sucesso.')
        else:
            flash('Você não tem permissão para excluir esta proposta.')
    else:
        flash('Proposta não encontrada.')
    return redirect(url_for('dashboard'))

# Rota para criar uma nova proposta (exibir formulário)
@app.route('/criar_proposta', methods=['GET'])
@login_required
def exibir_criar_proposta():
    # Verificar se é uma nova proposta (reiniciar)
    reiniciar = request.args.get('reiniciar', 'false') == 'true'
    
    # Obter o cliente da URL, se fornecido
    cliente = request.args.get('cliente', '')
    
    # Carregar blocos disponíveis
    blocos = carregar_blocos()
    
    # Carregar ofertas disponíveis
    ofertas = carregar_ofertas()
    
    # Carregar rascunhos
    rascunhos = carregar_rascunhos()
    
    # Verificar se há um rascunho para este cliente
    rascunho = None
    rascunho_id = None
    
    if not reiniciar and cliente:
        # Procurar rascunho para este cliente
        for r_id, r_data in rascunhos.items():
            if r_data.get('nome_cliente') == cliente:
                rascunho = r_data
                rascunho_id = r_id
                break
    
    # Adicionar mensagem informativa sobre o formato das variáveis
    flash('Lembre-se: Use {{NOME_CLIENTE}} para o nome do cliente e {{logo_cliente}} para o logo na capa.')
    
    # Preparar dados para o template
    template_data = {
        'cliente': cliente,
        'blocos': blocos,
        'ofertas': ofertas,
        'rascunho': rascunho or {},
        'rascunho_id': rascunho_id
    }
    
    # Adicionar blocos específicos do cliente
    blocos_cliente = []
    for bloco_nome, bloco_info in blocos.items():
        if bloco_info.get('cliente_associado') == cliente:
            blocos_cliente.append(bloco_nome)
    
    template_data['blocos_cliente'] = blocos_cliente
    
    return render_template('criar_proposta.html', **template_data)

# Rota para processar a criação de uma proposta
@app.route('/criar_proposta', methods=['POST'])
@login_required
def criar_proposta():
    nome_cliente = request.form.get('nome_cliente', '')
    
    # Verificar se o nome do cliente foi fornecido
    if not nome_cliente:
        flash('Nome do cliente é obrigatório.')
        return redirect(url_for('exibir_criar_proposta'))
    
    # Verificar se há um rascunho para salvar
    rascunho_id = request.form.get('rascunho_id')
    
    # Obter os blocos selecionados
    blocos_selecionados = request.form.getlist('blocos')
    
    # Obter a oferta selecionada
    oferta_selecionada = request.form.get('oferta')
    
    # Verificar se há um logo para o cliente
    logo_path = None
    logo_atual = request.form.get('logo_atual')
    
    if 'logo_cliente' in request.files and request.files['logo_cliente'].filename:
        logo_file = request.files['logo_cliente']
        if logo_file and allowed_file(logo_file.filename):
            # Salvar o arquivo
            filename = secure_filename(logo_file.filename)
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            logo_file.save(logo_path)
            logging.info(f"Logo salvo em: {logo_path}")
    elif logo_atual:
        # Usar o logo atual se disponível
        logo_path = os.path.join(app.root_path, logo_atual)
    
    # Carregar os blocos disponíveis
    blocos = carregar_blocos()
    
    # Carregar ofertas disponíveis
    ofertas = carregar_ofertas()
    
    # Verificar se há oferta selecionada para incluir os blocos obrigatórios
    blocos_obrigatorios = []
    if oferta_selecionada and oferta_selecionada in ofertas:
        blocos_obrigatorios = ofertas[oferta_selecionada].get('obrigatorios', [])
        logging.info(f"Blocos obrigatórios da oferta '{oferta_selecionada}': {blocos_obrigatorios}")
        
        # Adicionar blocos obrigatórios à lista se ainda não estiverem lá
        for bloco_obrigatorio in blocos_obrigatorios:
            if bloco_obrigatorio not in blocos_selecionados:
                blocos_selecionados.append(bloco_obrigatorio)
                logging.info(f"Adicionando bloco obrigatório: {bloco_obrigatorio}")
    
    # Adicionar blocos específicos do cliente
    for bloco_nome, bloco_info in blocos.items():
        if bloco_info.get('cliente_associado') == nome_cliente and bloco_nome not in blocos_selecionados:
            blocos_selecionados.append(bloco_nome)
            logging.info(f"Adicionando bloco específico do cliente à lista de selecionados: {bloco_nome}")
    
    # Verificar se há blocos selecionados
    if not blocos_selecionados:
        flash('Selecione pelo menos um bloco para gerar a proposta.')
        return redirect(url_for('exibir_criar_proposta', cliente=nome_cliente))
    
    # Gerar a proposta
    try:
        arquivo_gerado, filename = gerar_proposta(nome_cliente, logo_path, None, blocos_selecionados, oferta_selecionada)
        
        # Criar registro da proposta
        propostas = carregar_propostas()
        proposta_id = str(uuid.uuid4())
        propostas[proposta_id] = {
            'nome_cliente': nome_cliente,
            'data_geracao': datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'gerado_por': session.get('usuario_logado', 'Desconhecido'),
            'arquivo': arquivo_gerado,
            'blocos_utilizados': blocos_selecionados,
            'oferta_selecionada': oferta_selecionada
        }
        salvar_propostas(propostas)
        
        # Se havia um rascunho, excluí-lo
        if rascunho_id:
            rascunhos = carregar_rascunhos()
            if rascunho_id in rascunhos:
                del rascunhos[rascunho_id]
                salvar_rascunhos(rascunhos)
                logging.info(f"Rascunho {rascunho_id} excluído após geração da proposta")
        
        flash('Proposta gerada com sucesso!')
        return redirect(url_for('visualizar_proposta', proposta_id=proposta_id))
    except Exception as e:
        logging.error(f"Erro ao gerar proposta: {str(e)}")
        flash(f'Erro ao gerar proposta: {str(e)}')
        return redirect(url_for('exibir_criar_proposta', cliente=nome_cliente))

# Função para criar imagem placeholder
def criar_imagem_placeholder(caminho, texto, largura=500, altura=200, cor_fundo=(0, 0, 0), cor_texto=(255, 255, 255)):
    """
    Cria uma imagem placeholder com texto centralizado.
    
    Args:
        caminho: Caminho onde a imagem será salva
        texto: Texto a ser exibido na imagem
        largura: Largura da imagem em pixels
        altura: Altura da imagem em pixels
        cor_fundo: Cor de fundo da imagem (R, G, B)
        cor_texto: Cor do texto (R, G, B)
    """
    try:
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        
        # Criar uma imagem com fundo preto
        imagem = Image.new('RGB', (largura, altura), color=cor_fundo)
        draw = ImageDraw.Draw(imagem)
        
        # Tentar carregar uma fonte, ou usar a fonte padrão
        try:
            fonte = ImageFont.truetype("arial.ttf", 20)
        except IOError:
            fonte = ImageFont.load_default()
        
        # Calcular posição do texto para centralizá-lo
        try:
            # Para versões mais recentes do PIL
            left, top, right, bottom = draw.textbbox((0, 0), texto, font=fonte)
            largura_texto = right - left
            altura_texto = bottom - top
        except AttributeError:
            try:
                # Para versões intermediárias do PIL
                largura_texto, altura_texto = draw.textsize(texto, font=fonte)
            except AttributeError:
                # Fallback para valores aproximados
                largura_texto, altura_texto = len(texto) * 10, 20
        
        posicao = ((largura - largura_texto) // 2, (altura - altura_texto) // 2)
        
        # Desenhar o texto
        draw.text(posicao, texto, fill=cor_texto, font=fonte)
        
        # Salvar a imagem
        imagem.save(caminho)
        logging.info(f"Imagem placeholder criada em: {caminho}")
        return True
    except Exception as e:
        logging.error(f"Erro ao criar imagem placeholder: {e}")
        return False

def gerar_proposta(nome_cliente, logo_cliente, modelo_proposta, blocos_selecionados, oferta_selecionada=None):
    try:
        # 1. Definir o nome do arquivo de saída
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"proposta_{nome_cliente.replace(' ', '_')}_{timestamp}.docx"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # 2. Usar o template da capa na raiz do projeto
        template_path = os.path.join(app.root_path, 'capa.docx')
        logging.info(f"Usando template da capa: {template_path}")
        
        # Verificar se o template existe
        if not os.path.exists(template_path):
            logging.error(f"Template da capa não encontrado em: {template_path}")
            raise FileNotFoundError(f"Template da capa não encontrado em: {template_path}")
        
        # Abrir o template usando DocxTemplate em vez de Document
        doc = DocxTemplate(template_path)
        logging.info("Template carregado com sucesso usando DocxTemplate")
        
        # 3. Preparar o contexto para substituição de variáveis
        context = {
            'NOME_CLIENTE': nome_cliente,
        }
        
        # Verificar se há logo do cliente
        if logo_cliente and os.path.exists(logo_cliente):
            context['logo_cliente'] = InlineImage(doc, logo_cliente, width=Inches(2))
            logging.info(f"Logo do cliente adicionado ao contexto: {logo_cliente}")
        
        # Renderizar o template com o contexto
        doc.render(context)
        logging.info("Template renderizado com sucesso")
        
        # 4. Converter para Document para continuar com a adição de blocos
        # Salvar temporariamente o documento renderizado
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], f"temp_{timestamp}.docx")
        doc.save(temp_path)
        
        # Reabrir com python-docx para adicionar os blocos
        doc_with_blocks = Document(temp_path)
        logging.info("Documento reaberto com python-docx para adicionar blocos")
        
        # Adicionar quebra de página após a capa
        doc_with_blocks.add_page_break()
        logging.info("Adicionada quebra de página após a capa")
        
        # 5. Carregar todos os blocos disponíveis e ofertas
        blocos = carregar_blocos()
        ofertas = carregar_ofertas()
        
        # 6. Preparar a lista de blocos a adicionar
        # Converter para lista para fácil manipulação e garantir que seja uma lista de strings
        if blocos_selecionados:
            # Se for uma lista imutável do Flask, converter para lista Python
            if hasattr(blocos_selecionados, 'getlist'):
                logging.info("blocos_selecionados é um tipo de objeto Flask")
                blocos_a_adicionar = blocos_selecionados.getlist('blocos')
            # Se for uma lista Python regular
            elif isinstance(blocos_selecionados, (list, tuple)):
                blocos_a_adicionar = list(blocos_selecionados)
            # Se for um único valor
            else:
                blocos_a_adicionar = [blocos_selecionados]
        else:
            blocos_a_adicionar = []
        
        logging.info(f"Blocos selecionados (inicial): {blocos_a_adicionar}")
            
        # 7. Verificar se há oferta selecionada para incluir os blocos obrigatórios
        if oferta_selecionada and oferta_selecionada in ofertas:
            blocos_obrigatorios = ofertas[oferta_selecionada].get('obrigatorios', [])
            logging.info(f"Blocos obrigatórios da oferta '{oferta_selecionada}': {blocos_obrigatorios}")
            
            # Adicionar blocos obrigatórios à lista se ainda não estiverem lá
            for bloco_obrigatorio in blocos_obrigatorios:
                if bloco_obrigatorio not in blocos_a_adicionar:
                    blocos_a_adicionar.append(bloco_obrigatorio)
                    logging.info(f"Adicionando bloco obrigatório: {bloco_obrigatorio}")

        logging.info(f"Lista final de blocos a adicionar: {blocos_a_adicionar}")
        
        # 8. Adicionar blocos específicos do cliente se não estiverem já incluídos
        for bloco_nome, bloco_info in blocos.items():
            if bloco_info.get('cliente_associado') == nome_cliente and bloco_nome not in blocos_a_adicionar:
                blocos_a_adicionar.append(bloco_nome)
                logging.info(f"Adicionando bloco específico do cliente: {bloco_nome}")
        
        # Se não houver blocos para adicionar, dê um aviso
        if not blocos_a_adicionar:
            logging.warning("Nenhum bloco selecionado ou obrigatório para adicionar à proposta")
        
        logging.info(f"Total de blocos a adicionar ({len(blocos_a_adicionar)}): {blocos_a_adicionar}")
        
        # 9. Adicionar os blocos ao documento
        secao_atual = 1
        
        # Processar cada bloco selecionado, mesmo que não exista no dicionário de blocos
        for indice, bloco_nome in enumerate(blocos_a_adicionar, 1):
            logging.info(f"Processando bloco {indice}: {bloco_nome}")
            
            # 9.1. Adicionar título do bloco com numeração (1.1, 1.2, etc.)
            titulo_formatado = f"{secao_atual}.{indice} {bloco_nome.replace('_', ' ').title()}"
            
            # Adicionar título como parágrafo estilizado
            p = doc_with_blocks.add_paragraph()
            p.style = 'Heading 2'  # Usar estilo de título 2
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(titulo_formatado)
            run.bold = True
            run.font.name = 'Calibri'
            run.font.size = Pt(12)
            
            # 9.2. Verificar se o bloco existe na biblioteca
            if bloco_nome in blocos:
                bloco = blocos[bloco_nome]
                
                # Processar texto do bloco
                texto_bloco = bloco.get('texto', '')
                
                # Substituir placeholders no texto
                if texto_bloco:
                    # Padronizando para o formato {{}}
                    formatos_placeholder = [
                        "{{NOME_CLIENTE}}",
                        "{{nome_cliente}}"
                    ]
                    
                    # Mantendo formatos antigos para compatibilidade
                    formatos_placeholder_compat = [
                        "[[NOME_CLIENTE]]",
                        "NOME_CLIENTE",
                        "[[nome_cliente]]",
                        "nome_cliente"
                    ]
                    
                    # Substituir cada formato possível
                    for formato in formatos_placeholder + formatos_placeholder_compat:
                        if formato in texto_bloco:
                            texto_bloco = texto_bloco.replace(formato, nome_cliente)
                    
                    # Usar BeautifulSoup para processar HTML
                    soup = BeautifulSoup(texto_bloco, 'html.parser')
                    
                    # Se o soup não estiver vazio, processar elementos
                    if soup and len(soup.contents) > 0:
                        # Processar cada elemento HTML
                        for element in soup.children:
                            try:
                                # Processar texto simples
                                if element.name is None:
                                    if element.strip():
                                        p = doc_with_blocks.add_paragraph()
                                        run = p.add_run(element.strip())
                                        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                                        run.font.name = 'Calibri'
                                        run.font.size = Pt(11)
                                
                                # Processar parágrafos
                                elif element.name == 'p':
                                    p = doc_with_blocks.add_paragraph()
                                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                                    
                                    # Processar o conteúdo do parágrafo
                                    for child in element.children:
                                        # Texto simples
                                        if child.name is None:
                                            run = p.add_run(child.string)
                                            run.font.name = 'Calibri'
                                            run.font.size = Pt(11)
                                        
                                        # Negrito
                                        elif child.name == 'strong' or child.name == 'b':
                                            run = p.add_run(child.get_text())
                                            run.bold = True
                                            run.font.name = 'Calibri'
                                            run.font.size = Pt(11)
                                        
                                        # Itálico
                                        elif child.name == 'em' or child.name == 'i':
                                            run = p.add_run(child.get_text())
                                            run.italic = True
                                            run.font.name = 'Calibri'
                                            run.font.size = Pt(11)
                                        
                                        # Sublinhado
                                        elif child.name == 'u':
                                            run = p.add_run(child.get_text())
                                            run.underline = True
                                            run.font.name = 'Calibri'
                                            run.font.size = Pt(11)
                                        
                                        # Links
                                        elif child.name == 'a':
                                            run = p.add_run(child.get_text())
                                            run.font.color.rgb = RGBColor(0, 0, 255)  # Azul
                                            run.underline = True
                                            run.font.name = 'Calibri'
                                            run.font.size = Pt(11)
                                        
                                        # Outros elementos
                                        else:
                                            run = p.add_run(child.get_text())
                                            run.font.name = 'Calibri'
                                            run.font.size = Pt(11)
                                
                                # Processar cabeçalhos
                                elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                                    level = int(element.name[1])
                                    p = doc_with_blocks.add_paragraph()
                                    p.style = f'Heading {level}'
                                    run = p.add_run(element.get_text())
                                    run.bold = True
                                    run.font.name = 'Calibri'
                                    if level == 1:
                                        run.font.size = Pt(16)
                                    elif level == 2:
                                        run.font.size = Pt(14)
                                    else:
                                        run.font.size = Pt(12)
                                
                                # Processar listas não ordenadas
                                elif element.name == 'ul':
                                    for li in element.find_all('li', recursive=False):
                                        p = doc_with_blocks.add_paragraph(style='List Bullet')
                                        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                                        run = p.add_run(li.get_text())
                                        run.font.name = 'Calibri'
                                        run.font.size = Pt(11)
                                
                                # Processar listas ordenadas
                                elif element.name == 'ol':
                                    for idx, li in enumerate(element.find_all('li', recursive=False), 1):
                                        p = doc_with_blocks.add_paragraph(style='List Number')
                                        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                                        run = p.add_run(li.get_text())
                                        run.font.name = 'Calibri'
                                        run.font.size = Pt(11)
                                
                                # Processar imagens
                                elif element.name == 'img':
                                    img_src = element.get('src', '')
                                    if img_src:
                                        # Verificar se é uma imagem base64
                                        if img_src.startswith('data:image'):
                                            # Extrair os dados base64
                                            img_data = img_src.split(',')[1]
                                            img_bytes = base64.b64decode(img_data)
                                            
                                            # Criar um arquivo temporário para a imagem
                                            img_temp = BytesIO(img_bytes)
                                            
                                            # Adicionar a imagem ao documento
                                            p = doc_with_blocks.add_paragraph()
                                            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                            run = p.add_run()
                                            run.add_picture(img_temp, width=Inches(6))
                                        else:
                                            # Tentar carregar a imagem de um caminho
                                            try:
                                                p = doc_with_blocks.add_paragraph()
                                                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                                                run = p.add_run()
                                                run.add_picture(img_src, width=Inches(6))
                                            except Exception as e:
                                                logging.error(f"Erro ao adicionar imagem: {str(e)}")
                            
                            except Exception as e:
                                logging.error(f"Erro ao processar elemento HTML: {str(e)}")
                                continue
                    else:
                        # Adicionar um parágrafo genérico se o bloco não tiver texto
                        p = doc_with_blocks.add_paragraph()
                        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                        run = p.add_run(f"Conteúdo a ser definido para '{bloco_nome.replace('_', ' ').title()}'")
                        run.italic = True
                        run.font.name = 'Calibri'
                        run.font.size = Pt(11)
                else:
                    # Adicionar um parágrafo genérico se o bloco não tiver texto
                    p = doc_with_blocks.add_paragraph()
                    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    run = p.add_run(f"Conteúdo a ser definido para '{bloco_nome.replace('_', ' ').title()}'")
                    run.italic = True
                    run.font.name = 'Calibri'
                    run.font.size = Pt(11)
            else:
                # Adicionar um parágrafo genérico se o bloco não existir na biblioteca
                logging.warning(f"Bloco não encontrado: {bloco_nome}")
                p = doc_with_blocks.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                run = p.add_run(f"[Bloco '{bloco_nome.replace('_', ' ').title()}' não encontrado na biblioteca]")
                run.italic = True
                run.font.name = 'Calibri'
                run.font.size = Pt(11)
        
        # 10. Salvar o documento final
        doc_with_blocks.save(output_path)
        logging.info(f"Documento salvo com sucesso: {output_path}")
        
        # Remover o arquivo temporário
        try:
            os.remove(temp_path)
            logging.info(f"Arquivo temporário removido: {temp_path}")
        except:
            logging.warning(f"Não foi possível remover o arquivo temporário: {temp_path}")
        
        return output_path, filename
    except Exception as e:
        logging.error(f"Erro na geração da proposta: {str(e)}")
        logging.error("Detalhes do erro:", exc_info=True)
        raise

# Função auxiliar para substituir variáveis nos parágrafos
def substituir_variaveis(paragraph, placeholder, valor):
    if not paragraph or not placeholder or not valor:
        return
    
    # Padronizando para o formato {{}}
    # Verificar se o placeholder já está no formato {{}}
    if placeholder.startswith('{{') and placeholder.endswith('}}'):
        formato_padrao = placeholder
    else:
        # Converter para o formato {{}}
        formato_padrao = '{{' + placeholder.replace('[[', '').replace(']]', '').replace('{{', '').replace('}}', '') + '}}'
    
    # Lista de possíveis formatos de placeholder
    formatos_placeholder = [
        formato_padrao,  # Formato padrão (ex: {{NOME_CLIENTE}})
        formato_padrao.lower(),  # Minúsculas (ex: {{nome_cliente}})
    ]
    
    # Formatos antigos para compatibilidade
    formatos_compat = [
        placeholder,  # Formato original (ex: [[NOME_CLIENTE]])
        placeholder.replace('[[', '').replace(']]', ''),  # Sem delimitadores (ex: NOME_CLIENTE)
        placeholder.lower(),  # Minúsculas (ex: [[nome_cliente]])
    ]
    
    # Substituir cada formato possível
    for formato in formatos_placeholder + formatos_compat:
        if formato in paragraph.text:
            for run in paragraph.runs:
                if formato in run.text:
                    run.text = run.text.replace(formato, valor)

def substituir_variaveis_robusto(doc, placeholder, valor):
    for paragraph in doc.paragraphs:
        full_text = ''.join(run.text for run in paragraph.runs)
        if placeholder in full_text:
            # Limpar o texto existente
            for run in paragraph.runs:
                run.text = ''
            # Recriar o texto com o valor substituído
            if placeholder == '{{logo_cliente}}' and os.path.exists(valor):
                paragraph.add_run().add_picture(valor, width=Inches(2))
            else:
                paragraph.add_run(full_text.replace(placeholder, valor))

    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                substituir_variaveis_robusto(cell, placeholder, valor)

# Rota padrão - redireciona para login se não estiver autenticado
@app.route('/')
@login_required
def index():
    return redirect(url_for('dashboard'))

# Rota para a página inicial após o login
@app.route('/home')
@login_required
def home():
    return redirect(url_for('index'))

# Rota para gerenciar usuários
@app.route('/gerenciar_usuarios', methods=['GET', 'POST'])
@admin_required
def gerenciar_usuarios():
    if request.method == 'POST':
        acao = request.form.get('acao')
        
        if acao == 'adicionar':
            # Adicionar novo usuário
            novo_usuario = request.form.get('novo_usuario')
            nova_senha = request.form.get('nova_senha')
            tipo_usuario = request.form.get('tipo_usuario')
            
            if not novo_usuario or not nova_senha or not tipo_usuario:
                flash('Todos os campos são obrigatórios.')
                return redirect(url_for('gerenciar_usuarios'))
            
            tipos_validos = ['admin', 'am', 'comercialpr', 'comercialrj', 'comercialrs', 'comercialsp', 'se']
            
            if tipo_usuario not in tipos_validos:
                flash('Tipo de usuário inválido.')
                return redirect(url_for('gerenciar_usuarios'))
            
            usuarios = carregar_usuarios()
            
            if novo_usuario in usuarios:
                flash('Nome de usuário já existe.')
                return redirect(url_for('gerenciar_usuarios'))
            
            usuarios[novo_usuario] = {
                'senha': nova_senha,
                'tipo': tipo_usuario
            }
            
            salvar_usuarios(usuarios)
            flash('Usuário adicionado com sucesso.')
            
        elif acao == 'remover':
            # Remover usuário existente
            usuario_remover = request.form.get('usuario_remover')
            
            if usuario_remover == 'admin':
                flash('Não é possível remover o usuário admin principal.')
                return redirect(url_for('gerenciar_usuarios'))
            
            usuarios = carregar_usuarios()
            
            if usuario_remover in usuarios:
                del usuarios[usuario_remover]
                salvar_usuarios(usuarios)
                flash('Usuário removido com sucesso.')
            else:
                flash('Usuário não encontrado.')
    
    usuarios = carregar_usuarios()
    return render_template('gerenciar_usuarios.html', usuarios=usuarios)

# Rota para adicionar usuário (mantida para compatibilidade)
@app.route('/adicionar_usuario', methods=['POST'])
@admin_required
def adicionar_usuario():
    username = request.form.get('novo_usuario')
    password = request.form.get('nova_senha')
    tipo = request.form.get('tipo_usuario')
    
    if not username or not password or not tipo:
        flash('Todos os campos são obrigatórios.')
        return redirect(url_for('gerenciar_usuarios'))
    
    tipos_validos = ['admin', 'am', 'comercialpr', 'comercialrj', 'comercialrs', 'comercialsp', 'se']
    
    if tipo not in tipos_validos:
        flash('Tipo de usuário inválido.')
        return redirect(url_for('gerenciar_usuarios'))
    
    usuarios = carregar_usuarios()
    
    if username in usuarios:
        flash('Nome de usuário já existe.')
        return redirect(url_for('gerenciar_usuarios'))
    
    usuarios[username] = {
        'senha': password,
        'tipo': tipo
    }
    
    salvar_usuarios(usuarios)
    flash('Usuário adicionado com sucesso.')
    return redirect(url_for('gerenciar_usuarios'))

# Função para salvar proposta como rascunho
def salvar_como_rascunho(nome_cliente, logo_cliente, modelo_proposta, blocos_selecionados, rascunho_id=None, logo_atual=None, oferta_selecionada=None):
    # Verificar se há dados suficientes para salvar
    if not nome_cliente:
        flash('Por favor, informe pelo menos o nome do cliente para salvar como rascunho.')
        return redirect(url_for('exibir_criar_proposta'))
    
    # Carregar rascunhos existentes
    rascunhos = carregar_rascunhos()
    
    # Gerar ID para o rascunho se não existir
    if not rascunho_id:
        rascunho_id = str(uuid.uuid4())
    
    # Processar upload de arquivo de logo
    if 'logo_file' in request.files and request.files['logo_file'].filename:
        logo_file = request.files['logo_file']
        # Verificar extensão
        if logo_file and '.' in logo_file.filename and logo_file.filename.rsplit('.', 1)[1].lower() in ['png', 'jpg', 'jpeg', 'gif']:
            # Gerar nome único para o arquivo
            filename = secure_filename(f"{nome_cliente.replace(' ', '_')}_{uuid.uuid4()}.{logo_file.filename.rsplit('.', 1)[1].lower()}")
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            logo_file.save(logo_path)
            logo_cliente = logo_path
        else:
            flash('Formato de arquivo não suportado. Use PNG, JPG ou GIF.')
            return redirect(url_for('exibir_criar_proposta', cliente=nome_cliente))
    elif logo_atual:
        # Se não foi enviado novo arquivo, mas existe um logo atual, usar o logo atual
        logo_cliente = logo_atual
    
    # Garantir que blocos_selecionados seja uma lista
    if not isinstance(blocos_selecionados, list):
        blocos_selecionados = [blocos_selecionados] if blocos_selecionados else []
    
    # Criar ou atualizar o rascunho
    rascunhos[rascunho_id] = {
        'nome_cliente': nome_cliente,
        'logo_cliente': logo_cliente,
        'blocos_selecionados': blocos_selecionados,
        'usuario': session.get('usuario_logado'),
        'data_atualizacao': datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
        'oferta_selecionada': oferta_selecionada
    }
    
    # Salvar os rascunhos
    salvar_rascunhos(rascunhos)
    
    # Verificar se é um salvamento automático
    auto_save = request.form.get('auto_save', '')
    if auto_save == '1':
        # Para salvamento automático, retornar uma resposta vazia com status 204 (No Content)
        return ('', 204)
    
    flash('Rascunho salvo com sucesso!')
    return redirect(url_for('dashboard'))

@app.route('/excluir_rascunho/<rascunho_id>')
@login_required
def excluir_rascunho(rascunho_id):
    # Carregar rascunhos existentes
    rascunhos = carregar_rascunhos()
    
    # Verificar se o rascunho existe
    if rascunho_id not in rascunhos:
        flash('Rascunho não encontrado.')
        return redirect(url_for('dashboard'))
    
    # Verificar se o usuário tem permissão para excluir o rascunho
    if rascunhos[rascunho_id]['usuario'] != session.get('usuario_logado') and session.get('tipo_usuario') != 'admin':
        flash('Você não tem permissão para excluir este rascunho.')
        return redirect(url_for('dashboard'))
    
    # Excluir o rascunho
    del rascunhos[rascunho_id]
    
    # Salvar os rascunhos atualizados
    salvar_rascunhos(rascunhos)
    
    flash('Rascunho excluído com sucesso!')
    return redirect(url_for('dashboard'))

@app.route('/static/img/placeholder-logo.png')
def placeholder_logo():
    # Criar uma imagem de placeholder
    width, height = 200, 200
    image = Image.new('RGB', (width, height), color=(240, 240, 240))
    
    # Adicionar texto
    draw = ImageDraw.Draw(image)
    
    # Tentar carregar uma fonte, ou usar a fonte padrão
    try:
        font = ImageFont.truetype("arial.ttf", 20)
    except IOError:
        font = ImageFont.load_default()
    
    text = "Logo do Cliente"
    
    # Diferentes versões do PIL têm diferentes métodos para obter o tamanho do texto
    try:
        # Para versões mais recentes do PIL
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        text_width = right - left
        text_height = bottom - top
    except AttributeError:
        try:
            # Para versões intermediárias do PIL
            text_width, text_height = draw.textsize(text, font=font)
        except AttributeError:
            # Fallback para valores aproximados
            text_width, text_height = 100, 20
    
    position = ((width - text_width) // 2, (height - text_height) // 2)
    
    # Desenhar o texto
    draw.text(position, text, fill=(150, 150, 150), font=font)
    
    # Salvar a imagem em um buffer
    img_io = BytesIO()
    image.save(img_io, 'PNG')
    img_io.seek(0)
    
    return send_file(img_io, mimetype='image/png')

# Função para carregar ofertas do arquivo JSON
def carregar_ofertas():
    try:
        if os.path.exists(OFERTAS_FILE):
            with open(OFERTAS_FILE, "r", encoding="utf-8") as f:
                ofertas = json.load(f)
                return ofertas
        else:
            return {}
    except json.JSONDecodeError as e:
        print(f"Erro ao ler ofertas.json: {e}")
        return {}

# Função para salvar ofertas no arquivo JSON
def salvar_ofertas(ofertas):
    with open(OFERTAS_FILE, "w", encoding="utf-8") as f:
        json.dump(ofertas, f, ensure_ascii=False, indent=4)

# Rota para obter todos os blocos (API)
@app.route('/api/blocos', methods=['GET'])
@login_required
def api_blocos():
    try:
        blocos = carregar_blocos()
        return jsonify(blocos)
    except Exception as e:
        app.logger.error(f"Erro ao carregar blocos: {str(e)}")
        return jsonify({"error": "Erro ao carregar blocos"}), 500

# Rota para obter um bloco específico (API)
@app.route('/api/bloco/<bloco_nome>', methods=['GET'])
@login_required
def api_bloco(bloco_nome):
    try:
        app.logger.info(f"Solicitação para obter bloco: {bloco_nome}")
        blocos = carregar_blocos()
        app.logger.info(f"Blocos carregados: {list(blocos.keys())}")
        
        if bloco_nome in blocos:
            app.logger.info(f"Bloco encontrado: {bloco_nome}")
            return jsonify(blocos[bloco_nome])
        else:
            app.logger.warning(f"Bloco não encontrado: {bloco_nome}")
            # Retornar um template vazio para permitir a criação do bloco
            return jsonify({
                "error": "Bloco não encontrado", 
                "texto": "<p>Este é um novo bloco. Edite o conteúdo e salve para criá-lo.</p>",
                "novo_bloco": True
            }), 200  # Retornar 200 em vez de 404 para permitir a criação
    except Exception as e:
        app.logger.error(f"Erro ao carregar bloco {bloco_nome}: {str(e)}")
        return jsonify({"error": "Erro ao carregar bloco", "texto": "<p>Erro ao carregar bloco</p>"}), 500

# Rota para salvar um bloco (API)
@app.route('/api/salvar_bloco', methods=['POST'])
@login_required
def salvar_bloco_api():
    try:
        data = request.json
        bloco_nome = data.get('nome')
        texto = data.get('texto')
        
        if not bloco_nome or not texto:
            return jsonify({"success": False, "error": "Dados incompletos"}), 400
        
        blocos = carregar_blocos()
        if bloco_nome in blocos:
            # Atualizar bloco existente
            blocos[bloco_nome]['texto'] = texto
            logging.info(f"Bloco atualizado: {bloco_nome}")
        else:
            # Criar novo bloco
            blocos[bloco_nome] = {
                'texto': texto,
                'imagem': None,
                'obrigatorio': False,
                'criado_por': session.get('usuario_logado'),
                'data_criacao': datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
                'cliente_associado': None
            }
            logging.info(f"Novo bloco criado: {bloco_nome}")
        
        salvar_blocos(blocos)
        return jsonify({"success": True})
    except Exception as e:
        logging.error(f"Erro ao salvar bloco: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# Adicionar nova rota para excluir bloco
@app.route('/api/excluir_bloco/<bloco_id>', methods=['DELETE'])
@login_required
def excluir_bloco_api(bloco_id):
    try:
        blocos = carregar_blocos()
        if bloco_id in blocos:
            # Verificar se o usuário é admin
            if session.get('tipo_usuario') != 'admin':
                return jsonify({"success": False, "error": "Apenas administradores podem excluir blocos"}), 403
                
            del blocos[bloco_id]
            salvar_blocos(blocos)
            return jsonify({"success": True})
        return jsonify({"success": False, "error": "Bloco não encontrado"}), 404
    except Exception as e:
        app.logger.error(f"Erro ao excluir bloco: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/adicionar_bloco', methods=['GET', 'POST'])
@login_required
def adicionar_bloco():
    cliente = request.args.get('cliente', '')
    
    if request.method == 'POST':
        nome_bloco = request.form['nome_bloco'].replace(' ', '_')
        texto_bloco = request.form['texto_bloco']
        cliente_associado = request.form.get('cliente_associado', '')
        reutilizavel = request.form.get('reutilizavel', 'off') == 'on'
        
        blocos = carregar_blocos()
        
        # Verificar se o bloco já existe
        if nome_bloco in blocos and reutilizavel:
            flash('Já existe um bloco com este nome. Escolha outro nome para o bloco reutilizável.')
            return render_template('adicionar_bloco.html', cliente=cliente)
        
        # Se não for reutilizável, tornar o nome do bloco único para este cliente
        if not reutilizavel and cliente_associado:
            nome_bloco = f"{cliente_associado}_{nome_bloco}"
        
        # Adicionar o novo bloco
        blocos[nome_bloco] = {
            'texto': texto_bloco,
            'imagem': None,
            'obrigatorio': False,
            'criado_por': session.get('usuario_logado'),
            'data_criacao': datetime.datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'cliente_associado': cliente_associado,
            'reutilizavel': reutilizavel
        }
        
        salvar_blocos(blocos)
        flash('Bloco adicionado com sucesso!')
        
        # Redirecionar para a página de criação de proposta, passando o bloco como selecionado
        if cliente_associado:
            # Se estamos criando um bloco para uma proposta específica, pré-selecionar o bloco
            return redirect(url_for('exibir_criar_proposta', cliente=cliente_associado, bloco_novo=nome_bloco))
        else:
            return redirect(url_for('exibir_criar_proposta'))
    
    return render_template('adicionar_bloco.html', cliente=cliente)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)
