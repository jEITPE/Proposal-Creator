from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timedelta

db = SQLAlchemy()

# Tabela de associação entre Proposta e Blocos
proposta_blocos = db.Table('proposta_blocos',
    db.Column('proposta_id', db.String(36), db.ForeignKey('proposta.id', ondelete='CASCADE')),
    db.Column('bloco_nome', db.String(100), db.ForeignKey('bloco_proposta.nome', ondelete='CASCADE'))
)

# Tabela de associação entre Proposta e Ofertas
proposta_ofertas = db.Table('proposta_ofertas',
    db.Column('proposta_id', db.String(36), db.ForeignKey('proposta.id', ondelete='CASCADE')),
    db.Column('oferta_id', db.Integer, db.ForeignKey('oferta.id', ondelete='CASCADE'))
)

# Tabela de associação entre Usuário e Blocos (permissões)
usuario_permissoes_blocos = db.Table('usuario_permissoes_blocos',
    db.Column('usuario_id', db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE')),
    db.Column('bloco_nome', db.String(100), db.ForeignKey('bloco_proposta.nome', ondelete='CASCADE'))
)

# Modelo de Perfil de Usuário
class Perfil(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), nullable=False, unique=True)
    descricao = db.Column(db.String(255))
    usuarios = db.relationship('Usuario', backref='perfil', lazy=True)
    # Indica se é um perfil com acesso temporário
    acesso_temporario = db.Column(db.Boolean, default=False)

# Modelo de Usuário
class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    login = db.Column(db.String(50), nullable=False, unique=True)
    senha = db.Column(db.String(255), nullable=False)
    status = db.Column(db.Integer, default=1)  # 1 ativo / 2 inativo
    id_perfil = db.Column(db.Integer, db.ForeignKey('perfil.id'), nullable=False)
    ultimo_acesso = db.Column(db.DateTime, default=datetime.utcnow)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    data_expiracao = db.Column(db.DateTime, nullable=True)  # Data de expiração para usuários temporários
    superusuario = db.Column(db.Boolean, default=False)  # Usuário com acesso a todos os blocos
    
    # Relação muitos-para-muitos com os blocos que o usuário pode editar
    blocos_permitidos = db.relationship(
        'BlocoProposta',
        secondary=usuario_permissoes_blocos,
        lazy='subquery',
        backref=db.backref('usuarios_com_acesso', lazy=True)
    )
    
    # Verifica se o acesso do usuário está expirado (para usuários temporários)
    def is_acesso_expirado(self):
        if not self.data_expiracao:
            return False
        return datetime.utcnow() > self.data_expiracao
    
    # Verifica se o usuário tem permissão para editar um bloco específico
    def pode_editar_bloco(self, bloco_nome):
        # Se for superusuário ou admin, pode editar qualquer bloco
        if self.superusuario or self.perfil.nome == "Governança":
            return True
            
        # Caso contrário, verifica nas permissões específicas
        for bloco in self.blocos_permitidos:
            if bloco.nome == bloco_nome:
                return True
                
        return False

# Modelo de Bloco de Proposta
class BlocoProposta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    titulo = db.Column(db.String(200))
    texto = db.Column(db.Text, nullable=False)
    imagem = db.Column(db.String(255))
    obrigatorio = db.Column(db.Boolean, default=False)
    criado_por = db.Column(db.String(50))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

# Modelo de Oferta
class Oferta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    tipo_oferta = db.Column(db.String(100), nullable=False, unique=True)
    blocos = db.relationship('BlocoPropostaOferta', backref='oferta', lazy=True)

# Modelo de Bloco de Proposta por Oferta
class BlocoPropostaOferta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_oferta = db.Column(db.Integer, db.ForeignKey('oferta.id'), nullable=False)
    texto = db.Column(db.Text, nullable=False)
    imagem = db.Column(db.String(255))
    criado_por = db.Column(db.String(50))
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)

# Modelo de Proposta
class Proposta(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    nome_cliente = db.Column(db.String(100), nullable=False)
    data_geracao = db.Column(db.DateTime, default=datetime.utcnow)
    gerado_por = db.Column(db.String(50))
    arquivo = db.Column(db.String(255))
    
    # Relacionamentos corrigidos com joins explícitos
    blocos_utilizados = db.relationship(
        'BlocoProposta', 
        secondary=proposta_blocos,
        primaryjoin="Proposta.id == proposta_blocos.c.proposta_id",
        secondaryjoin="proposta_blocos.c.bloco_nome == BlocoProposta.nome",
        lazy='subquery',
        backref=db.backref('propostas', lazy='dynamic')
    )
    
    ofertas_selecionadas = db.relationship(
        'Oferta', 
        secondary=proposta_ofertas,
        primaryjoin="Proposta.id == proposta_ofertas.c.proposta_id",
        secondaryjoin="proposta_ofertas.c.oferta_id == Oferta.id",
        lazy='subquery',
        backref=db.backref('propostas', lazy='dynamic')
    )

# Modelo de Rascunho
class Rascunho(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    nome_cliente = db.Column(db.String(100), nullable=False)
    logo_cliente = db.Column(db.String(255))
    modelo_proposta = db.Column(db.String(255))
    usuario = db.Column(db.String(50))
    data_atualizacao = db.Column(db.DateTime, default=datetime.utcnow)
    blocos_selecionados = db.Column(JSONB)
    blocos_temporarios = db.Column(JSONB) 

# Modelo de associação entre Usuário e Blocos
class UsuarioBloco(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id', ondelete='CASCADE'), nullable=False)
    bloco_nome = db.Column(db.String(100), db.ForeignKey('bloco_proposta.nome', ondelete='CASCADE'), nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    usuario = db.relationship('Usuario', backref=db.backref('permissoes_blocos', lazy='dynamic'))
    bloco = db.relationship('BlocoProposta', backref=db.backref('permissoes_usuarios', lazy='dynamic')) 