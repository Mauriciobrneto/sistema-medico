import os
import pymysql
from dotenv import load_dotenv
from werkzeug.security import check_password_hash

load_dotenv()


# ============================================================
# CONEXÃO COM BANCO
# ============================================================

def get_db_connection():
    """Cria e retorna uma conexão com o banco MySQL."""
    return pymysql.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        user=os.getenv('DB_USER', 'root'),
        password=os.getenv('DB_PASSWORD', ''),
        db=os.getenv('DB_NAME', 'sistema'),
        port=int(os.getenv('DB_PORT', 3306)),
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor
    )


def fetch_one(sql, params=None):
    """Executa SELECT e retorna apenas um registro."""
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchone()
    finally:
        conn.close()


def fetch_all(sql, params=None):
    """Executa SELECT e retorna vários registros."""
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            return cursor.fetchall()
    finally:
        conn.close()


def execute_query(sql, params=None):
    """Executa INSERT, UPDATE ou DELETE."""
    conn = get_db_connection()

    try:
        with conn.cursor() as cursor:
            cursor.execute(sql, params or ())
            conn.commit()
            return cursor.lastrowid
    finally:
        conn.close()


# ============================================================
# LOGIN
# ============================================================

def check_user(username, password):
    """Busca usuário pelo nome e valida senha criptografada."""
    sql = "SELECT * FROM usuarios WHERE nome = %s"
    user = fetch_one(sql, (username,))

    if user and check_password_hash(user['senha'], password):
        return user

    return None


# ============================================================
# PACIENTES
# ============================================================

def inserir_paciente(nome, idade, dnacimento, cpf, telefone, convenio, foto,
                     rua, cidade, estado, pais, numero, historico=''):
    sql = """
        INSERT INTO pacientes
        (nome, idade, dnacimento, cpf, telefone, convenio, foto,
         rua, cidade, estado, pais, numero, historico)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """

    params = (
        nome, idade, dnacimento, cpf, telefone, convenio, foto,
        rua, cidade, estado, pais, numero, historico
    )

    return execute_query(sql, params)


def obter_pacientes():
    sql = """
        SELECT p.*,
            (
                SELECT GROUP_CONCAT(
                    CONCAT(
                        c.data, ' - ',
                        c.horario, ' - ',
                        c.consultas_convenio, ' - ',
                        c.motivo, ' - ',
                        c.diagnostico
                    )
                    SEPARATOR '\\n'
                )
                FROM consultas c
                WHERE c.paciente_id = p.id
            ) AS historico
        FROM pacientes p
        ORDER BY p.nome ASC
    """

    return fetch_all(sql)


def buscar_pacientes(search_term):
    sql = """
        SELECT *
        FROM pacientes
        WHERE nome LIKE %s OR cpf LIKE %s
        ORDER BY nome ASC
    """

    termo = f"%{search_term}%"
    return fetch_all(sql, (termo, termo))


def obter_paciente_por_id(id):
    sql = "SELECT * FROM pacientes WHERE id = %s"
    return fetch_one(sql, (id,))


def atualizar_paciente(id, nome, idade, dnacimento, cpf, convenio, foto,
                       rua, cidade, estado, pais, numero, historico=''):
    sql = """
        UPDATE pacientes
        SET nome = %s,
            idade = %s,
            dnacimento = %s,
            cpf = %s,
            convenio = %s,
            foto = %s,
            rua = %s,
            cidade = %s,
            estado = %s,
            pais = %s,
            numero = %s,
            historico = %s
        WHERE id = %s
    """

    params = (
        nome, idade, dnacimento, cpf, convenio, foto,
        rua, cidade, estado, pais, numero, historico, id
    )

    execute_query(sql, params)


def deletar_paciente(paciente_id):
    consultas = obter_consultas_por_paciente_id(paciente_id)

    if consultas:
        raise ValueError(
            "Existem consultas associadas a este paciente. Não é possível deletar."
        )

    sql = "DELETE FROM pacientes WHERE id = %s"
    execute_query(sql, (paciente_id,))


# ============================================================
# CONSULTAS
# ============================================================

def inserir_consulta(data, horario, paciente_id, consultas_convenio, motivo, diagnostico):
    sql = """
        INSERT INTO consultas
        (data, horario, paciente_id, consultas_convenio, motivo, diagnostico)
        VALUES (%s, %s, %s, %s, %s, %s)
    """

    params = (data, horario, paciente_id, consultas_convenio, motivo, diagnostico)
    return execute_query(sql, params)


def obter_consultas():
    sql = """
        SELECT consultas.*,
               pacientes.nome AS paciente_nome
        FROM consultas
        JOIN pacientes ON consultas.paciente_id = pacientes.id
        ORDER BY consultas.data DESC, consultas.horario ASC
    """

    return fetch_all(sql)


def obter_consultas_por_data(data):
    sql = """
        SELECT consultas.*,
               pacientes.nome AS paciente_nome,
               consultas.consultas_convenio AS convenio
        FROM consultas
        JOIN pacientes ON consultas.paciente_id = pacientes.id
        WHERE consultas.data = %s
        ORDER BY consultas.horario ASC
    """

    return fetch_all(sql, (data,))


def obter_consulta_por_id(id):
    sql = "SELECT * FROM consultas WHERE id = %s"
    return fetch_one(sql, (id,))


def obter_consultas_por_paciente_id(paciente_id):
    sql = """
        SELECT *
        FROM consultas
        WHERE paciente_id = %s
        ORDER BY data DESC, horario DESC
    """

    return fetch_all(sql, (paciente_id,))


def atualizar_consulta(id, data, horario, paciente_id, motivo, diagnostico=''):
    sql = """
        UPDATE consultas
        SET data = %s,
            horario = %s,
            paciente_id = %s,
            motivo = %s,
            diagnostico = %s
        WHERE id = %s
    """

    params = (data, horario, paciente_id, motivo, diagnostico, id)
    execute_query(sql, params)


def deletar_consulta(id):
    sql = "DELETE FROM consultas WHERE id = %s"
    execute_query(sql, (id,))


# ============================================================
# USUÁRIOS
# ============================================================

def inserir_usuario(username, password, email, nivel_acesso):
    sql = """
        INSERT INTO usuarios
        (nome, senha, email, nivel_acesso)
        VALUES (%s, %s, %s, %s)
    """

    return execute_query(sql, (username, password, email, nivel_acesso))


def obter_usuarios():
    sql = """
        SELECT *
        FROM usuarios
        ORDER BY nome ASC
    """

    return fetch_all(sql)


def obter_usuario_por_id(id):
    sql = "SELECT * FROM usuarios WHERE idusuarios = %s"
    return fetch_one(sql, (id,))


def atualizar_usuario(id, username, password, email, nivel_acesso):
    sql = """
        UPDATE usuarios
        SET nome = %s,
            senha = %s,
            email = %s,
            nivel_acesso = %s
        WHERE idusuarios = %s
    """

    execute_query(sql, (username, password, email, nivel_acesso, id))


def deletar_usuario(id):
    sql = "DELETE FROM usuarios WHERE idusuarios = %s"
    execute_query(sql, (id,))


# ============================================================
# ANOTAÇÕES
# ============================================================

def inserir_anotacao(user_id, conteudo):
    sql = """
        INSERT INTO anotacoes
        (user_id, conteudo)
        VALUES (%s, %s)
    """

    return execute_query(sql, (user_id, conteudo))


def obter_anotacoes_por_usuario(user_id):
    sql = """
        SELECT *
        FROM anotacoes
        WHERE user_id = %s
        ORDER BY data_criacao DESC
    """

    return fetch_all(sql, (user_id,))


def deletar_anotacao(id):
    sql = "DELETE FROM anotacoes WHERE id = %s"
    execute_query(sql, (id,))

def atualizar_status_consulta(id, status):
    sql = """
        UPDATE consultas
        SET status = %s
        WHERE id = %s
    """

    execute_query(sql, (status, id))

# ============================================================
# LOGS DO SISTEMA
# Compatível com a tabela atual:
# id, acao, item_afetado, item_id, usuario_id, data_hora
# ============================================================

def registrar_log(usuario_id, acao, item_afetado='', item_id=0):
    sql = """
        INSERT INTO logs
        (acao, item_afetado, item_id, usuario_id)
        VALUES (%s, %s, %s, %s)
    """

    execute_query(sql, (
        acao,
        item_afetado,
        item_id,
        usuario_id
    ))


def obter_logs(limite=300):
    sql = """
        SELECT
            logs.*,
            usuarios.nome AS usuario_nome
        FROM logs
        LEFT JOIN usuarios
            ON logs.usuario_id = usuarios.idusuarios
        ORDER BY logs.data_hora DESC
        LIMIT %s
    """

    return fetch_all(sql, (limite,))