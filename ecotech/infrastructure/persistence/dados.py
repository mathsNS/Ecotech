import sqlite3
from datetime import datetime

class Dados:

    def __init__(self):
        self.conn = sqlite3.connect('ecotech.db')
        self.conn.row_factory = sqlite3.Row
        self.criar_tabelas()

    def criar_tabelas(self):
        c = self.conn.cursor()

        # Tabelas de Usuários
        c.execute("""
        CREATE TABLE IF NOT EXISTS usuario (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            codigo TEXT,
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
            id_usuario INTEGER,
            timestamp TEXT,
            mensagem TEXT,
            FOREIGN KEY(id_usuario) REFERENCES usuario(id)   
        )
        """)

        # Tabela de Dispositivos
        c.execute("""
        CREATE TABLE IF NOT EXISTS dispositivo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            peso_kg REAL,
            marca TEXT,
            modelo TEXT
        )
        """)

        # Tabela de Ponto de Coleta
        c.execute("""
        CREATE TABLE IF NOT EXISTS ponto_coleta (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            endereco TEXT,
            latitude REAL,
            longitude REAL,
            ativo INTEGER,
            capacidade_kg REAL,
            ocupacao_atual_kg REAL 
        )
        """)

        # Tabelas de Descarte
        c.execute("""
        CREATE TABLE IF NOT EXISTS solicitacao_descarte (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER,
            id_ponto_coleta INTEGER,
            estado TEXT,
            metodo_tratamento TEXT,
            data_criacao TEXT,
            data_agendamento TEXT,
            FOREIGN KEY(id_usuario) REFERENCES usuario(id),
            FOREIGN KEY(id_ponto_coleta) REFERENCES ponto_coleta(id)
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS item_descarte (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_dispositivo INTEGER,
            id_solicitacao INTEGER,
            quantidade INTEGER,
            observacoes TEXT,
            FOREIGN KEY(id_dispositivo) REFERENCES dispositivo(id),
            FOREIGN KEY(id_solicitacao) REFERENCES solicitacao_descarte(id)
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS historico_rastreamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_solicitacao INTEGER,
            timestamp TEXT,
            mensagem TEXT,
            FOREIGN KEY(id_solicitacao) REFERENCES solicitacao_descarte(id) 
        )
        """)

        self.conn.commit()

    # -------------------
    # SALVAR
    # -------------------

    def salvar_cidadao(self, cidadao):
        c = self.conn.cursor()

        c.execute("""
        INSERT INTO usuario (codigo, nome, email, data_cadastro, ativo, tipo)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (cidadao.id, cidadao.nome, cidadao.email, datetime.now().strftime("%d/%m/%Y %H:%M"), True, "cidadao"))
        
        id_usuario = c.lastrowid

        c.execute("INSERT INTO cidadao (id_usuario, cpf, solicitacoes_ativas, pontos) VALUES (?, ?, ?, ?)", (id_usuario, cidadao.cpf, 0, 0))

        self.conn.commit()

    def salvar_empresa(self, empresa):
        c = self.conn.cursor()

        c.execute("""
        INSERT INTO usuario (codigo, nome, email, data_cadastro, ativo, tipo)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (empresa.id, empresa.nome, empresa.email, datetime.now().strftime("%d/%m/%Y %H:%M"), True, 'empresa'))
        
        id_usuario = c.lastrowid

        c.execute("INSERT INTO empresa (id_usuario, cnpj, razao_social, limite_mensal, descartado_mes) VALUES (?, ?, ?, ?, ?)", (id_usuario, empresa.cnpj, empresa.razao_social, 0, 0))

        self.conn.commit()

    def salvar_administrador(self, administrador):
        c = self.conn.cursor()

        c.execute("""
        INSERT INTO usuario (codigo, nome, email, data_cadastro, ativo, tipo)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (administrador.id, administrador.nome, administrador.email, datetime.now().strftime("%d/%m/%Y %H:%M"), True, "cidadao"))
        
        id_usuario = c.lastrowid

        c.execute("INSERT INTO administrador (id_usuario, nivel) VALUES (?, ?, ?, ?)", (id_usuario, administrador.nivel))

        self.conn.commit()

d = Dados()