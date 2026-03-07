import sqlite3

class Dados:

    def __init__(self):
        self.conn = sqlite3.connect('ecotech.db')
        self.conn.row_factory = sqlite3.Row
        self.criar_tabelas()

    def criar_tabelas(self):
        c = self.conn.cursor()

        # Tabela de Usuários
        c.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            email TEXT,
            data_cadastro TEXT,
            ativo INTEGER,
            tipo TEXT   
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS cidadao (
            id_usuario INTEGER PRIMARY KEY,
            cpf TEXT,
            solicitacoes_ativas INTEGER,
            pontos INTEGER,
            FOREIGN KEY(id_usuario) REFERENCES usuario(id)
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS empresa (
            id_usuario INTEGER PRIMARY KEY,
            cnpj TEXT,
            razao_social TEXT,
            limite_mensal REAL,
            descartado_mes REAL,
            FOREIGN KEY(id_usuario) REFERENCES usuario(id)
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS administrador (
            id_usuario INTEGER PRIMARY KEY,
            nivel INTEGER,
            FOREIGN KEY(id_usuario) REFERENCES usuario(id)
        )
        """)

        # Tabela de Notificações
        c.execute("""
        CREATE TABLE IF NOT EXISTS notificacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER
            timestamp TEXT,
            mensagem TEXT,
            FOREIGN KEY(id_usuario) REFERENCES usuario(id)   
        )
        """)

        self.conn.commit()

d = Dados()