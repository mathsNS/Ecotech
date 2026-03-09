import sqlite3
from datetime import datetime
from ...domain.usuarios import Cidadao, Empresa, Administrador
from ...domain.dispositivos import Celular
from ...domain.descarte import PontoColeta, ItemDescarte, SolicitacaoDescarte, RastreamentoEntrega

class Dados:

    def __init__(self):
        self.conn = sqlite3.connect('ecotech.db', check_same_thread=False)
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

        # tabela de entregas/transacoes
        c.execute("""
        CREATE TABLE IF NOT EXISTS entrega (
            id TEXT PRIMARY KEY,
            id_usuario TEXT,
            valor REAL,
            empresa TEXT,
            data TEXT,
            hora TEXT,
            status TEXT,
            FOREIGN KEY(id_usuario) REFERENCES usuario(id)
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
        INSERT OR IGNORE INTO usuario (id, nome, email, data_cadastro, ativo, tipo)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (cidadao.id, cidadao.nome, cidadao.email, data_cadastro, 1, "cidadao"))

        c.execute("INSERT OR IGNORE INTO cidadao (id_usuario, cpf, solicitacoes_ativas, pontos) VALUES (?, ?, ?, ?)", (cidadao.id, cidadao.cpf, 0, 0))

        self.conn.commit()

    def salvar_empresa(self, empresa):
        c = self.conn.cursor()

        data_cadastro = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        c.execute("""
        INSERT OR IGNORE INTO usuario (id, nome, email, data_cadastro, ativo, tipo)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (empresa.id, empresa.nome, empresa.email, data_cadastro, 1, 'empresa'))

        c.execute("INSERT OR IGNORE INTO empresa (id_usuario, cnpj, razao_social, limite_mensal, descartado_mes) VALUES (?, ?, ?, ?, ?)", (empresa.id, empresa.cnpj, empresa.razao_social, 0, 0))

        self.conn.commit()

    def salvar_administrador(self, administrador):
        c = self.conn.cursor()

        data_cadastro = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

        c.execute("""
        INSERT OR IGNORE INTO usuario (id, nome, email, data_cadastro, ativo, tipo)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (administrador.id, administrador.nome, administrador.email, data_cadastro, 1, "administrador"))

        c.execute("INSERT OR IGNORE INTO administrador (id_usuario, nivel) VALUES (?, ?)", (administrador.id, administrador.nivel))

        self.conn.commit()

    def salvar_notificacao(self, id_usuario, mensagem):
        c = self.conn.cursor()
        
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        c.execute("""
        INSERT OR IGNORE INTO notificacao (id_usuario, timestamp, mensagem)
        VALUES (?, ?, ?)
        """, (id_usuario, timestamp, mensagem))
            
        self.conn.commit()

    def salvar_dispositivo(self, dispositivo):
        c = self.conn.cursor()

        c.execute("""
        INSERT OR IGNORE INTO dispositivo (id, nome, peso_kg, marca, modelo)
        VALUES (?, ?, ?, ?, ?)
        """, (dispositivo.id, dispositivo.nome, dispositivo.peso_kg, dispositivo.marca, dispositivo.modelo))

        self.conn.commit()

    def salvar_ponto(self, ponto_coleta):
        c = self.conn.cursor()

        c.execute("""
        INSERT OR IGNORE INTO ponto_coleta (id, nome, endereco, latitude, longitude, ativo, capacidade_kg, ocupacao_atual_kg)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (ponto_coleta.id, ponto_coleta.nome, ponto_coleta.endereco, ponto_coleta.latitude, ponto_coleta.longitude, 1, ponto_coleta.capacidade_kg, 0.0))

        self.conn.commit()

    def salvar_solicitacao(self, solicitacao_descarte):
        c = self.conn.cursor()

        data_criacao = datetime.now().strftime("%d/%m/%Y %H:%M")

        c.execute("""
        INSERT OR IGNORE INTO solicitacao_descarte (id, id_usuario, id_ponto_coleta, estado, metodo_tratamento, data_criacao, data_agendamento) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (solicitacao_descarte.id, solicitacao_descarte.usuario.id, solicitacao_descarte.ponto_coleta.id, 'SOLICITADO', None, data_criacao, None))

        self.conn.commit()

    def salvar_itens_descarte(self, id_solicitacao, item):
        c = self.conn.cursor()

        c.execute("""
        INSERT OR IGNORE INTO item_descarte (id_dispositivo, id_solicitacao, quantidade, observacoes)
        VALUES (?, ?, ?, ?)
        """, (item.dispositivo.id, id_solicitacao, item.quantidade, item.observacoes))
        
        self.conn.commit()

    def salvar_historico_rastreamento(self, id_solicitacao, mensagem):
        c = self.conn.cursor()
        
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        c.execute("""
        INSERT OR IGNORE INTO historico_rastreamento (id_solicitacao, timestamp, mensagem)
        VALUES (?, ?, ?)
        """, (id_solicitacao, timestamp, mensagem))
            
        self.conn.commit()

    def salvar_entrega(self, id_entrega, id_usuario, valor, empresa, data, hora, status):
        """Salva uma entrega/transação no histórico."""
        c = self.conn.cursor()
        
        c.execute("""
        INSERT OR REPLACE INTO entrega (id, id_usuario, valor, empresa, data, hora, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (id_entrega, id_usuario, valor, empresa, data, hora, status))
        
        self.conn.commit()

    # -------------------
    # BUSCAR
    # -------------------

    def buscar_usuario(self, id_usuario):
        """Busca um usuário por ID."""
        c = self.conn.cursor()
        c.execute("SELECT * FROM usuario WHERE id = ?", (id_usuario,))
        return c.fetchone()

    def buscar_todos_usuarios(self):
        """Retorna todos os usuários."""
        c = self.conn.cursor()
        c.execute("SELECT * FROM usuario")
        return c.fetchall()

    def buscar_cidadao(self, id_usuario):
        """Busca dados específicos de cidadão."""
        c = self.conn.cursor()
        c.execute("""
            SELECT u.*, c.cpf, c.solicitacoes_ativas, c.pontos
            FROM usuario u
            JOIN cidadao c ON u.id = c.id_usuario
            WHERE u.id = ?
        """, (id_usuario,))
        return c.fetchone()

    def buscar_empresa(self, id_usuario):
        """Busca dados específicos de empresa."""
        c = self.conn.cursor()
        c.execute("""
            SELECT u.*, e.cnpj, e.razao_social, e.limite_mensal, e.descartado_mes
            FROM usuario u
            JOIN empresa e ON u.id = e.id_usuario
            WHERE u.id = ?
        """, (id_usuario,))
        return c.fetchone()

    def buscar_dispositivo(self, id_dispositivo):
        """Busca um dispositivo por ID."""
        c = self.conn.cursor()
        c.execute("SELECT * FROM dispositivo WHERE id = ?", (id_dispositivo,))
        return c.fetchone()

    def buscar_ponto_coleta(self, id_ponto):
        """Busca um ponto de coleta por ID."""
        c = self.conn.cursor()
        c.execute("SELECT * FROM ponto_coleta WHERE id = ?", (id_ponto,))
        return c.fetchone()

    def buscar_todos_pontos_coleta(self):
        """Retorna todos os pontos de coleta ativos."""
        c = self.conn.cursor()
        c.execute("SELECT * FROM ponto_coleta WHERE ativo = 1")
        return c.fetchall()

    def buscar_solicitacao(self, id_solicitacao):
        """Busca uma solicitação por ID."""
        c = self.conn.cursor()
        c.execute("SELECT * FROM solicitacao_descarte WHERE id = ?", (id_solicitacao,))
        return c.fetchone()

    def buscar_todas_solicitacoes(self):
        """Retorna todas as solicitações."""
        c = self.conn.cursor()
        c.execute("SELECT * FROM solicitacao_descarte")
        return c.fetchall()

    def buscar_solicitacoes_usuario(self, id_usuario):
        """Retorna todas as solicitações de um usuário específico."""
        c = self.conn.cursor()
        c.execute("SELECT * FROM solicitacao_descarte WHERE id_usuario = ?", (id_usuario,))
        return c.fetchall()

    def buscar_itens_solicitacao(self, id_solicitacao):
        """Retorna todos os itens de uma solicitação."""
        c = self.conn.cursor()
        c.execute("""
            SELECT i.*, d.nome, d.peso_kg, d.marca, d.modelo
            FROM item_descarte i
            JOIN dispositivo d ON i.id_dispositivo = d.id
            WHERE i.id_solicitacao = ?
        """, (id_solicitacao,))
        return c.fetchall()

    def buscar_entregas_usuario(self, id_usuario):
        """Retorna todas as entregas de um usuário."""
        c = self.conn.cursor()
        c.execute("""
            SELECT * FROM entrega 
            WHERE id_usuario = ? 
            ORDER BY data DESC, hora DESC
        """, (id_usuario,))
        return c.fetchall()

    def buscar_notificacoes_usuario(self, id_usuario):
        """Retorna todas as notificações de um usuário."""
        c = self.conn.cursor()
        c.execute("""
            SELECT * FROM notificacao 
            WHERE id_usuario = ? 
            ORDER BY timestamp DESC
        """, (id_usuario,))
        return c.fetchall()

    def contar_usuarios(self):
        """Conta total de usuários no sistema."""
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) as total FROM usuario")
        return c.fetchone()['total']

    def contar_solicitacoes(self):
        """Conta total de solicitações no sistema."""
        c = self.conn.cursor()
        c.execute("SELECT COUNT(*) as total FROM solicitacao_descarte")
        return c.fetchone()['total']

    # -------------------
    # SEED
    # -------------------

    def seed(self):
        """Inicializa dados básicos apenas se o banco estiver vazio."""
        # verifica se ja existem usuarios no banco
        if self.contar_usuarios() > 0:
            return  # ja tem dados, nao precisa fazer seed
        
        # cria dados iniciais apenas se o banco estiver vazio
        cidadao = Cidadao("USR-CID-001", "João Silva", "joaosilva@email.com", "12345678901")
        self.salvar_cidadao(cidadao)

        empresa = Empresa("USR-EMP-001", "EcoSoluções LTDA", "contato@ecosolucoes.com", "98765432000100", "EcoSoluções Reciclagem Industrial")
        self.salvar_empresa(empresa)

        admin = Administrador("USR-ADM-001", "Admin Master", "admin@ecotech.com", 3)
        self.salvar_administrador(admin)

        dispositivo = Celular("DISP-001", "Smartphone X", 0.2, "Tech", "Pro")
        self.salvar_dispositivo(dispositivo)

        ponto_coleta = PontoColeta("PNT-001"," EcoPonto Sul", "Rua B, 500", -23.5, -46.6, 500.0)
        self.salvar_ponto(ponto_coleta)

        solicitacao = SolicitacaoDescarte("SOL-001", cidadao, ponto_coleta)
        self.salvar_solicitacao(solicitacao)
        
        item = ItemDescarte(dispositivo, 1, "Tela trincada")
        self.salvar_itens_descarte('SOL-001', item)