from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib
import os

app = Flask(__name__, static_folder='static')
CORS(app)

# ============================================================
# CONFIGURAÇÕES
# ============================================================
db_url = os.environ.get('DATABASE_URL', 'sqlite:///sonhar.db')
db_url = os.environ.get('DATABASE_URL', 'postgresql+pg8000://postgres:yqqVKbvMhpcjLCEqDVnxBLkHVFkGvuiA@thomas.proxy.rlwy.net:24843/railway')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql+pg8000://', 1)
elif db_url.startswith('postgresql://'):
    db_url = db_url.replace('postgresql://', 'postgresql+pg8000://', 1)
print(f'>>> BANCO EM USO: {db_url[:60]}')
app.config['SQLALCHEMY_DATABASE_URI'] = db_url

POSTBACK_KEY = os.environ.get('POSTBACK_KEY', 'aeb82267e3b25c1d2debe5b4eaf64337')

db = SQLAlchemy(app)

# ============================================================
# MODELOS — BANCO DE DADOS
# ============================================================
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id          = db.Column(db.Integer, primary_key=True)
    nome        = db.Column(db.String(120), nullable=False)
    cpf         = db.Column(db.String(14), unique=True, nullable=False)
    senha_hash  = db.Column(db.String(64), nullable=False)
    perfil      = db.Column(db.String(20), default='atendente')  # gestor | atendente
    ativo       = db.Column(db.Boolean, default=True)
    criado_em   = db.Column(db.DateTime, default=datetime.utcnow)

    def check_senha(self, senha):
        return self.senha_hash == hashlib.sha256(senha.encode()).hexdigest()

    def to_dict(self):
        return {
            'id': self.id, 'nome': self.nome, 'cpf': self.cpf,
            'perfil': self.perfil, 'ativo': self.ativo
        }


class Atendente(db.Model):
    __tablename__ = 'atendentes'
    id              = db.Column(db.Integer, primary_key=True)
    nome            = db.Column(db.String(120), nullable=False)
    cpf             = db.Column(db.String(14), unique=True, nullable=False)
    telefone        = db.Column(db.String(20))
    admissao        = db.Column(db.Date)
    desligamento    = db.Column(db.Date)
    fixo            = db.Column(db.Float, default=400.0)
    automacao       = db.Column(db.Float, default=67.0)
    trafego         = db.Column(db.Float, default=800.0)
    investimento    = db.Column(db.Float, default=167.47)
    dias_trabalhados= db.Column(db.Integer, default=28)
    status          = db.Column(db.String(10), default='ativo')
    criado_em       = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id, 'nome': self.nome, 'cpf': self.cpf,
            'telefone': self.telefone,
            'admissao': self.admissao.isoformat() if self.admissao else None,
            'desligamento': self.desligamento.isoformat() if self.desligamento else None,
            'fixo': self.fixo, 'automacao': self.automacao,
            'trafego': self.trafego, 'investimento': self.investimento,
            'dias_trabalhados': self.dias_trabalhados, 'status': self.status
        }


class Pedido(db.Model):
    __tablename__ = 'pedidos'
    id              = db.Column(db.Integer, primary_key=True)
    pedido_id_ext   = db.Column(db.String(80), unique=True)   # ID da Sonhar Digital
    atendente_id    = db.Column(db.Integer, db.ForeignKey('atendentes.id'))
    cliente_nome    = db.Column(db.String(120))
    cliente_cpf     = db.Column(db.String(14))
    cliente_tel     = db.Column(db.String(20))
    cliente_email   = db.Column(db.String(120))
    produto         = db.Column(db.String(120))
    kit             = db.Column(db.String(20))   # kit1 | kit3 | kit5 | kit12
    valor           = db.Column(db.Float, default=0.0)
    comissao        = db.Column(db.Float, default=0.0)
    status          = db.Column(db.String(30), default='pendente')
    # pendente | aprovado | cancelado | enviado | entregue | devolvido
    status_rastreio = db.Column(db.String(30))
    codigo_rastreio = db.Column(db.String(30))
    origem          = db.Column(db.String(20), default='atendente')  # atendente | postback
    dados_raw       = db.Column(db.Text)   # JSON bruto recebido do postback
    criado_em       = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em   = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'pedido_id_ext': self.pedido_id_ext,
            'atendente_id': self.atendente_id,
            'cliente_nome': self.cliente_nome,
            'cliente_cpf': self.cliente_cpf,
            'cliente_tel': self.cliente_tel,
            'cliente_email': self.cliente_email,
            'produto': self.produto,
            'kit': self.kit,
            'valor': self.valor,
            'comissao': self.comissao,
            'status': self.status,
            'status_rastreio': self.status_rastreio,
            'codigo_rastreio': self.codigo_rastreio,
            'origem': self.origem,
            'criado_em': self.criado_em.isoformat(),
            'atualizado_em': self.atualizado_em.isoformat(),
        }


class AtividadeDia(db.Model):
    __tablename__ = 'atividades_dia'
    id           = db.Column(db.Integer, primary_key=True)
    atendente_id = db.Column(db.Integer, db.ForeignKey('atendentes.id'))
    data         = db.Column(db.Date, nullable=False)
    leads        = db.Column(db.Integer, default=0)
    ligacoes     = db.Column(db.Integer, default=0)
    __table_args__ = (db.UniqueConstraint('atendente_id', 'data'),)

    def to_dict(self):
        return {
            'id': self.id, 'atendente_id': self.atendente_id,
            'data': self.data.isoformat(), 'leads': self.leads, 'ligacoes': self.ligacoes
        }


# ============================================================
# ROTAS — POSTBACK SONHAR DIGITAL
# ============================================================
@app.route('/postback/sonhar', methods=['POST'])
def postback_sonhar():
    """Recebe pedidos automáticos da Sonhar Digital via PostBack"""
    # Validar chave
    chave = request.headers.get('X-Postback-Key') or request.args.get('key') or ''
    if chave != POSTBACK_KEY:
        return jsonify({'erro': 'Chave inválida'}), 401

    data = request.get_json(silent=True) or request.form.to_dict()
    if not data:
        return jsonify({'erro': 'Payload vazio'}), 400

    import json

    # Mapear campos da Sonhar Digital → nosso modelo
    pedido_id_ext = str(data.get('id') or data.get('order_id') or data.get('pedido_id') or '')
    status_raw    = str(data.get('status') or data.get('situacao') or 'pendente').lower()

    # Normalizar status
    status_map = {
        'aprovado': 'aprovado', 'approved': 'aprovado', 'pago': 'aprovado',
        'cancelado': 'cancelado', 'cancelled': 'cancelado', 'canceled': 'cancelado',
        'pendente': 'pendente', 'pending': 'pendente', 'aguardando': 'pendente',
        'enviado': 'enviado', 'shipped': 'enviado',
        'entregue': 'entregue', 'delivered': 'entregue',
        'devolvido': 'devolvido', 'returned': 'devolvido',
    }
    status = status_map.get(status_raw, 'pendente')

    # Verificar se pedido já existe (atualizar status)
    pedido = Pedido.query.filter_by(pedido_id_ext=pedido_id_ext).first() if pedido_id_ext else None

    if pedido:
        pedido.status          = status
        pedido.status_rastreio = data.get('status_rastreio') or data.get('tracking_status')
        pedido.codigo_rastreio = data.get('codigo_rastreio') or data.get('tracking_code')
        pedido.atualizado_em   = datetime.utcnow()
        db.session.commit()
        return jsonify({'ok': True, 'acao': 'atualizado', 'id': pedido.id})

    # Criar novo pedido
    valor    = float(data.get('valor') or data.get('value') or data.get('amount') or 0)
    comissao = round(valor * 0.10, 2)

    # Detectar kit pelo valor
    kit_map = {197: 'kit1', 297: 'kit3', 397: 'kit5', 697: 'kit12'}
    kit = kit_map.get(int(valor), 'kit1')

    novo = Pedido(
        pedido_id_ext   = pedido_id_ext,
        cliente_nome    = data.get('nome') or data.get('customer_name') or data.get('cliente'),
        cliente_cpf     = data.get('cpf') or data.get('document'),
        cliente_tel     = data.get('telefone') or data.get('phone'),
        cliente_email   = data.get('email'),
        produto         = data.get('produto') or data.get('product_name'),
        kit             = kit,
        valor           = valor,
        comissao        = comissao,
        status          = status,
        status_rastreio = data.get('status_rastreio') or data.get('tracking_status'),
        codigo_rastreio = data.get('codigo_rastreio') or data.get('tracking_code'),
        origem          = 'postback',
        dados_raw       = json.dumps(data, ensure_ascii=False),
    )
    db.session.add(novo)
    db.session.commit()
    return jsonify({'ok': True, 'acao': 'criado', 'id': novo.id}), 201


# ============================================================
# ROTAS — AUTENTICAÇÃO
# ============================================================
@app.route('/api/login', methods=['POST'])
def login():
    data  = request.get_json()
    cpf   = data.get('cpf','').strip()
    senha = data.get('senha','').strip()
    user  = Usuario.query.filter_by(cpf=cpf, ativo=True).first()
    if not user or not user.check_senha(senha):
        return jsonify({'erro': 'CPF ou senha incorretos'}), 401
    return jsonify({'ok': True, 'usuario': user.to_dict()})


# ============================================================
# ROTAS — ATENDENTES
# ============================================================
@app.route('/api/atendentes', methods=['GET'])
def listar_atendentes():
    ats = Atendente.query.all()
    return jsonify([a.to_dict() for a in ats])

@app.route('/api/atendentes', methods=['POST'])
def criar_atendente():
    d = request.get_json()
    at = Atendente(
        nome=d['nome'], cpf=d['cpf'], telefone=d.get('telefone'),
        fixo=d.get('fixo',400), automacao=d.get('automacao',67),
        trafego=d.get('trafego',800), investimento=d.get('investimento',167.47),
        dias_trabalhados=d.get('dias',28), status=d.get('status','ativo')
    )
    db.session.add(at); db.session.commit()
    return jsonify(at.to_dict()), 201

@app.route('/api/atendentes/<int:id>', methods=['PUT'])
def atualizar_atendente(id):
    at = Atendente.query.get_or_404(id)
    d  = request.get_json()
    for campo in ['nome','cpf','telefone','fixo','automacao','trafego','investimento','dias_trabalhados','status']:
        if campo in d: setattr(at, campo, d[campo])
    db.session.commit()
    return jsonify(at.to_dict())

@app.route('/api/atendentes/<int:id>', methods=['DELETE'])
def deletar_atendente(id):
    at = Atendente.query.get_or_404(id)
    db.session.delete(at); db.session.commit()
    return jsonify({'ok': True})


# ============================================================
# ROTAS — PEDIDOS
# ============================================================
@app.route('/api/pedidos', methods=['GET'])
def listar_pedidos():
    status       = request.args.get('status')
    atendente_id = request.args.get('atendente_id')
    q = Pedido.query
    if status:       q = q.filter_by(status=status)
    if atendente_id: q = q.filter_by(atendente_id=int(atendente_id))
    pedidos = q.order_by(Pedido.criado_em.desc()).all()
    return jsonify([p.to_dict() for p in pedidos])

@app.route('/api/pedidos', methods=['POST'])
def criar_pedido():
    d = request.get_json()
    valor    = float(d.get('valor', 0))
    comissao = round(valor * 0.10, 2)
    p = Pedido(
        atendente_id = d.get('atendente_id'),
        cliente_nome = d.get('cliente_nome'),
        cliente_cpf  = d.get('cliente_cpf'),
        cliente_tel  = d.get('cliente_tel'),
        produto      = d.get('produto'),
        kit          = d.get('kit'),
        valor        = valor,
        comissao     = comissao,
        status       = d.get('status', 'pendente'),
        origem       = 'atendente',
    )
    db.session.add(p); db.session.commit()
    return jsonify(p.to_dict()), 201

@app.route('/api/pedidos/<int:id>/status', methods=['PATCH'])
def atualizar_status_pedido(id):
    p = Pedido.query.get_or_404(id)
    d = request.get_json()
    p.status          = d.get('status', p.status)
    p.status_rastreio = d.get('status_rastreio', p.status_rastreio)
    p.codigo_rastreio = d.get('codigo_rastreio', p.codigo_rastreio)
    p.atualizado_em   = datetime.utcnow()
    db.session.commit()
    return jsonify(p.to_dict())

@app.route('/api/pedidos/<int:id>', methods=['DELETE'])
def deletar_pedido(id):
    p = Pedido.query.get_or_404(id)
    db.session.delete(p); db.session.commit()
    return jsonify({'ok': True})


# ============================================================
# ROTAS — ATIVIDADES DO DIA
# ============================================================
@app.route('/api/atividades', methods=['POST'])
def salvar_atividade():
    d    = request.get_json()
    data = datetime.strptime(d['data'], '%Y-%m-%d').date()
    atv  = AtividadeDia.query.filter_by(atendente_id=d['atendente_id'], data=data).first()
    if atv:
        atv.leads    = d.get('leads', atv.leads)
        atv.ligacoes = d.get('ligacoes', atv.ligacoes)
    else:
        atv = AtividadeDia(atendente_id=d['atendente_id'], data=data,
                           leads=d.get('leads',0), ligacoes=d.get('ligacoes',0))
        db.session.add(atv)
    db.session.commit()
    return jsonify(atv.to_dict())

@app.route('/api/atividades/<int:atendente_id>', methods=['GET'])
def listar_atividades(atendente_id):
    ativs = AtividadeDia.query.filter_by(atendente_id=atendente_id).all()
    return jsonify([a.to_dict() for a in ativs])


# ============================================================
# ROTAS — DASHBOARD / RESUMO
# ============================================================
@app.route('/api/resumo', methods=['GET'])
def resumo():
    total_pedidos  = Pedido.query.count()
    aprovados      = Pedido.query.filter_by(status='aprovado').all()
    pendentes      = Pedido.query.filter_by(status='pendente').count()
    faturamento    = sum(p.valor for p in aprovados)
    comissoes      = sum(p.comissao for p in aprovados)
    return jsonify({
        'total_pedidos': total_pedidos,
        'aprovados': len(aprovados),
        'pendentes': pendentes,
        'faturamento': faturamento,
        'comissoes': comissoes,
    })


# ============================================================
# SERVIR O FRONTEND
# ============================================================
@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)


# ============================================================
# INICIALIZAÇÃO
# ============================================================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Criar gestor padrão se não existir
        if not Usuario.query.filter_by(cpf='000.000.000-00').first():
            gestor = Usuario(
                nome='Gestor Master',
                cpf='000.000.000-00',
                senha_hash=hashlib.sha256('admin123'.encode()).hexdigest(),
                perfil='gestor'
            )
            db.session.add(gestor)
            db.session.commit()
            print('✅ Gestor padrão criado: CPF 000.000.000-00 / senha admin123')
    print('🚀 Backend Sonhar Digital rodando em http://localhost:5000')
    app.run(debug=True, host='0.0.0.0', port=5000)
