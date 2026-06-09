import os
import logging
from functools import wraps
from datetime import date, datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file
from flask_paginate import Pagination, get_page_args
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

import banco
from banco import registrar_log

import subprocess

import base64
from PIL import Image
from io import BytesIO


# ============================================================
# CONFIGURAÇÕES INICIAIS
# ============================================================

load_dotenv()

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.secret_key = os.getenv('SECRET_KEY', 'agenda_medica_dev')
app.permanent_session_lifetime = timedelta(minutes=45)
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024


# ============================================================
# LOGS
# ============================================================

logging.basicConfig(
    filename='app.log',
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


# ============================================================
# UPLOADS
# ============================================================

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    """Verifica se o arquivo enviado possui extensão permitida."""
    return (
        '.' in filename and
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
    )


def salvar_foto(foto):
    """Salva uma imagem enviada e retorna o nome do arquivo."""
    if foto and foto.filename != '' and allowed_file(foto.filename):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        filename = f"{timestamp}_{secure_filename(foto.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        foto.save(filepath)
        return filename

    return ''

def salvar_foto_webcam(imagem_base64):
    """Salva foto capturada pela webcam em JPG redimensionado."""

    if not imagem_base64:
        return ''

    try:
        cabecalho, dados = imagem_base64.split(',', 1)
        imagem_bytes = base64.b64decode(dados)

        imagem = Image.open(BytesIO(imagem_bytes)).convert('RGB')

        imagem.thumbnail((600, 600))

        nome_arquivo = f"webcam_{datetime.now().strftime('%Y%m%d%H%M%S')}.jpg"
        caminho = os.path.join(app.config['UPLOAD_FOLDER'], nome_arquivo)

        imagem.save(caminho, 'JPEG', quality=85, optimize=True)

        return nome_arquivo

    except Exception as erro:
        app.logger.error(f"Erro ao salvar foto da webcam: {erro}", exc_info=True)
        return ''


# ============================================================
# AUTENTICAÇÃO E PERMISSÕES
# ============================================================

def verificar_autenticacao():
    """Verifica se existe usuário logado na sessão."""
    return 'user_id' in session


def login_required(f):
    """Protege rotas que exigem login."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not verificar_autenticacao():
            flash('Você precisa estar logado para acessar esta página.', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """Protege rotas permitidas apenas para administradores."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('nivel_acesso') != 'Administrador':
            flash('Acesso negado. Apenas administradores podem acessar esta página.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)

    return decorated_function


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def formatar_cpf(cpf):
    """Remove caracteres e formata CPF no padrão 000.000.000-00."""
    cpf_numerico = ''.join(filter(str.isdigit, cpf))

    if len(cpf_numerico) != 11:
        raise ValueError('CPF deve conter 11 dígitos.')

    return '{}.{}.{}-{}'.format(
        cpf_numerico[:3],
        cpf_numerico[3:6],
        cpf_numerico[6:9],
        cpf_numerico[9:]
    )


def formatar_dnascimento(dnascimento):
    """
    Remove caracteres e formata nascimento no padrão DD/MM/AAAA.
    Mantive o nome dnacimento para compatibilidade com teu banco atual.
    """
    dnascimento_numerico = ''.join(filter(str.isdigit, dnascimento))

    if len(dnascimento_numerico) != 8:
        raise ValueError('Data de nascimento deve conter 8 dígitos.')

    return '{}/{}/{}'.format(
        dnascimento_numerico[:2],
        dnascimento_numerico[2:4],
        dnascimento_numerico[4:]
    )


# ============================================================
# LOGIN / LOGOUT
# ============================================================

@app.route('/')
def index():
    """Tela de login."""
    if verificar_autenticacao():
        return redirect(url_for('dashboard'))

    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    """Realiza autenticação do usuário."""
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')

    user = banco.check_user(username, password)

    if user:
        session.permanent = True
        session['user_id'] = user['idusuarios']
        session['username'] = user['nome']
        registrar_log(
            user['idusuarios'],
            'Login no sistema',
            'Usuário',
            user['idusuarios']
        )

        session['nivel_acesso'] = user['nivel_acesso']

        app.logger.info(f"Login realizado pelo usuário: {username}")
        return redirect(url_for('dashboard'))

    flash('Usuário ou senha inválidos.', 'error')
    app.logger.warning(f"Tentativa de login inválida para usuário: {username}")
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    """Encerra a sessão do usuário."""

    username = session.get('username')
    user_id = session.get('user_id')

    if user_id:
        registrar_log(
            user_id,
            'Logout do sistema',
            'Usuário',
            user_id
        )

    session.clear()

    app.logger.info(f"Logout realizado pelo usuário: {username}")

    return redirect(url_for('index'))


# ============================================================
# DASHBOARD
# ============================================================

@app.route('/dashboard')
@login_required
def dashboard():

    consultas_hoje = banco.obter_consultas_por_data(date.today())

    agendadas = [
    c for c in consultas_hoje
    if c['status'] == 'Agendada'
    ]

    aguardando = [
        c for c in consultas_hoje
        if c['status'] == 'Paciente chegou'
    ]

    em_atendimento = [
        c for c in consultas_hoje
        if c['status'] == 'Em atendimento'
    ]

    atendidas = [
        c for c in consultas_hoje
        if c['status'] == 'Atendida'
    ]

    anotacoes = banco.obter_anotacoes_por_usuario(
        session['user_id']
    )

    perfil = session.get('nivel_acesso')

    if perfil == 'Medico':
        template_dashboard = 'dashboard_medico.html'
    elif perfil == 'Secretaria':
        template_dashboard = 'dashboard_secretaria.html'
    else:
        template_dashboard = 'dashboard.html'

    return render_template(
        template_dashboard,
        username=session.get('username'),
        consultas_hoje=consultas_hoje,
        agendadas=agendadas,
        aguardando=aguardando,
        em_atendimento=em_atendimento,
        atendidas=atendidas,
        anotacoes=anotacoes
    )

# ============================================================
# PACIENTES
# ============================================================

@app.route('/cadastro_de_pacientes')
@login_required
def cadastro_de_pacientes():
    """Tela de cadastro de pacientes."""
    return render_template('cadastro_de_pacientes.html')


@app.route('/cadastrar_paciente', methods=['POST'])
@login_required
def cadastrar_paciente():
    """Cadastra um novo paciente."""
    try:
        nome = request.form['nome']
        idade = request.form['idade']
        dnacimento = formatar_dnascimento(request.form['dnacimento'])
        cpf = formatar_cpf(request.form['cpf'])
        telefone = request.form['telefone']
        convenio = request.form['convenio']
        rua = request.form['rua']
        cidade = request.form['cidade']
        estado = request.form['estado']
        pais = request.form['pais']
        numero = request.form['numero']
        historico = request.form.get('historico', '')

        foto = request.files.get('foto')
        foto_path = salvar_foto(foto)

        foto_webcam = request.form.get('foto_webcam')

        if foto_webcam:
            foto_path = salvar_foto_webcam(foto_webcam)

        paciente_id = banco.inserir_paciente(
            nome, idade, dnacimento, cpf, telefone, convenio,
            foto_path, rua, cidade, estado, pais, numero, historico
        )
        registrar_log(
            session.get('user_id'),
            'Cadastro de paciente',
            nome,
            paciente_id
        )

        flash('Paciente cadastrado com sucesso.', 'success')
        app.logger.info(f"Paciente cadastrado: {nome}")
        return redirect(url_for('consultar_pacientes'))

    except ValueError as erro_validacao:
        flash(str(erro_validacao), 'error')
        return redirect(url_for('cadastro_de_pacientes'))

    except Exception as erro:
        app.logger.error(f"Erro ao cadastrar paciente: {erro}", exc_info=True)
        flash('Erro ao cadastrar paciente. Verifique os dados e tente novamente.', 'error')
        return redirect(url_for('cadastro_de_pacientes'))


@app.route('/consultar_pacientes', methods=['GET'])
@login_required
def consultar_pacientes():
    """Lista e pesquisa pacientes."""
    search_term = request.args.get('search', '').strip()
    page, per_page, offset = get_page_args(
        page_parameter='page',
        per_page_parameter='per_page'
    )

    if search_term:
        pacientes = banco.buscar_pacientes(search_term)
    else:
        pacientes = banco.obter_pacientes()

    total = len(pacientes)
    pacientes_paginados = pacientes[offset: offset + per_page]

    pagination = Pagination(
        page=page,
        per_page=per_page,
        total=total,
        css_framework='bootstrap5'
    )

    return render_template(
        'consultar_pacientes.html',
        pacientes=pacientes_paginados,
        page=page,
        per_page=per_page,
        pagination=pagination
    )


@app.route('/editar_paciente/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_paciente(id):
    """Edita dados cadastrais do paciente."""
    paciente = banco.obter_paciente_por_id(id)

    if not paciente:
        flash('Paciente não encontrado.', 'error')
        return redirect(url_for('consultar_pacientes'))

    if request.method == 'POST':
        try:
            nome = request.form['nome']
            idade = request.form['idade']
            dnacimento = request.form['dnacimento']
            cpf = request.form['cpf']
            telefone = request.form.get('telefone', '')
            convenio = request.form['convenio']
            rua = request.form['rua']
            cidade = request.form['cidade']
            estado = request.form['estado']
            pais = request.form['pais']
            numero = request.form['numero']
            historico = request.form.get('historico', '')

            foto_path = paciente['foto']

            foto = request.files.get('foto')
            nova_foto = salvar_foto(foto)

            if nova_foto:
                foto_path = nova_foto

            banco.atualizar_paciente(
                id, nome, idade, dnacimento, cpf, convenio,
                foto_path, rua, cidade, estado, pais, numero, historico
            )
            registrar_log(
                session.get('user_id'),
                'Paciente editado',
                nome,
                id
            )

            flash('Paciente atualizado com sucesso.', 'success')
            app.logger.info(f"Paciente atualizado: {nome} ID {id}")
            return redirect(url_for('consultar_pacientes'))

        except Exception as erro:
            app.logger.error(f"Erro ao atualizar paciente ID {id}: {erro}", exc_info=True)
            flash(f"Erro ao atualizar paciente: {erro}", 'error')

    return render_template('editar_paciente.html', paciente=paciente)


@app.route('/deletar_paciente/<int:id>', methods=['POST'])
@login_required
def deletar_paciente(id):
    """Remove paciente se não houver consultas vinculadas."""
    paciente = banco.obter_paciente_por_id(id)

    if not paciente:
        flash('Paciente não encontrado.', 'error')
        return redirect(url_for('consultar_pacientes'))

    consultas = banco.obter_consultas_por_paciente_id(id)

    if consultas:
        flash('Não é possível deletar o paciente. Existem consultas associadas.', 'error')
        app.logger.warning(
            f"Usuário {session.get('username')} tentou deletar paciente com consultas: {paciente['nome']} ID {id}"
        )
        return redirect(url_for('consultar_pacientes'))

    banco.deletar_paciente(id)

    registrar_log(
        session.get('user_id'),
        'Paciente deletado',
        paciente['nome'],
        id
    )

    flash('Paciente deletado com sucesso.', 'success')
    app.logger.info(f"Paciente deletado: {paciente['nome']} ID {id}")
    return redirect(url_for('consultar_pacientes'))


@app.route('/historico_paciente/<int:id>')
@login_required
def historico_paciente(id):

    if session.get('nivel_acesso') == 'Secretaria':
        flash('Acesso não permitido para recepção.', 'danger')
        return redirect(url_for('consultar_pacientes'))

    """Exibe histórico completo do paciente."""
    paciente = banco.obter_paciente_por_id(id)

    if not paciente:
        flash('Paciente não encontrado.', 'error')
        return redirect(url_for('consultar_pacientes'))

    consultas = banco.obter_consultas_por_paciente_id(id)

    return render_template(
        'historico_paciente.html',
        paciente=paciente,
        consultas=consultas
    )


# ============================================================
# CONSULTAS
# ============================================================

@app.route('/agenda_consultas')
@login_required
def agenda_consultas():
    """Tela para agendar consulta."""
    pacientes = banco.obter_pacientes()
    return render_template('agenda_consultas.html', pacientes=pacientes)


@app.route('/agendar_consulta', methods=['POST'])
@login_required
def agendar_consulta():
    """Cadastra uma nova consulta."""
    try:
        data = request.form['data']
        horario = request.form['horario']
        paciente_id = request.form['paciente']
        consultas_convenio = request.form['consultas_convenio']
        motivo = request.form['motivo']
        if session.get('nivel_acesso') == 'Secretaria':
            diagnostico = ''
        else:
            diagnostico = request.form.get('diagnostico', '')

        consulta_id = banco.inserir_consulta(
            data, horario, paciente_id,
            consultas_convenio, motivo, diagnostico
        )
        registrar_log(
            session.get('user_id'),
            'Consulta agendada',
            f'Paciente ID {paciente_id}',
            consulta_id
        )

        flash('Consulta agendada com sucesso.', 'success')
        app.logger.info(f"Consulta agendada para paciente ID {paciente_id} em {data} às {horario}")
        return redirect(url_for('consulta_agenda'))

    except Exception as erro:
        app.logger.error(f"Erro ao agendar consulta: {erro}", exc_info=True)
        flash(f"Erro ao agendar consulta: {erro}", 'error')
        return redirect(url_for('agenda_consultas'))


@app.route('/consulta_agenda', methods=['GET'])
@login_required
def consulta_agenda():
    """Lista consultas e permite filtro por nome e data."""
    search_nome = request.args.get('search_nome', '').strip()
    search_data = request.args.get('search_data', date.today().strftime('%Y-%m-%d'))

    consultas = banco.obter_consultas()

    if search_nome:
        consultas = [
            consulta for consulta in consultas
            if search_nome.lower() in consulta['paciente_nome'].lower()
        ]

    if search_data:
        consultas = [
            consulta for consulta in consultas
            if search_data == consulta['data'].strftime('%Y-%m-%d')
        ]

    for consulta in consultas:
        consulta['data_formatada'] = consulta['data'].strftime('%d/%m/%Y')

    return render_template(
        'consulta_agenda.html',
        consultas=consultas,
        search_nome=search_nome,
        search_data=search_data
    )


@app.route('/editar_consulta/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_consulta(id):
    """Edita uma consulta existente."""
    consulta = banco.obter_consulta_por_id(id)

    if not consulta:
        flash('Consulta não encontrada.', 'error')
        return redirect(url_for('consulta_agenda'))

    if request.method == 'POST':
        try:
            data = request.form['data']
            horario = request.form['horario']
            paciente_id = request.form['paciente']
            motivo = request.form['motivo']
            if session.get('nivel_acesso') == 'Secretaria':
                diagnostico = consulta['diagnostico']
            else:
                diagnostico = request.form.get('diagnostico', '')

            banco.atualizar_consulta(
                id, data, horario,
                paciente_id, motivo, diagnostico
            )
            registrar_log(
                session.get('user_id'),
                'Consulta editada',
                f'Consulta ID {id}',
                id
            )

            flash('Consulta atualizada com sucesso.', 'success')
            app.logger.info(f"Consulta atualizada ID {id}")
            return redirect(url_for('consulta_agenda'))

        except Exception as erro:
            app.logger.error(f"Erro ao atualizar consulta ID {id}: {erro}", exc_info=True)
            flash(f"Erro ao atualizar consulta: {erro}", 'error')

    pacientes = banco.obter_pacientes()
    return render_template(
        'editar_consulta.html',
        consulta=consulta,
        pacientes=pacientes
    )


@app.route('/deletar_consulta/<int:id>', methods=['POST'])
@login_required
def deletar_consulta(id):
    """Remove uma consulta."""
    try:
        registrar_log(
            session.get('user_id'),
            'Consulta deletada',
            f'Consulta ID {id}',
            id
        )

        banco.deletar_consulta(id)

        flash('Consulta deletada com sucesso.', 'success')
        app.logger.info(f"Consulta deletada ID {id}")

    except Exception as erro:
        app.logger.error(f"Erro ao deletar consulta ID {id}: {erro}", exc_info=True)
        flash(f"Erro ao deletar consulta: {erro}", 'error')

    return redirect(url_for('consulta_agenda'))


# ============================================================
# USUÁRIOS
# ============================================================

@app.route('/cadastro_de_usuarios')
@login_required
@admin_required
def cadastro_de_usuarios():
    """Tela de cadastro de usuário."""
    return render_template('cadastro_de_usuarios.html')


@app.route('/gerenciar_usuarios')
@login_required
@admin_required
def gerenciar_usuarios():
    """Lista e gerencia usuários."""
    usuarios = banco.obter_usuarios()
    return render_template('gerenciar_usuarios.html', usuarios=usuarios)


@app.route('/cadastrar_usuario', methods=['POST'])
@login_required
@admin_required
def cadastrar_usuario():
    """Cadastra novo usuário com senha criptografada."""
    try:
        username = request.form['username']
        senha_digitada = request.form['password']

        if len(senha_digitada) < 6:
            flash('A senha deve ter no mínimo 6 caracteres.', 'warning')
            return redirect(url_for('gerenciar_usuarios'))

        password = generate_password_hash(senha_digitada)
        email = request.form['email']
        nivel_acesso = request.form['nivel_acesso']

        usuario_id = banco.inserir_usuario(username, password, email, nivel_acesso)
        registrar_log(
            session.get('user_id'),
            'Usuário cadastrado',
            username,
            usuario_id
        )

        flash('Usuário cadastrado com sucesso.', 'success')
        app.logger.info(f"Usuário cadastrado: {username}")
        return redirect(url_for('gerenciar_usuarios'))

    except Exception as erro:
        app.logger.error(f"Erro ao cadastrar usuário: {erro}", exc_info=True)
        flash('Erro ao cadastrar usuário.', 'error')
        return redirect(url_for('gerenciar_usuarios'))


@app.route('/editar_usuario/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def editar_usuario(id):
    """Edita usuário e gera nova senha criptografada."""
    usuario = banco.obter_usuario_por_id(id)

    if not usuario:
        flash('Usuário não encontrado.', 'error')
        return redirect(url_for('gerenciar_usuarios'))

    if request.method == 'POST':
        try:
            username = request.form['username']
            password = generate_password_hash(request.form['password'])
            email = request.form['email']
            nivel_acesso = request.form['nivel_acesso']

            banco.atualizar_usuario(id, username, password, email, nivel_acesso)

            registrar_log(
                session.get('user_id'),
                'Usuário editado',
                username,
                id
            )

            flash('Usuário atualizado com sucesso.', 'success')
            app.logger.info(f"Usuário atualizado: {username} ID {id}")
            return redirect(url_for('gerenciar_usuarios'))

        except Exception as erro:
            app.logger.error(f"Erro ao editar usuário ID {id}: {erro}", exc_info=True)
            flash(f"Erro ao editar usuário: {erro}", 'error')

    return render_template('editar_usuario.html', usuario=usuario)


@app.route('/deletar_usuario/<int:id>', methods=['POST'])
@login_required
@admin_required
def deletar_usuario(id):
    """Remove usuário."""
    try:
        if id == session.get('user_id'):
            flash('Você não pode deletar o próprio usuário logado.', 'warning')
            return redirect(url_for('gerenciar_usuarios'))

        registrar_log(
            session.get('user_id'),
            'Usuário deletado',
            f'Usuário ID {id}',
            id
        )

        banco.deletar_usuario(id)

        flash('Usuário deletado com sucesso.', 'success')
        app.logger.info(f"Usuário deletado ID {id}")

    except Exception as erro:
        app.logger.error(f"Erro ao deletar usuário ID {id}: {erro}", exc_info=True)
        flash(f"Erro ao deletar usuário: {erro}", 'error')

    return redirect(url_for('gerenciar_usuarios'))


# ============================================================
# ANOTAÇÕES
# ============================================================

@app.route('/anotacoes', methods=['POST'])
@login_required
def adicionar_anotacao():
    """Adiciona anotação no dashboard."""
    conteudo = request.form.get('conteudo', '').strip()

    if not conteudo:
        flash('A anotação não pode estar vazia.', 'warning')
        return redirect(url_for('dashboard'))

    anotacao_id = banco.inserir_anotacao(session['user_id'], conteudo)

    registrar_log(
        session.get('user_id'),
        'Anotação criada',
        'Anotação',
        anotacao_id
    )

    flash('Anotação adicionada com sucesso.', 'success')
    return redirect(url_for('dashboard'))


@app.route('/anotacoes/<int:id>/deletar', methods=['POST'])
@login_required
def deletar_anotacao(id):
    """Deleta anotação."""
    registrar_log(
        session.get('user_id'),
        'Anotação deletada',
        'Anotação',
        id
    )

    banco.deletar_anotacao(id)

    flash('Anotação deletada com sucesso.', 'success')
    return redirect(url_for('dashboard'))

# ============================================================
# STATUS DE ATENDIMENTO
# ============================================================
@app.route('/consulta/<int:id>/status/<status>', methods=['POST'])
@login_required
def atualizar_status_consulta(id, status):
    status_permitidos = [
        'Agendada',
        'Paciente chegou',
        'Em atendimento',
        'Atendida',
        'Cancelada',
        'Faltou'
    ]

    if status not in status_permitidos:
        flash('Status inválido.', 'error')
        return redirect(url_for('consulta_agenda'))

    banco.atualizar_status_consulta(id, status)
    registrar_log(
        session.get('user_id'),
        f'Status alterado para {status}',
        'Consulta',
        id
    )

    flash('Status da consulta atualizado com sucesso.', 'success')
    return redirect(url_for('consulta_agenda'))

# ============================================================
# ROTA DE ATENDIMENTOS
# ============================================================

@app.route('/atendimento/<int:id>', methods=['GET', 'POST'])
@login_required
def atendimento(id):
    """Tela de atendimento médico e finalização da consulta."""

    if session.get('nivel_acesso') == 'Secretaria':
        flash('Acesso não permitido.', 'danger')
        return redirect(url_for('dashboard'))

    consulta = banco.obter_consulta_por_id(id)

    if not consulta:
        flash('Consulta não encontrada.', 'error')
        return redirect(url_for('consulta_agenda'))

    paciente = banco.obter_paciente_por_id(consulta['paciente_id'])

    if not paciente:
        flash('Paciente não encontrado.', 'error')
        return redirect(url_for('consulta_agenda'))

    if consulta['status'] not in ['Em atendimento', 'Atendida']:
        banco.atualizar_status_consulta(
            consulta['id'],
            'Em atendimento'
        )

        registrar_log(
            session.get('user_id'),
            'Atendimento iniciado',
            paciente['nome'],
            consulta['id']
        )

        consulta['status'] = 'Em atendimento'

    historico = banco.obter_consultas_por_paciente_id(
        consulta['paciente_id']
    )

    if request.method == 'POST':
        diagnostico = request.form.get('diagnostico', '')
        motivo = request.form.get('motivo', '')

        banco.atualizar_consulta(
            consulta['id'],
            consulta['data'],
            consulta['horario'],
            consulta['paciente_id'],
            motivo,
            diagnostico
        )

        banco.atualizar_status_consulta(
            consulta['id'],
            'Atendida'
        )

        registrar_log(
            session.get('user_id'),
            'Atendimento finalizado',
            paciente['nome'],
            consulta['id']
        )

        flash('Atendimento finalizado com sucesso.', 'success')

        return redirect(url_for('consulta_agenda'))

    return render_template(
        'atendimento.html',
        consulta=consulta,
        paciente=paciente,
        historico=historico
    )

@app.route('/logs')
@login_required
@admin_required
def visualizar_logs():
    logs = banco.obter_logs()
    return render_template('logs.html', logs=logs)

@app.route('/backup')
@login_required
@admin_required
def realizar_backup():

    try:

        os.makedirs('backups', exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        nome_arquivo = f'backup_sistema_{timestamp}.sql'

        caminho_arquivo = os.path.join(
            'backups',
            nome_arquivo
        )

        comando = [
            r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysqldump.exe",
            '-u', os.getenv('DB_USER'),
            f"-p{os.getenv('DB_PASSWORD')}",
            os.getenv('DB_NAME')
        ]

        with open(caminho_arquivo, 'w', encoding='utf-8') as arquivo:

            subprocess.run(
                comando,
                stdout=arquivo,
                check=True
            )

        registrar_log(
            session.get('user_id'),
            'Backup manual realizado',
            nome_arquivo,
            0
        )

        app.logger.info(
            f"Backup realizado: {nome_arquivo}"
        )

        return send_file(
            caminho_arquivo,
            as_attachment=True
        )

    except Exception as erro:

        app.logger.error(
            f"Erro ao realizar backup: {erro}",
            exc_info=True
        )

        flash(
            f'Erro ao realizar backup: {erro}',
            'danger'
        )

        return redirect(
            url_for('dashboard')
        )
    
@app.route('/privacidade')
def privacidade():
    return render_template('privacidade.html')

# ============================================================
# EXECUÇÃO LOCAL
# ============================================================

if __name__ == '__main__':
    app.run(
        debug=False,
        host='0.0.0.0',
        port=5000
    )