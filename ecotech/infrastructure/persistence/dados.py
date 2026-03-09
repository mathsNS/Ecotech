import sqlite3
from datetime import datetime
from ...domain.usuarios import Cidadao, Empresa, Administrador
from ...domain.dispositivos import Celular, Computador, Eletrodomestico
from ...domain.descarte import PontoColeta, ItemDescarte, SolicitacaoDescarte, RastreamentoEntrega
from...domain.tratamento import MetodoTratamento, Reciclagem, Reuso, DescarteControlado

class Dados:

    def __init__(self):
        self.conn = sqlite3.connect('ecotech.db')
        self.conn.row_factory = sqlite3.Row
        self.criar_tabelas()
        self.seed()

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
            modelo TEXT,
            tipo TEXT,
            impacto_ambiental REAL,
            valor_revenda REAL
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

        # Tabela de Métodos de Tratamento
        c.execute("""
        CREATE TABLE IF NOT EXISTS metodo_tratamento (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            custo_base_kg REAL,
            reducao_impacto_percentual REAL
        )
        """)

        # Tabelas de Descarte
        c.execute("""
        CREATE TABLE IF NOT EXISTS solicitacao_descarte (
            id TEXT PRIMARY KEY,
            id_usuario TEXT,
            id_ponto_coleta TEXT,
            id_metodo_tratamento INTEGER,
            estado TEXT,
            data_criacao TEXT,
            data_agendamento TEXT,
            FOREIGN KEY(id_usuario) REFERENCES usuario(id),
            FOREIGN KEY(id_ponto_coleta) REFERENCES ponto_coleta(id)
            FOREIGN KEY(id_metodo_tratamento) REFERENCES metodo_tratamento(id)
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

    def salvar_cidadao(self, cidadao: Cidadao):
        c = self.conn.cursor()

        data_cadastro = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        c.execute("""
        INSERT OR IGNORE INTO usuario (id, nome, email, data_cadastro, ativo, tipo)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (cidadao.id, cidadao.nome, cidadao.email, data_cadastro, 1, "Cidadao"))

        c.execute("INSERT OR IGNORE INTO cidadao (id_usuario, cpf, solicitacoes_ativas, pontos) VALUES (?, ?, ?, ?)", (cidadao.id, cidadao.cpf, 0, 0))

        self.conn.commit()

    def salvar_empresa(self, empresa: Empresa):
        c = self.conn.cursor()

        data_cadastro = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        c.execute("""
        INSERT OR IGNORE INTO usuario (id, nome, email, data_cadastro, ativo, tipo)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (empresa.id, empresa.nome, empresa.email, data_cadastro, 1, 'Empresa'))

        c.execute("INSERT OR IGNORE INTO empresa (id_usuario, cnpj, razao_social, limite_mensal, descartado_mes) VALUES (?, ?, ?, ?, ?)", (empresa.id, empresa.cnpj, empresa.razao_social, 0, 0))

        self.conn.commit()

    def salvar_administrador(self, administrador: Administrador):
        c = self.conn.cursor()

        data_cadastro = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        c.execute("""
        INSERT OR IGNORE INTO usuario (id, nome, email, data_cadastro, ativo, tipo)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (administrador.id, administrador.nome, administrador.email, data_cadastro, 1, "Administrador"))

        c.execute("INSERT OR IGNORE INTO administrador (id_usuario, nivel) VALUES (?, ?)", (administrador.id, administrador.nivel))

        self.conn.commit()

    def salvar_notificacao(self, id_usuario: str, mensagem: str):
        c = self.conn.cursor()
        
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        c.execute("""
        INSERT OR IGNORE INTO notificacao (id_usuario, timestamp, mensagem)
        VALUES (?, ?, ?)
        """, (id_usuario, timestamp, mensagem))
            
        self.conn.commit()

    def salvar_celular(self, dispositivo: Celular):
        c = self.conn.cursor()

        impacto_ambiental = dispositivo.peso_kg * 5.0
        valor_revenda = dispositivo.peso_kg * 10.0

        c.execute("""
        INSERT OR IGNORE INTO dispositivo (id, nome, peso_kg, marca, modelo, tipo, impacto_ambiental, valor_revenda)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (dispositivo.id, dispositivo.nome, dispositivo.peso_kg, dispositivo.marca, dispositivo.modelo, "Celular", impacto_ambiental, valor_revenda))

        self.conn.commit()

    def salvar_computador(self, dispositivo: Computador):
        c = self.conn.cursor()

        impacto_ambiental = dispositivo.peso_kg * 15.0
        valor_revenda = dispositivo.peso_kg * 25.0

        c.execute("""
        INSERT OR IGNORE INTO dispositivo (id, nome, peso_kg, marca, modelo, tipo, impacto_ambiental, valor_revenda)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (dispositivo.id, dispositivo.nome, dispositivo.peso_kg, dispositivo.marca, dispositivo.modelo, "Computador", impacto_ambiental, valor_revenda))

        self.conn.commit()

    def salvar_eletrodomestico(self, dispositivo: Eletrodomestico):
        c = self.conn.cursor()

        impacto_ambiental = dispositivo.peso_kg * 8.0
        valor_revenda = dispositivo.peso_kg * 15.0

        c.execute("""
        INSERT OR IGNORE INTO dispositivo (id, nome, peso_kg, marca, modelo, tipo, impacto_ambiental, valor_revenda)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (dispositivo.id, dispositivo.nome, dispositivo.peso_kg, dispositivo.marca, dispositivo.modelo, "Eletrodomestico", impacto_ambiental, valor_revenda))

        self.conn.commit()

    def salvar_ponto(self, ponto_coleta: PontoColeta):
        c = self.conn.cursor()

        c.execute("""
        INSERT OR IGNORE INTO ponto_coleta (id, nome, endereco, latitude, longitude, ativo, capacidade_kg, ocupacao_atual_kg)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ponto_coleta.id, ponto_coleta.nome, ponto_coleta.endereco, ponto_coleta.latitude, ponto_coleta.longitude, 1, ponto_coleta.capacidade_kg, 0.0))

        self.conn.commit()

    def salvar_metodo_tratamento(self, nome: str, metodo: MetodoTratamento):
        c = self.conn.cursor()

        c.execute("""
        INSERT OR IGNORE INTO metodo_tratamento (nome, custo_base_kg,reducao_impacto_percentual)
        VALUES (?, ?, ?)
        """, (nome, metodo.custo_base_por_kg, metodo.reducao_impacto_percentual))

        self.conn.commit()

    def salvar_solicitacao(self, solicitacao_descarte: SolicitacaoDescarte):
        c = self.conn.cursor()

        data_criacao = datetime.now().strftime("%d/%m/%Y %H:%M")

        c.execute("""
        INSERT OR IGNORE INTO solicitacao_descarte (id, id_usuario, id_ponto_coleta, id_metodo_tratamento, estado, data_criacao, data_agendamento) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (solicitacao_descarte.id, solicitacao_descarte.usuario.id, solicitacao_descarte.ponto_coleta.id, None, 'Solicitado', data_criacao, None))

        self.conn.commit()

    def salvar_itens_descarte(self, id_solicitacao: str, item: ItemDescarte):
        c = self.conn.cursor()

        c.execute("""
        INSERT OR IGNORE INTO item_descarte (id_dispositivo, id_solicitacao, quantidade, observacoes)
        VALUES (?, ?, ?, ?)
        """, (item.dispositivo.id, id_solicitacao, item.quantidade, item.observacoes))
        
        self.conn.commit()

    def salvar_historico_rastreamento(self, id_solicitacao: str, mensagem: str):
        c = self.conn.cursor()
        
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        c.execute("""
        INSERT OR IGNORE INTO historico_rastreamento (id_solicitacao, timestamp, mensagem)
        VALUES (?, ?, ?)
        """, (id_solicitacao, timestamp, mensagem))
            
        self.conn.commit()

    # -------------------
    # SEED
    # -------------------

    def seed(self):
        cidadao = Cidadao("USR-CID-001", "João Silva", "joaosilva@email.com", "12345678901")
        self.salvar_cidadao(cidadao)

        empresa = Empresa("USR-EMP-001", "EcoSoluções LTDA", "contato@ecosolucoes.com", "98765432000100", "EcoSoluções Reciclagem Industrial")
        self.salvar_empresa(empresa)

        admin = Administrador("USR-ADM-001", "Admin Master", "admin@ecotech.com", 3)
        self.salvar_administrador(admin)

        dispositivo = Celular("DISP-001", "Smartphone X", 0.2, "Tech", "Pro")
        self.salvar_celular(dispositivo)

        ponto_coleta = PontoColeta("PNT-001"," EcoPonto Sul", "Rua B, 500", -23.5, -46.6, 500.0)
        self.salvar_ponto(ponto_coleta)

        solicitacao = SolicitacaoDescarte("SOL-001", cidadao, ponto_coleta)
        self.salvar_solicitacao(solicitacao)