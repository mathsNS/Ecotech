import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash
from ...domain.usuarios import Cidadao, Empresa, Administrador
from ...domain.dispositivos import Celular
from ...domain.descarte import PontoColeta, ItemDescarte, SolicitacaoDescarte, RastreamentoEntrega
from ...domain.repositorio import RepositorioBase

class Dados(RepositorioBase):
    """Implementação concreta de RepositorioBase usando SQLite.

    Gerencia a persistência de dados do sistema em banco de dados SQLite,
    implementando todos os métodos definidos na interface abstrata.
    """

    def __init__(self):
        self.conn = sqlite3.connect('ecotech.db', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
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
            tipo TEXT,
            password_hash TEXT
        )
        """)

        # Migração incremental: adiciona password_hash se a tabela já existia sem ela
        try:
            c.execute("ALTER TABLE usuario ADD COLUMN password_hash TEXT")
        except Exception:
            pass  # coluna já existe

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
            tipo TEXT DEFAULT 'celular'
        )
        """)
        # migracao: adiciona coluna tipo se nao existir
        try:
            c.execute("ALTER TABLE dispositivo ADD COLUMN tipo TEXT DEFAULT 'celular'")
            self.conn.commit()
        except Exception:
            pass  # coluna ja existe

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

    def salvar_cidadao(self, cidadao, password_hash: str = ""):
        data_cadastro = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        with self.conn:
            self.conn.execute("""
            INSERT OR IGNORE INTO usuario (id, nome, email, data_cadastro, ativo, tipo, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (cidadao.id, cidadao.nome, cidadao.email, data_cadastro, 1, "cidadao", password_hash))
            self.conn.execute(
                "INSERT OR IGNORE INTO cidadao (id_usuario, cpf, solicitacoes_ativas, pontos) VALUES (?, ?, ?, ?)",
                (cidadao.id, cidadao.cpf, 0, 0)
            )

    def salvar_empresa(self, empresa, password_hash: str = ""):
        data_cadastro = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        with self.conn:
            self.conn.execute("""
            INSERT OR IGNORE INTO usuario (id, nome, email, data_cadastro, ativo, tipo, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (empresa.id, empresa.nome, empresa.email, data_cadastro, 1, 'empresa', password_hash))
            self.conn.execute(
                "INSERT OR IGNORE INTO empresa (id_usuario, cnpj, razao_social, limite_mensal, descartado_mes) VALUES (?, ?, ?, ?, ?)",
                (empresa.id, empresa.cnpj, empresa.razao_social, empresa.limite_mensal, empresa.descartado_mes)
            )

    def salvar_administrador(self, administrador, password_hash: str = ""):
        data_cadastro = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        with self.conn:
            self.conn.execute("""
            INSERT OR IGNORE INTO usuario (id, nome, email, data_cadastro, ativo, tipo, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (administrador.id, administrador.nome, administrador.email, data_cadastro, 1, "administrador", password_hash))
            self.conn.execute(
                "INSERT OR IGNORE INTO administrador (id_usuario, nivel) VALUES (?, ?)",
                (administrador.id, administrador.nivel)
            )
    def salvar_notificacao(self, id_usuario, mensagem):
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        with self.conn:
            self.conn.execute("""
            INSERT INTO notificacao (id_usuario, timestamp, mensagem)
            VALUES (?, ?, ?)
            """, (id_usuario, timestamp, mensagem))

    def salvar_dispositivo(self, dispositivo):
        with self.conn:
            self.conn.execute("""
            INSERT OR IGNORE INTO dispositivo (id, nome, peso_kg, marca, modelo, tipo)
            VALUES (?, ?, ?, ?, ?, ?)
            """, (dispositivo.id, dispositivo.nome, dispositivo.peso_kg, dispositivo.marca, dispositivo.modelo, dispositivo.obter_tipo().lower()))

    def salvar_ponto(self, ponto_coleta):
        with self.conn:
            self.conn.execute("""
            INSERT OR IGNORE INTO ponto_coleta (id, nome, endereco, latitude, longitude, ativo, capacidade_kg, ocupacao_atual_kg)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (ponto_coleta.id, ponto_coleta.nome, ponto_coleta.endereco,
                  ponto_coleta.latitude, ponto_coleta.longitude, 1,
                  ponto_coleta.capacidade_kg, ponto_coleta.ocupacao_atual_kg))

    def salvar_solicitacao(self, solicitacao_descarte):
        data_criacao = datetime.now().strftime("%d/%m/%Y %H:%M")
        estado_str = solicitacao_descarte.estado.obter_nome().upper().replace(' ', '_')
        metodo_str = (
            solicitacao_descarte.metodo_tratamento.obter_nome()
            if solicitacao_descarte.metodo_tratamento else None
        )
        with self.conn:
            self.conn.execute("""
            INSERT OR IGNORE INTO solicitacao_descarte
                (id, id_usuario, id_ponto_coleta, estado, metodo_tratamento, data_criacao, data_agendamento)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                solicitacao_descarte.id,
                solicitacao_descarte.usuario.id,
                solicitacao_descarte.ponto_coleta.id if solicitacao_descarte.ponto_coleta else None,
                estado_str,
                metodo_str,
                data_criacao,
                None
            ))

    def salvar_itens_descarte(self, id_solicitacao, item):
        with self.conn:
            self.conn.execute("""
            INSERT OR IGNORE INTO item_descarte (id_dispositivo, id_solicitacao, quantidade, observacoes)
            VALUES (?, ?, ?, ?)
            """, (item.dispositivo.id, id_solicitacao, item.quantidade, item.observacoes))

    def salvar_historico_rastreamento(self, id_solicitacao, mensagem):
        timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        with self.conn:
            self.conn.execute("""
            INSERT INTO historico_rastreamento (id_solicitacao, timestamp, mensagem)
            VALUES (?, ?, ?)
            """, (id_solicitacao, timestamp, mensagem))

    def salvar_entrega(self, id_entrega, id_usuario, valor, empresa, data, hora, status):
        """Salva uma entrega/transação no histórico."""
        with self.conn:
            self.conn.execute("""
            INSERT OR REPLACE INTO entrega (id, id_usuario, valor, empresa, data, hora, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (id_entrega, id_usuario, valor, empresa, data, hora, status))

    # -------------------
    # ATUALIZAR
    # -------------------

    def atualizar_solicitacao(self, id_solicitacao: str, estado: str,
                               metodo_tratamento=None) -> None:
        """Atualiza estado e opcionalmente o método de tratamento de uma solicitação."""
        with self.conn:
            self.conn.execute("""
            UPDATE solicitacao_descarte
               SET estado = ?,
                   metodo_tratamento = COALESCE(?, metodo_tratamento)
             WHERE id = ?
            """, (estado, metodo_tratamento, id_solicitacao))

    def atualizar_ocupacao_ponto(self, id_ponto: str, ocupacao_atual_kg: float) -> None:
        """Atualiza a ocupação atual de um ponto de coleta."""
        with self.conn:
            self.conn.execute(
                "UPDATE ponto_coleta SET ocupacao_atual_kg = ? WHERE id = ?",
                (ocupacao_atual_kg, id_ponto)
            )

    # -------------------
    # DESATIVAR (soft-delete)
    # -------------------

    def desativar_usuario(self, id_usuario: str) -> None:
        """Desativa um usuário (soft-delete: mantém dados, marca ativo = 0)."""
        with self.conn:
            self.conn.execute(
                "UPDATE usuario SET ativo = 0 WHERE id = ?",
                (id_usuario,)
            )

    # -------------------
    # BUSCAR
    # -------------------

    def buscar_usuario(self, id_usuario):
        """Busca um usuário por ID."""
        c = self.conn.cursor()
        c.execute("SELECT * FROM usuario WHERE id = ?", (id_usuario,))
        return c.fetchone()

    def buscar_usuario_por_cpf(self, cpf: str):
        """
        Busca um cidadão pelo CPF.

        Retorna a linha completa da tabela usuario com todos os campos,
        incluindo password_hash, para uso na autenticação.
        """
        c = self.conn.cursor()
        c.execute("""
            SELECT u.*
            FROM usuario u
            JOIN cidadao ci ON u.id = ci.id_usuario
            WHERE ci.cpf = ? AND u.ativo = 1
        """, (cpf,))
        return c.fetchone()

    def buscar_usuario_por_cnpj(self, cnpj: str):
        """
        Busca uma empresa pelo CNPJ.

        Retorna a linha completa da tabela usuario com todos os campos,
        incluindo password_hash, para uso na autenticação.
        """
        c = self.conn.cursor()
        c.execute("""
            SELECT u.*
            FROM usuario u
            JOIN empresa e ON u.id = e.id_usuario
            WHERE e.cnpj = ? AND u.ativo = 1
        """, (cnpj,))
        return c.fetchone()

    def buscar_usuario_por_email(self, email: str):
        """
        Busca um usuário pelo email.

        Utilizado no login de administradores, que não possuem CPF nem CNPJ.
        Retorna a linha completa da tabela usuario incluindo password_hash.
        """
        c = self.conn.cursor()
        c.execute("SELECT * FROM usuario WHERE email = ? AND ativo = 1", (email,))
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
            SELECT i.*, d.nome, d.peso_kg, d.marca, d.modelo, d.tipo
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
        """Mantido por compatibilidade. Seeding é gerenciado por _inicializar_dados_exemplo em web.py."""
        pass