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
from datetime import datetime
import shutil
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from docx.oxml.ns import nsdecls
from docx.oxml import parse_xml
import html

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
                return blocos
        else:
            return {}
    except json.JSONDecodeError as e:
        print(f"Erro ao ler blocos.json: {e}")
        return {}

# Função para salvar os blocos de conteúdo no arquivo JSON
def salvar_blocos(blocos):
    try:
        os.makedirs(os.path.dirname(BLOCOS_FILE), exist_ok=True)
        with open(BLOCOS_FILE, "w", encoding="utf-8") as f:
            json.dump(blocos, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Erro ao salvar blocos.json: {e}")

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
    
    # Carregar rascunhos do usuário atual
    rascunhos = carregar_rascunhos()
    rascunhos_usuario = {}
    
    usuario_atual = session.get('usuario_logado')
    for rascunho_id, rascunho in rascunhos.items():
        if rascunho.get('usuario') == usuario_atual:
            rascunhos_usuario[rascunho_id] = rascunho
    
    return render_template('dashboard.html', 
                          propostas=propostas,
                          rascunhos_usuario=rascunhos_usuario,
                          tipo_usuario=session.get('tipo_usuario', ''))

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
    nova_proposta = request.args.get('nova', False)
    
    # Obter o cliente da query string (se existir)
    cliente = request.args.get('cliente', '')
    
    # Verificar se há um rascunho para continuar
    rascunho_id = request.args.get('rascunho_id', '')
    rascunho_data = {}
    
    if rascunho_id and not nova_proposta:
        rascunhos = carregar_rascunhos()
        if rascunho_id in rascunhos and rascunhos[rascunho_id].get('usuario') == session.get('usuario_logado'):
            rascunho_data = rascunhos[rascunho_id]
            cliente = rascunho_data.get('nome_cliente', cliente)
    
    # Limpar qualquer seleção anterior de blocos (para reiniciar a página)
    if nova_proposta or ('blocos_selecionados' in session and not rascunho_id):
        if 'blocos_selecionados' in session:
            session.pop('blocos_selecionados')
        # Limpar outros dados de sessão relacionados à proposta
        if 'cliente' in session:
            session.pop('cliente')
        if 'logo_cliente' in session:
            session.pop('logo_cliente')
        cliente = ''  # Limpar o cliente se for uma nova proposta
        rascunho_id = ''  # Limpar o ID do rascunho
        rascunho_data = {}  # Limpar os dados do rascunho
    
    # Verificar tipo de usuário
    is_admin = session.get('tipo_usuario') == 'admin'
    
    # Carregar blocos de texto
    blocos = carregar_blocos()
    
    # Carregar ofertas disponíveis
    ofertas = carregar_ofertas()
    
    # Obter a primeira oferta, se existir
    primeira_oferta = next(iter(ofertas.keys())) if ofertas else ''
    
    # Filtrar blocos: mostrar apenas blocos obrigatórios e blocos específicos para este cliente
    blocos_filtrados = {}
    for bloco_nome, bloco_info in blocos.items():
        # Incluir blocos obrigatórios
        if bloco_info.get('obrigatorio', False):
            blocos_filtrados[bloco_nome] = bloco_info
        # Incluir blocos específicos para este cliente
        elif cliente and bloco_info.get('cliente_associado') == cliente:
            blocos_filtrados[bloco_nome] = bloco_info
        # Incluir blocos gerais (não associados a nenhum cliente)
        elif not bloco_info.get('cliente_associado'):
            blocos_filtrados[bloco_nome] = bloco_info
        # Administradores podem ver todos os blocos
        elif is_admin:
            blocos_filtrados[bloco_nome] = bloco_info
    
    # Renderizar o template com os dados
    return render_template('criar_proposta.html', 
                          blocos=blocos_filtrados, 
                          ofertas=ofertas,
                          is_admin=is_admin,
                          cliente=cliente,
                          rascunho=rascunho_data,
                          rascunho_id=rascunho_id,
                          primeira_oferta=primeira_oferta)

# Rota para processar a criação de uma proposta
@app.route('/criar_proposta', methods=['POST'])
@login_required
def criar_proposta():
    nome_cliente = request.form.get('nome_cliente', '')
    blocos_selecionados = request.form.getlist('blocos')
    rascunho_id = request.form.get('rascunho_id', '')
    logo_atual = request.form.get('logo_atual', '')
    auto_save = request.form.get('auto_save', '')
    oferta_selecionada = request.form.get('oferta_selecionada', '')
    
    # Verificar se é para salvar como rascunho ou salvamento automático
    if 'salvar_rascunho' in request.form or auto_save == '1':
        return salvar_como_rascunho(nome_cliente, None, None, blocos_selecionados, rascunho_id, logo_atual, oferta_selecionada)
    
    # Processar upload de arquivo de logo
    logo_path = None
    if 'logo_file' in request.files and request.files['logo_file'].filename:
        logo_file = request.files['logo_file']
        # Verificar extensão
        if logo_file and '.' in logo_file.filename and logo_file.filename.rsplit('.', 1)[1].lower() in ['png', 'jpg', 'jpeg', 'gif']:
            # Gerar nome único para o arquivo
            filename = secure_filename(f"{nome_cliente.replace(' ', '_')}_{uuid.uuid4()}.{logo_file.filename.rsplit('.', 1)[1].lower()}")
            logo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            logo_file.save(logo_path)
        else:
            flash('Formato de arquivo não suportado. Use PNG, JPG ou GIF.')
            return redirect(url_for('exibir_criar_proposta', cliente=nome_cliente))
    elif logo_atual:
        # Usar o logo atual se disponível
        logo_path = os.path.join(app.root_path, logo_atual)
    
    # Verificar se há blocos selecionados
    if not blocos_selecionados:
        flash('Selecione pelo menos um bloco de conteúdo.')
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
        
        flash('Proposta gerada com sucesso!')
        return redirect(url_for('visualizar_proposta', proposta_id=proposta_id))
    except Exception as e:
        flash(f'Erro ao gerar proposta: {str(e)}')
        return redirect(url_for('exibir_criar_proposta', cliente=nome_cliente))

# Função para gerar proposta
def gerar_proposta(nome_cliente, logo_cliente, modelo_proposta, blocos_selecionados, oferta_selecionada=None):
    # Criar um novo documento do zero
    doc = Document()
    
    # Configurar margens do documento
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.5)
        section.right_margin = Inches(0.5)
    
    # Adicionar a capa
    # Criar uma nova seção para a capa
    section = doc.add_section()
    section.start_type = WD_SECTION_START.NEW_PAGE
    
    # Definir o fundo preto para a capa
    # Nota: Python-docx não suporta diretamente fundos de página, então vamos usar uma tabela para simular
    table = doc.add_table(rows=1, cols=1)
    table.autofit = False
    table.allow_autofit = False
    cell = table.cell(0, 0)
    
    # Definir largura e altura da tabela para cobrir toda a página
    table.width = Inches(8.5)  # Largura padrão de uma página A4
    cell.width = Inches(8.5)
    
    # Definir cor de fundo da célula para preto
    shading_elm = parse_xml(r'<w:shd {} w:fill="000000"/>'.format(nsdecls('w')))
    cell._tc.get_or_add_tcPr().append(shading_elm)
    
    # Adicionar conteúdo da capa dentro da célula
    paragraph = cell.paragraphs[0]
    paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
    paragraph.space_after = Pt(50)
    
    # Adicionar espaço no topo
    for _ in range(5):
        p = cell.add_paragraph()
        p.space_after = Pt(12)
    
    # Adicionar o logo da Service IT
    p = cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.space_after = Pt(50)
    
    service_it_logo_path = os.path.join('static', 'img', 'logo_service_it.png')
    if os.path.exists(service_it_logo_path):
        run = p.add_run()
        run.add_picture(service_it_logo_path, width=Inches(3))
    
    # Adicionar linha horizontal
    p = cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.space_after = Pt(30)
    run = p.add_run()
    run.add_text('_' * 50)  # Linha simples
    run.font.color.rgb = RGBColor(200, 200, 200)  # Cinza claro
    
    # Adicionar nome do cliente
    p = cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.space_after = Pt(20)
    run = p.add_run(f"{{{{NOME_CLIENTE}}}}")
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor(200, 200, 200)  # Cinza claro
    
    # Adicionar espaço para o logo do cliente
    p = cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.space_after = Pt(80)
    run = p.add_run("{{logo_cliente}}")
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(200, 200, 200)  # Cinza claro
    
    # Adicionar título da proposta
    p = cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.space_after = Pt(12)
    run = p.add_run("PROPOSTA COMERCIAL")
    run.font.size = Pt(24)
    run.font.bold = True
    run.font.color.rgb = RGBColor(255, 255, 255)  # Branco
    
    # Adicionar subtítulo
    p = cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.space_after = Pt(100)
    run = p.add_run("Serviços Gerenciados")
    run.font.size = Pt(16)
    run.font.color.rgb = RGBColor(200, 200, 200)  # Cinza claro
    
    # Adicionar espaço antes do rodapé
    for _ in range(3):
        p = cell.add_paragraph()
        p.space_after = Pt(12)
    
    # Adicionar rodapé com site
    p = cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.space_after = Pt(12)
    run = p.add_run("www.service.com.br")
    run.font.size = Pt(10)
    run.font.color.rgb = RGBColor(150, 150, 150)  # Cinza médio
    
    # Adicionar classificação "Restrita" no canto inferior esquerdo
    p = cell.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run("Classificação: Restrita")
    run.font.size = Pt(8)
    run.font.color.rgb = RGBColor(150, 150, 150)  # Cinza médio
    
    # Iniciar uma nova seção para o conteúdo
    section = doc.add_section()
    section.start_type = WD_SECTION_START.NEW_PAGE
    
    # Adicionar cabeçalho com logo da Service IT e nome do cliente
    header = section.header
    htable = header.add_table(1, 2, width=Inches(6))
    htable.style = 'Table Grid'
    htable.autofit = False
    
    # Remover bordas da tabela
    for cell in htable.cells:
        for border in ['top', 'left', 'bottom', 'right']:
            cell._element.get_or_add_tcPr().first_child_found_in("w:tcBorders").get_or_add_child('w:{}'.format(border)).set('w:val', 'nil')
    
    # Célula para o logo da Service IT
    cell = htable.cell(0, 0)
    cell.width = Inches(2)
    p = cell.paragraphs[0]
    run = p.add_run()
    run.add_picture(service_it_logo_path, width=Inches(1.5))
    
    # Célula para o nome do cliente
    cell = htable.cell(0, 1)
    cell.width = Inches(4)
    p = cell.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    run = p.add_run(f"{{{{NOME_CLIENTE}}}}")
    run.font.size = Pt(12)
    
    # Adicionar rodapé com número de página e site
    footer = section.footer
    p = footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("www.service.com.br")
    run.font.size = Pt(10)
    
    # Adicionar informação da oferta selecionada, se disponível
    if oferta_selecionada:
        p = doc.add_paragraph()
        p.style = 'Heading 1'
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run(f"Oferta: {oferta_selecionada}")
    
    # Carregar blocos de conteúdo
    blocos = carregar_blocos()
    
    # Adicionar blocos de conteúdo selecionados
    for bloco_nome in blocos_selecionados:
        if bloco_nome in blocos:
            bloco = blocos[bloco_nome]
            
            # Adicionar título do bloco
            p = doc.add_paragraph()
            p.style = 'Heading 2'
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            run = p.add_run(bloco_nome.replace('_', ' ').title())
            
            # Adicionar conteúdo HTML do bloco
            html_content = bloco.get('texto', '')
            
            # Substituir placeholders
            html_content = html_content.replace('{{NOME_CLIENTE}}', nome_cliente)
            
            # Adicionar o conteúdo HTML ao documento
            adicionar_html_para_docx(doc, html_content)
            
            # Adicionar imagem, se existir
            if bloco.get('imagem'):
                try:
                    img_path = os.path.join(app.config['UPLOAD_FOLDER'], bloco['imagem'])
                    if os.path.exists(img_path):
                        doc.add_picture(img_path, width=Inches(6))
                        last_paragraph = doc.paragraphs[-1]
                        last_paragraph.alignment = WD_ALIGN_PARAGRAPH.CENTER
                except Exception as e:
                    print(f"Erro ao adicionar imagem: {e}")
    
    # Substituir placeholders na capa e no cabeçalho
    for paragraph in doc.paragraphs:
        if '{{NOME_CLIENTE}}' in paragraph.text:
            for run in paragraph.runs:
                run.text = run.text.replace('{{NOME_CLIENTE}}', nome_cliente)
    
    # Substituir o placeholder do logo do cliente
    if logo_cliente and os.path.exists(logo_cliente):
        for i, paragraph in enumerate(doc.paragraphs):
            if '{{logo_cliente}}' in paragraph.text:
                # Limpar o parágrafo
                for run in paragraph.runs:
                    run.text = ''
                # Adicionar o logo
                run = paragraph.add_run()
                run.add_picture(logo_cliente, width=Inches(2))
                break
    
    # Substituir placeholders nos cabeçalhos
    for section in doc.sections:
        for header in [section.header]:
            for paragraph in header.paragraphs:
                if '{{NOME_CLIENTE}}' in paragraph.text:
                    for run in paragraph.runs:
                        run.text = run.text.replace('{{NOME_CLIENTE}}', nome_cliente)
            # Verificar tabelas no cabeçalho
            for table in header.tables:
                for row in table.rows:
                    for cell in row.cells:
                        for paragraph in cell.paragraphs:
                            if '{{NOME_CLIENTE}}' in paragraph.text:
                                for run in paragraph.runs:
                                    run.text = run.text.replace('{{NOME_CLIENTE}}', nome_cliente)
    
    # Substituir placeholders nas tabelas
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    if '{{NOME_CLIENTE}}' in paragraph.text:
                        for run in paragraph.runs:
                            run.text = run.text.replace('{{NOME_CLIENTE}}', nome_cliente)
                    if '{{logo_cliente}}' in paragraph.text and logo_cliente and os.path.exists(logo_cliente):
                        # Limpar o parágrafo
                        for run in paragraph.runs:
                            run.text = ''
                        # Adicionar o logo
                        run = paragraph.add_run()
                        run.add_picture(logo_cliente, width=Inches(2))
    
    # Gerar nome de arquivo único para a proposta
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"proposta_{nome_cliente.replace(' ', '_')}_{timestamp}.docx"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    # Salvar o documento
    doc.save(output_path)
    
    return output_path, filename

def adicionar_html_para_docx(doc, html_content):
    """
    Converte conteúdo HTML para formatação no documento Word
    """
    # Remover tags HTML básicas e preservar formatação
    from bs4 import BeautifulSoup
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Processar o conteúdo HTML
        for element in soup.find_all(recursive=False):
            if element.name == 'p':
                p = doc.add_paragraph()
                processar_elemento(element, p)
            elif element.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                level = int(element.name[1])
                p = doc.add_paragraph()
                p.style = f'Heading {level}'
                processar_elemento(element, p)
            elif element.name == 'ul':
                for li in element.find_all('li', recursive=False):
                    p = doc.add_paragraph(style='List Bullet')
                    processar_elemento(li, p)
            elif element.name == 'ol':
                for li in element.find_all('li', recursive=False):
                    p = doc.add_paragraph(style='List Number')
                    processar_elemento(li, p)
            else:
                # Para outros elementos, adicionar como parágrafo simples
                p = doc.add_paragraph()
                processar_elemento(element, p)
    except Exception as e:
        # Se ocorrer algum erro na conversão, adicionar o texto sem formatação
        doc.add_paragraph(BeautifulSoup(html_content, 'html.parser').get_text())

def processar_elemento(element, paragraph):
    """
    Processa um elemento HTML e adiciona ao parágrafo com a formatação apropriada
    """
    if element.name == 'br':
        paragraph.add_run().add_break()
        return
    
    # Processar o texto e os elementos filhos
    for content in element.contents:
        if content.name is None:  # É um nó de texto
            run = paragraph.add_run(content.string if content.string else '')
        else:  # É um elemento HTML
            if content.name == 'strong' or content.name == 'b':
                run = paragraph.add_run(content.get_text())
                run.bold = True
            elif content.name == 'em' or content.name == 'i':
                run = paragraph.add_run(content.get_text())
                run.italic = True
            elif content.name == 'u':
                run = paragraph.add_run(content.get_text())
                run.underline = True
            elif content.name == 'br':
                paragraph.add_run().add_break()
            elif content.name == 'a':
                run = paragraph.add_run(content.get_text())
                run.underline = True
                run.font.color.rgb = RGBColor(0, 0, 255)  # Azul para links
            else:
                # Para outros elementos, processar recursivamente
                processar_elemento(content, paragraph)

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

# Rota para editar e salvar blocos
@app.route('/editar_blocos')
@admin_required
def editar_blocos():
    blocos_de_texto = carregar_blocos()
    is_admin = session.get('tipo_usuario') == 'admin'
    return render_template('editar_blocos.html', blocos=blocos_de_texto, is_admin=is_admin)

# Rota para salvar as edições dos blocos no JSON
@app.route('/salvar_blocos', methods=['POST'])
@admin_required
def salvar_edicao_blocos():
    blocos_de_texto = carregar_blocos()
    is_admin = session.get('tipo_usuario') == 'admin'
    
    # Verificar se o usuário é admin para editar blocos obrigatórios
    for bloco in blocos_de_texto.keys():
        if session.get('tipo_usuario') != 'admin' and blocos_de_texto[bloco].get('obrigatorio', False):
            continue  # AMs não podem editar blocos obrigatórios
            
        novo_texto = request.form.get(f"{bloco}_texto")
        if novo_texto:
            # Substituir imagens embutidas por imagens salvas corretamente
            novo_texto = salvar_imagens_e_substituir(novo_texto, bloco)
            blocos_de_texto[bloco]['texto'] = novo_texto
    
    salvar_blocos(blocos_de_texto)
    return redirect(url_for('dashboard'))

# Rota para excluir um bloco de conteúdo
@app.route('/excluir_bloco/<nome_bloco>', methods=['GET'])
@login_required
def excluir_bloco(nome_bloco):
    try:
        blocos_de_texto = carregar_blocos()
        is_admin = session.get('tipo_usuario') == 'admin'
        
        # Verificar se o bloco existe
        if nome_bloco not in blocos_de_texto:
            flash('Bloco não encontrado.', 'danger')
            return redirect(url_for('editar_blocos'))
        
        # Verificar se o bloco é obrigatório
        if blocos_de_texto[nome_bloco].get('obrigatorio', False):
            if not is_admin:
                flash('Você não tem permissão para excluir blocos obrigatórios.', 'danger')
                return redirect(url_for('dashboard'))
            else:
                # Confirmar exclusão de bloco obrigatório por admin
                flash('Atenção: Você está excluindo um bloco obrigatório.', 'warning')
        
        # Excluir o bloco
        del blocos_de_texto[nome_bloco]
        salvar_blocos(blocos_de_texto)
        flash(f'Bloco "{nome_bloco.replace("_", " ")}" excluído com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir bloco: {str(e)}', 'danger')
    
    if is_admin:
        return redirect(url_for('editar_blocos'))
    else:
        return redirect(url_for('dashboard'))

# Rota para adicionar um novo bloco de conteúdo
@app.route('/adicionar_bloco', methods=['GET', 'POST'])
@login_required
def adicionar_bloco():
    is_admin = session.get('tipo_usuario') == 'admin'
    cliente = request.args.get('cliente', '')
    
    if request.method == 'POST':
        nome_bloco = request.form['nome_bloco'].replace(' ', '_')
        texto_bloco = request.form['texto_bloco']
        obrigatorio = request.form.get('obrigatorio') == 'on'
        cliente_associado = request.form.get('cliente_associado', '')
        
        # Apenas admins podem marcar blocos como obrigatórios
        if not is_admin:
            obrigatorio = False
        
        blocos_de_texto = carregar_blocos()
        
        # Verificar se o bloco já existe
        if nome_bloco in blocos_de_texto:
            flash(f'Já existe um bloco com o nome "{nome_bloco.replace("_", " ")}"!', 'danger')
            return render_template('adicionar_bloco.html', is_admin=is_admin, cliente=cliente_associado)
        
        # Salvar imagens embutidas no texto HTML
        texto_processado = salvar_imagens_e_substituir(texto_bloco, nome_bloco)
        
        # Adicionar o novo bloco
        blocos_de_texto[nome_bloco] = {
            'texto': texto_processado,
            'imagem': None,
            'obrigatorio': obrigatorio,
            'criado_por': session.get('usuario_logado'),
            'data_criacao': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
            'cliente_associado': cliente_associado  # Novo campo para associar o bloco a um cliente
        }
        
        salvar_blocos(blocos_de_texto)
        flash(f'Bloco "{nome_bloco.replace("_", " ")}" adicionado com sucesso!', 'success')
        
        # Redirecionar para a página de criação de proposta com o cliente preenchido
        if cliente_associado:
            return redirect(url_for('exibir_criar_proposta', cliente=cliente_associado))
        else:
            return redirect(url_for('exibir_criar_proposta'))
    
    return render_template('adicionar_bloco.html', is_admin=is_admin, cliente=cliente)

# Função para processar imagens e salvar com caminho correto no HTML
def salvar_imagens_e_substituir(texto_html, bloco_nome):
    img_counter = 1

    def salvar_imagem(match):
        nonlocal img_counter
        img_data = match.group(1)
        if img_data.startswith("data:image/"):
            img_data = img_data.split(",")[1]
            img_bytes = base64.b64decode(img_data)
            img_nome = f"{bloco_nome}_img_{img_counter}.png"
            img_path = os.path.join(app.config['IMAGE_FOLDER'], img_nome)
            with Image.open(BytesIO(img_bytes)) as img:
                img.save(img_path, format="PNG")
            img_counter += 1
            return f'<img src="/{img_path}">'
        return match.group(0)

    return re.sub(r'<img src="([^"]+)"', salvar_imagem, texto_html)

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
            
            if tipo_usuario not in ['admin', 'am']:
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
    
    tipos_validos = ['admin', 'am', 'vp_comercial', 'diretor_regional', 'gerente_comercial', 
                     'vp_tecnologia', 'head_sales_engineer', 'sales_engineer']
    
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
        'data_atualizacao': datetime.now().strftime('%d/%m/%Y %H:%M:%S'),
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
    blocos = carregar_blocos()
    return jsonify(blocos)

# Rota para obter um bloco específico (API)
@app.route('/api/bloco/<bloco_nome>', methods=['GET'])
@login_required
def api_bloco(bloco_nome):
    blocos = carregar_blocos()
    if bloco_nome in blocos:
        return jsonify(blocos[bloco_nome])
    else:
        return jsonify({"error": "Bloco não encontrado"}), 404

# Rota para salvar um bloco (API)
@app.route('/api/salvar_bloco', methods=['POST'])
@login_required
def api_salvar_bloco():
    data = request.json
    bloco_nome = data.get('bloco_nome')
    texto = data.get('texto')
    
    if not bloco_nome or not texto:
        return jsonify({"success": False, "error": "Nome do bloco e texto são obrigatórios"}), 400
    
    blocos = carregar_blocos()
    
    # Verificar se o bloco existe
    if bloco_nome not in blocos:
        return jsonify({"success": False, "error": "Bloco não encontrado"}), 404
    
    # Atualizar o texto do bloco
    blocos[bloco_nome]['texto'] = texto
    
    # Salvar os blocos
    try:
        salvar_blocos(blocos)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
