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
            id TEXT PRIMARY KEY,
            nome TEXT,
            email TEXT,
            data_cadastro TEXT,
            ativo INTEGER,
            tipo TEXT   
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS cidadao (
            id_usuario TEXT PRIMARY KEY,
            cpf TEXT,
            solicitacoes_ativas INTEGER,
            pontos INTEGER,
            FOREIGN KEY(id_usuario) REFERENCES usuario(id)
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS empresa (
            id_usuario TEXT PRIMARY KEY,
            cnpj TEXT,
            razao_social TEXT,
            limite_mensal REAL,
            descartado_mes REAL,
            FOREIGN KEY(id_usuario) REFERENCES usuario(id)
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS administrador (
            id_usuario TEXT PRIMARY KEY,
            nivel INTEGER,
            FOREIGN KEY(id_usuario) REFERENCES usuario(id)
        )
        """)

        # Tabela de Notificações
        c.execute("""
        CREATE TABLE IF NOT EXISTS notificacao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario TEXT,
            timestamp TEXT,
            mensagem TEXT,
            FOREIGN KEY(id_usuario) REFERENCES usuario(id)   
        )
        """)

        # Tabela de Dispositivos
        c.execute("""
        CREATE TABLE IF NOT EXISTS dispositivo (
            id TEXT PRIMARY KEY,
            nome TEXT,
            peso_kg REAL,
            marca TEXT,
            modelo TEXT
        )
        """)

        # Tabela de Ponto de Coleta
        c.execute("""
        CREATE TABLE IF NOT EXISTS ponto_coleta (
            id TEXT PRIMARY KEY,
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
            id TEXT PRIMARY KEY,
            id_usuario TEXT,
            id_ponto_coleta TEXT,
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
            id_dispositivo TEXT,
            id_solicitacao TEXT,
            quantidade INTEGER,
            observacoes TEXT,
            FOREIGN KEY(id_dispositivo) REFERENCES dispositivo(id),
            FOREIGN KEY(id_solicitacao) REFERENCES solicitacao_descarte(id)
        )
        """)

        c.execute("""
        CREATE TABLE IF NOT EXISTS historico_rastreamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_solicitacao TEXT,
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

        data_cadastro = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        c.execute("""
        INSERT INTO usuario (id, nome, email, data_cadastro, ativo, tipo)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (cidadao.id, cidadao.nome, cidadao.email, data_cadastro, 1, "CIDADAO"))

        c.execute("INSERT INTO cidadao (id_usuario, cpf, solicitacoes_ativas, pontos) VALUES (?, ?, ?, ?)", (cidadao.id, cidadao.cpf, 0, 0))

        self.conn.commit()

    def salvar_empresa(self, empresa):
        c = self.conn.cursor()

        data_cadastro = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        c.execute("""
        INSERT INTO usuario (id, nome, email, data_cadastro, ativo, tipo)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (empresa.id, empresa.nome, empresa.email, data_cadastro, 1, 'EMPRESA'))

        c.execute("INSERT INTO empresa (id_usuario, cnpj, razao_social, limite_mensal, descartado_mes) VALUES (?, ?, ?, ?, ?)", (empresa.id, empresa.cnpj, empresa.razao_social, 0, 0))

        self.conn.commit()

    def salvar_administrador(self, administrador):
        c = self.conn.cursor()

        data_cadastro = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        c.execute("""
        INSERT INTO usuario (id, nome, email, data_cadastro, ativo, tipo)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (administrador.id, administrador.nome, administrador.email, data_cadastro, 1, "ADMINISTRADOR"))

        c.execute("INSERT INTO administrador (id_usuario, nivel) VALUES (?, ?)", (administrador.id, administrador.nivel))

        self.conn.commit()

    def salvar_notificacao(self, id_usuario, mensagem):
        c = self.conn.cursor()
        
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        c.execute("""
        INSERT INTO notificacao (id_usuario, timestamp, mensagem)
        VALUES (?, ?, ?)
        """, (id_usuario, timestamp, mensagem))
            
        self.conn.commit()

    def salvar_dispositivo(self, dispositivo):
        c = self.conn.cursor()

        c.execute("""
        INSERT INTO dispositivo (id, nome, peso_kg, marca, modelo)
        VALUES (?, ?, ?, ?)
        """, (dispositivo.id, dispositivo.nome, dispositivo.peso_kg, dispositivo.marca, dispositivo.modelo))

        self.conn.commit()

    def salvar_ponto(self, ponto_coleta):
        c = self.conn.cursor()

        c.execute("""
        INSERT INTO ponto_coleta (id, nome, endereco, latitude, longitude, ativo, capacidade_kg, ocupacao_atual_kg)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ponto_coleta.id, ponto_coleta.nome, ponto_coleta.endereco, ponto_coleta.latitude, ponto_coleta.longitude, 1, ponto_coleta.capacidade_kg, 0.0))

        self.conn.commit()

    def salvar_solicitacao(self, solicitacao_descarte):
        c = self.conn.cursor()

        data_criacao = datetime.now().strftime("%d/%m/%Y %H:%M")

        c.execute("""
        INSERT INTO solicitacao_descarte (id, id_usuario, id_ponto_coleta, estado, metodo_tratamento, data_criacao, data_agendamento) VALUES (?, ?, ?, ?, ?, ?, ?)" \
        """, (solicitacao_descarte.id, solicitacao_descarte.usuario.id, solicitacao_descarte.ponto_coleta.id, 'SOLICITADO', None, data_criacao, None))

        self.conn.commit()

    def salvar_itens_descarte(self, id_solicitacao, itens):
        c = self.conn.cursor()

        for item in itens:
            c.execute("""
            INSERT INTO item_descarte (id_dispositivo, id_solicitacao, quantidade, observacoes)
            VALUES (?, ?, ?, ?)
            """, (item.dispositivo.id, id_solicitacao, item.quantidade, item.observacoes))
        
        self.conn.commit()

    def salvar_historico_rastreamento(self, id_solicitacao, mensagem):
        c = self.conn.cursor()
        
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        c.execute("""
        INSERT INTO historico_rastreamento (id_solicitacao, timestamp, mensagem)
        VALUES (?, ?, ?)
        """, (id_solicitacao, timestamp, mensagem))
            
        self.conn.commit()