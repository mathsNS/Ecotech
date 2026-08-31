import sqlite3
from datetime import datetime
from werkzeug.security import generate_password_hash
from ...domain.usuarios import Cidadao, Empresa, Administrador
from ...domain.dispositivos import Celular
from ...domain.descarte import PontoColeta, ItemDescarte, SolicitacaoDescarte, RastreamentoEntrega
from ...domain.repositorio import RepositorioBase
from ...domain.logistica import BaseOperacional
from .migrations import executar_migrations, versao_atual

class Dados(RepositorioBase):
    """Implementação SQLite do RepositorioBase."""

    def __init__(self):
        self.conn = sqlite3.connect('ecotech.db', check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.criar_tabelas()

    def _coluna_existe(self, tabela: str, coluna: str) -> bool:
        return any(
            row['name'] == coluna
            for row in self.conn.execute(f"PRAGMA table_info({tabela})")
        )

    def _adicionar_coluna_se_ausente(
        self, tabela: str, coluna: str, definicao: str
    ) -> None:
        """Aplica uma evolução legada de coluna sem ocultar erros do SQLite."""
        if not self._coluna_existe(tabela, coluna):
            self.conn.execute(
                f"ALTER TABLE {tabela} ADD COLUMN {coluna} {definicao}"
            )

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

        self._adicionar_coluna_se_ausente('usuario', 'password_hash', 'TEXT')

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
        self._adicionar_coluna_se_ausente(
            'dispositivo', 'tipo', "TEXT DEFAULT 'celular'"
        )

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
        self._adicionar_coluna_se_ausente('ponto_coleta', 'id_empresa', 'TEXT')
        self._adicionar_coluna_se_ausente(
            'empresa', 'plano', "TEXT DEFAULT 'free'"
        )
        self._adicionar_coluna_se_ausente(
            'empresa', 'saldo', 'REAL DEFAULT 0.0'
        )

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
        for coluna, definicao in (
            ('tipo_coleta', "TEXT DEFAULT 'domiciliar'"),
            ('endereco_coleta', 'TEXT'),
            ('nome_contato', 'TEXT'),
            ('confirmado_cidadao', 'INTEGER DEFAULT 0'),
            ('confirmado_empresa', 'INTEGER DEFAULT 0'),
            ('estado_produto', 'TEXT'),
            ('valor_proposto', 'REAL'),
            ('justificativa_valor', 'TEXT'),
            ('status_override', "TEXT DEFAULT 'nenhum'"),
        ):
            self._adicionar_coluna_se_ausente(
                'solicitacao_descarte', coluna, definicao
            )

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
            id_solicitacao TEXT,
            id_usuario TEXT,
            valor REAL,
            empresa TEXT,
            data TEXT,
            hora TEXT,
            status TEXT,
            FOREIGN KEY(id_usuario) REFERENCES usuario(id),
            FOREIGN KEY(id_solicitacao) REFERENCES solicitacao_descarte(id)
        )
        """)

        # Tabela de Saques
        c.execute("""
        CREATE TABLE IF NOT EXISTS saque (
            id TEXT PRIMARY KEY,
            id_usuario TEXT,
            valor REAL,
            metodo TEXT,
            data TEXT,
            hora TEXT,
            status TEXT,
            FOREIGN KEY(id_usuario) REFERENCES usuario(id)
        )
        """)

        self._adicionar_coluna_se_ausente(
            'dispositivo', 'subcategoria', "TEXT DEFAULT 'smartphone_medio'"
        )

        # tabela de precificacao por subcategoria
        c.execute("""
        CREATE TABLE IF NOT EXISTS tabela_precos (
            subcategoria TEXT PRIMARY KEY,
            categoria TEXT,
            valor_minimo_sucata REAL,
            valor_base_funcionando REAL
        )
        """)
        precos_padrao = [
            ('smartphone_basico',    'celular',          8.00,   300.00),
            ('smartphone_medio',     'celular',         10.00,   600.00),
            ('smartphone_premium',   'celular',         15.00,  1500.00),
            ('iphone',               'celular',         20.00,  2500.00),
            ('notebook_basico',      'computador',      30.00,   800.00),
            ('notebook_gamer',       'computador',      50.00,  3000.00),
            ('desktop',              'computador',      40.00,   700.00),
            ('geladeira',            'eletrodomestico', 130.00,  900.00),
            ('lavadora',             'eletrodomestico',  80.00,  700.00),
            ('ar_condicionado',      'eletrodomestico', 120.00, 1000.00),
            ('micro_ondas',          'eletrodomestico',  15.00,  200.00),
            ('tv',                   'eletrodomestico',  15.00,  500.00),
        ]
        c.executemany(
            "INSERT OR IGNORE INTO tabela_precos (subcategoria, categoria, valor_minimo_sucata, valor_base_funcionando) VALUES (?, ?, ?, ?)",
            precos_padrao
        )

        # Índices para otimizar buscas frequentes
        c.execute("CREATE INDEX IF NOT EXISTS idx_solicitacao_usuario ON solicitacao_descarte(id_usuario)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_item_solicitacao ON item_descarte(id_solicitacao)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_notificacao_usuario ON notificacao(id_usuario)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_entrega_usuario ON entrega(id_usuario)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_rastreamento_solicitacao ON historico_rastreamento(id_solicitacao)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_saque_usuario ON saque(id_usuario)")

        # tabela de receita da EcoTech (comissao por solicitacao)
        c.execute("""
        CREATE TABLE IF NOT EXISTS receita_ecotech (
            id TEXT PRIMARY KEY,
            id_solicitacao TEXT,
            valor REAL,
            data TEXT,
            FOREIGN KEY(id_solicitacao) REFERENCES solicitacao_descarte(id)
        )
        """)

        self.conn.commit()
        executar_migrations(self.conn)

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
            INSERT OR IGNORE INTO dispositivo (id, nome, peso_kg, marca, modelo, tipo, subcategoria)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (dispositivo.id, dispositivo.nome, dispositivo.peso_kg, dispositivo.marca, dispositivo.modelo, dispositivo.obter_tipo().lower(), dispositivo.subcategoria))

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

    def salvar_saque(self, id_saque: str, id_usuario: str, valor: float,
                     metodo: str, data: str, hora: str, status: str) -> None:
        """Registra uma solicitação de saque."""
        with self.conn:
            self.conn.execute("""
            INSERT OR IGNORE INTO saque (id, id_usuario, valor, metodo, data, hora, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (id_saque, id_usuario, valor, metodo, data, hora, status))

    def buscar_saques_usuario(self, id_usuario: str):
        """Retorna todos os saques de um usuário."""
        c = self.conn.cursor()
        c.execute("SELECT * FROM saque WHERE id_usuario = ? ORDER BY data DESC", (id_usuario,))
        return c.fetchall()

    def buscar_total_sacado_usuario(self, id_usuario: str) -> float:
        """Retorna o total já sacado (status pendente ou finalizado) por um usuário."""
        c = self.conn.cursor()
        c.execute("""
            SELECT COALESCE(SUM(valor), 0.0) as total
            FROM saque
            WHERE id_usuario = ? AND status IN ('pendente', 'finalizado')
        """, (id_usuario,))
        row = c.fetchone()
        return float(row['total']) if row else 0.0

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

    def atualizar_localizacao_coleta(
        self, id_solicitacao: str, latitude: float, longitude: float,
        origem: str
    ) -> None:
        with self.conn:
            cursor = self.conn.execute("""
                UPDATE solicitacao_descarte
                SET latitude_coleta = ?, longitude_coleta = ?,
                    localizacao_obtida_em = ?, origem_localizacao = ?
                WHERE id = ? AND tipo_coleta = 'domiciliar'
            """, (
                latitude, longitude, datetime.now().isoformat(timespec='seconds'),
                origem, id_solicitacao,
            ))
        if cursor.rowcount != 1:
            raise ValueError("solicitação domiciliar não encontrada")

    def atualizar_ocupacao_ponto(self, id_ponto: str, ocupacao_atual_kg: float) -> None:
        """Atualiza a ocupação atual de um ponto de coleta."""
        with self.conn:
            self.conn.execute(
                "UPDATE ponto_coleta SET ocupacao_atual_kg = ? WHERE id = ?",
                (ocupacao_atual_kg, id_ponto)
            )

    def salvar_base_operacional(self, base: BaseOperacional) -> None:
        agora = datetime.now().isoformat(timespec='seconds')
        with self.conn:
            self.conn.execute("""
                INSERT INTO base_operacional (
                    id, empresa_id, ponto_coleta_id, nome, endereco,
                    latitude, longitude, raio_atendimento_km,
                    capacidade_kg, ocupacao_atual_kg,
                    realiza_coleta_domiciliar, ativa, criada_em, atualizada_em
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                base.id, base.empresa_id, base.ponto_coleta_id,
                base.nome, base.endereco, base.latitude, base.longitude,
                base.raio_atendimento_km, base.capacidade_kg,
                base.ocupacao_atual_kg,
                int(base.realiza_coleta_domiciliar), int(base.ativa),
                agora, agora,
            ))

    def buscar_base_operacional(self, id_base: str):
        return self.conn.execute(
            "SELECT * FROM base_operacional WHERE id = ?", (id_base,)
        ).fetchone()

    def buscar_bases_empresa(self, id_empresa: str):
        return self.conn.execute("""
            SELECT * FROM base_operacional
            WHERE empresa_id = ? ORDER BY ativa DESC, nome
        """, (id_empresa,)).fetchall()

    def atualizar_base_operacional(self, base: BaseOperacional) -> None:
        with self.conn:
            cursor = self.conn.execute("""
                UPDATE base_operacional
                SET nome = ?, endereco = ?, latitude = ?, longitude = ?,
                    raio_atendimento_km = ?, capacidade_kg = ?,
                    ocupacao_atual_kg = ?, realiza_coleta_domiciliar = ?,
                    atualizada_em = ?
                WHERE id = ? AND empresa_id = ?
            """, (
                base.nome, base.endereco, base.latitude, base.longitude,
                base.raio_atendimento_km, base.capacidade_kg,
                base.ocupacao_atual_kg, int(base.realiza_coleta_domiciliar),
                datetime.now().isoformat(timespec='seconds'),
                base.id, base.empresa_id,
            ))
        if cursor.rowcount != 1:
            raise ValueError("base operacional não encontrada para esta empresa")

    def definir_atividade_base(
        self, id_base: str, id_empresa: str, ativa: bool
    ) -> None:
        with self.conn:
            cursor = self.conn.execute("""
                UPDATE base_operacional SET ativa = ?, atualizada_em = ?
                WHERE id = ? AND empresa_id = ?
            """, (
                int(ativa), datetime.now().isoformat(timespec='seconds'),
                id_base, id_empresa,
            ))
        if cursor.rowcount != 1:
            raise ValueError("base operacional não encontrada para esta empresa")

    # -------------------
    # DESATIVAR (soft-delete)
    # -------------------

    def desativar_usuario(self, id_usuario: str) -> None:
        """Marca o usuário como inativo sem remover o registro."""
        with self.conn:
            self.conn.execute(
                "UPDATE usuario SET ativo = 0 WHERE id = ?",
                (id_usuario,)
            )

    def atualizar_pontos_cidadao(self, id_usuario: str, pontos_a_adicionar: int) -> None:
        """Incrementa os pontos do cidadão no banco."""
        with self.conn:
            self.conn.execute(
                "UPDATE cidadao SET pontos = pontos + ? WHERE id_usuario = ?",
                (pontos_a_adicionar, id_usuario)
            )

    def buscar_plano_empresa(self, id_usuario: str) -> str:
        """Retorna o plano atual da empresa ('free', 'professional', 'enterprise')."""
        c = self.conn.cursor()
        c.execute("SELECT plano FROM empresa WHERE id_usuario = ?", (id_usuario,))
        row = c.fetchone()
        return row['plano'] if row and row['plano'] else 'free'

    def atualizar_plano_empresa(self, id_usuario: str, plano: str) -> None:
        """Atualiza o plano da empresa."""
        planos_validos = {'free', 'professional', 'enterprise'}
        if plano not in planos_validos:
            raise ValueError(f"Plano inválido: {plano}")
        with self.conn:
            self.conn.execute(
                "UPDATE empresa SET plano = ? WHERE id_usuario = ?",
                (plano, id_usuario)
            )

    def atualizar_usuario(self, id_usuario: str, nome: str, email: str, password_hash: str = None) -> None:
        """Atualiza nome e email do usuário. Se password_hash fornecido, atualiza também a senha."""
        with self.conn:
            if password_hash:
                self.conn.execute(
                    "UPDATE usuario SET nome = ?, email = ?, password_hash = ? WHERE id = ?",
                    (nome, email, password_hash, id_usuario)
                )
            else:
                self.conn.execute(
                    "UPDATE usuario SET nome = ?, email = ? WHERE id = ?",
                    (nome, email, id_usuario)
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
        """Busca por CPF ativo, retorna row com password_hash."""
        c = self.conn.cursor()
        c.execute("""
            SELECT u.*
            FROM usuario u
            JOIN cidadao ci ON u.id = ci.id_usuario
            WHERE ci.cpf = ? AND u.ativo = 1
        """, (cpf,))
        return c.fetchone()

    def buscar_usuario_por_cnpj(self, cnpj: str):
        """Busca por CNPJ ativo, retorna row com password_hash."""
        c = self.conn.cursor()
        c.execute("""
            SELECT u.*
            FROM usuario u
            JOIN empresa e ON u.id = e.id_usuario
            WHERE e.cnpj = ? AND u.ativo = 1
        """, (cnpj,))
        return c.fetchone()

    def buscar_usuario_por_email(self, email: str):
        """Busca por email ativo (usado no login de admin)."""
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
            SELECT i.*, d.nome, d.peso_kg, d.marca, d.modelo, d.tipo, d.subcategoria
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

    def vincular_empresa_a_ponto(self, id_ponto: str, id_empresa: str) -> None:
        """Associa uma empresa a um ponto de coleta."""
        with self.conn:
            self.conn.execute(
                "UPDATE ponto_coleta SET id_empresa = ? WHERE id = ?",
                (id_empresa, id_ponto)
            )
            self.conn.execute("""
                INSERT OR IGNORE INTO base_operacional (
                    id, empresa_id, ponto_coleta_id, nome, endereco,
                    latitude, longitude, raio_atendimento_km,
                    capacidade_kg, ocupacao_atual_kg,
                    realiza_coleta_domiciliar, ativa, criada_em, atualizada_em
                )
                SELECT 'base-' || id, ?, id, nome, endereco,
                       latitude, longitude, 25.0, capacidade_kg,
                       ocupacao_atual_kg, 1, ativo, datetime('now'), datetime('now')
                FROM ponto_coleta WHERE id = ?
            """, (id_empresa, id_ponto))

    def buscar_pontos_para_selecao(self):
        """Retorna apenas pontos vinculados a empresas para o select do formulario."""
        c = self.conn.cursor()
        c.execute("""
            SELECT pc.id, pc.nome, pc.endereco, pc.id_empresa,
                   COALESCE(u.nome, '') as nome_empresa
            FROM ponto_coleta pc
            JOIN usuario u ON pc.id_empresa = u.id
            WHERE pc.ativo = 1
            ORDER BY pc.nome
        """)
        return [dict(row) for row in c.fetchall()]

    def atualizar_detalhes_coleta(
        self, id_sol: str, tipo_coleta: str,
        endereco_coleta: str, nome_contato: str, data_agendamento: str
    ) -> None:
        """Salva tipo, endereco, nome de contato e data agendada na solicitacao."""
        with self.conn:
            self.conn.execute("""
                UPDATE solicitacao_descarte
                SET tipo_coleta=?, endereco_coleta=?, nome_contato=?, data_agendamento=?
                WHERE id=?
            """, (tipo_coleta, endereco_coleta or None, nome_contato or None,
                  data_agendamento or None, id_sol))

    def buscar_todos_cidadaos_admin(self):
        c = self.conn.cursor()
        c.execute("""
            SELECT u.id, u.nome, u.email, u.data_cadastro, ci.cpf, ci.pontos
            FROM usuario u
            JOIN cidadao ci ON u.id = ci.id_usuario
            WHERE u.tipo = 'cidadao'
        """)
        return [dict(row) for row in c.fetchall()]

    def buscar_todos_empresas_admin(self):
        """Retorna lista com id, nome, email, data_cadastro, cnpj e descartado_mes de todas as empresas."""
        c = self.conn.cursor()
        c.execute("""
            SELECT u.id, u.nome, u.email, u.data_cadastro, e.cnpj, e.descartado_mes
            FROM usuario u
            JOIN empresa e ON u.id = e.id_usuario
            WHERE u.tipo = 'empresa'
        """)
        return [dict(row) for row in c.fetchall()]

    def buscar_pontos_empresa(self, id_empresa: str):
        """Retorna todos os pontos de coleta ativos vinculados a esta empresa."""
        c = self.conn.cursor()
        c.execute("SELECT * FROM ponto_coleta WHERE id_empresa = ? AND ativo = 1", (id_empresa,))
        return [dict(row) for row in c.fetchall()]

    def buscar_solicitacoes_ponto(self, id_ponto: str):
        """Retorna todas as solicitações de um ponto, com nome do usuário."""
        c = self.conn.cursor()
        c.execute("""
            SELECT s.*, u.nome AS nome_usuario
            FROM solicitacao_descarte s
            JOIN usuario u ON s.id_usuario = u.id
            WHERE s.id_ponto_coleta = ?
            ORDER BY s.data_criacao DESC
        """, (id_ponto,))
        return [dict(row) for row in c.fetchall()]

    def confirmar_solicitacao(self, id_sol: str, quem: str) -> None:
        """Marca confirmado_cidadao ou confirmado_empresa na solicitação."""
        if quem not in ('cidadao', 'empresa'):
            raise ValueError("quem deve ser 'cidadao' ou 'empresa'")
        col = f'confirmado_{quem}'
        with self.conn:
            self.conn.execute(f"UPDATE solicitacao_descarte SET {col} = 1 WHERE id = ?", (id_sol,))

    def buscar_confirmacoes_solicitacao(self, id_sol: str) -> dict:
        """Retorna {confirmado_cidadao, confirmado_empresa} para a solicitação."""
        c = self.conn.cursor()
        c.execute(
            "SELECT confirmado_cidadao, confirmado_empresa FROM solicitacao_descarte WHERE id = ?",
            (id_sol,)
        )
        row = c.fetchone()
        if not row:
            return {'confirmado_cidadao': 0, 'confirmado_empresa': 0}
        return {
            'confirmado_cidadao': row['confirmado_cidadao'] or 0,
            'confirmado_empresa': row['confirmado_empresa'] or 0,
        }

    def buscar_solicitacoes_ativas_cidadao(self, id_usuario: str):
        """Retorna todas as solicitações não finalizadas de um cidadão."""
        ESTADOS_FINAIS = ('RECICLADO', 'REUTILIZADO', 'DESCARTADO', 'CANCELADO')
        c = self.conn.cursor()
        c.execute("""
            SELECT s.*, pc.nome AS nome_ponto
            FROM solicitacao_descarte s
            LEFT JOIN ponto_coleta pc ON s.id_ponto_coleta = pc.id
            WHERE s.id_usuario = ?
            ORDER BY s.data_criacao DESC
        """, (id_usuario,))
        rows = [dict(r) for r in c.fetchall()]
        return [r for r in rows if r['estado'] not in ESTADOS_FINAIS]

    def salvar_entrega_para_solicitacao(
        self, id_sol: str, id_usuario: str, valor: float, nome_empresa: str
    ) -> str:
        """Cria registro de entrega/incentivo quando a solicitação atinge estado final."""
        import uuid as _uuid
        id_entrega = str(_uuid.uuid4())
        now = datetime.now()
        with self.conn:
            self.conn.execute("""
                INSERT OR IGNORE INTO entrega
                    (id, id_solicitacao, id_usuario, valor, empresa, data, hora, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                id_entrega, id_sol, id_usuario, round(valor, 2), nome_empresa,
                now.strftime('%d/%m/%Y'), now.strftime('%H:%M'), 'finalizado'
            ))
        return id_entrega

    # -------------------
    # SEED
    # -------------------

    def seed(self):
        # no-op seed real está em _inicializar_dados_exemplo (web.py)
        pass

    # -------------------
    # TABELA DE PREÇOS
    # -------------------

    def buscar_tabela_precos(self):
        c = self.conn.cursor()
        c.execute("SELECT * FROM tabela_precos ORDER BY categoria, subcategoria")
        return c.fetchall()

    def buscar_preco_subcategoria(self, subcategoria: str):
        c = self.conn.cursor()
        c.execute("SELECT * FROM tabela_precos WHERE subcategoria = ?", (subcategoria,))
        return c.fetchone()

    def atualizar_avaliacao_solicitacao(
        self, id_sol: str, estado_produto: str,
        valor_proposto: float, justificativa: str, status_override: str
    ):
        with self.conn:
            self.conn.execute("""
                UPDATE solicitacao_descarte
                SET estado_produto = ?, valor_proposto = ?,
                    justificativa_valor = ?, status_override = ?
                WHERE id = ?
            """, (estado_produto, valor_proposto, justificativa, status_override, id_sol))

    def buscar_avaliacao_solicitacao(self, id_sol: str):
        c = self.conn.cursor()
        c.execute("""
            SELECT estado_produto, valor_proposto, justificativa_valor, status_override
            FROM solicitacao_descarte WHERE id = ?
        """, (id_sol,))
        return c.fetchone()

    def buscar_overrides_pendentes(self):
        """Retorna solicitações aguardando aprovação de override de valor."""
        c = self.conn.cursor()
        c.execute("""
            SELECT sd.id, sd.data_criacao, sd.estado_produto, sd.valor_proposto,
                   sd.justificativa_valor, u.nome as nome_usuario, u.tipo as tipo_usuario
            FROM solicitacao_descarte sd
            JOIN usuario u ON sd.id_usuario = u.id
            WHERE sd.status_override = 'pendente_doc'
            ORDER BY sd.data_criacao DESC
        """)
        return c.fetchall()

    def aprovar_override(self, id_sol: str):
        """Aprova o override de valor proposto pelo operador."""
        c = self.conn.cursor()
        c.execute(
            "UPDATE solicitacao_descarte SET status_override = 'aprovado' WHERE id = ?",
            (id_sol,)
        )
        self.conn.commit()

    def rejeitar_override(self, id_sol: str, valor_recalculado: float):
        """Rejeita o override, revertendo ao valor calculado automaticamente."""
        c = self.conn.cursor()
        c.execute(
            "UPDATE solicitacao_descarte SET status_override = 'rejeitado', valor_proposto = ? WHERE id = ?",
            (valor_recalculado, id_sol)
        )
        self.conn.commit()

    # -------------------
    # RECEITA / SALDO
    # -------------------

    def atualizar_saldo_empresa(self, id_empresa: str, delta: float):
        """Credita delta no saldo financeiro da empresa."""
        c = self.conn.cursor()
        c.execute(
            "UPDATE empresa SET saldo = COALESCE(saldo, 0.0) + ? WHERE id_usuario = ?",
            (delta, id_empresa)
        )
        self.conn.commit()

    def buscar_saldo_empresa(self, id_empresa: str) -> float:
        """Retorna o saldo financeiro acumulado da empresa."""
        c = self.conn.cursor()
        c.execute("SELECT saldo FROM empresa WHERE id_usuario = ?", (id_empresa,))
        row = c.fetchone()
        return float(row['saldo']) if row and row['saldo'] is not None else 0.0

    def registrar_receita_ecotech(self, id_sol: str, valor: float) -> bool:
        """Registra uma única receita por solicitação e informa se foi criada."""
        import uuid
        c = self.conn.cursor()
        c.execute(
            "INSERT OR IGNORE INTO receita_ecotech "
            "(id, id_solicitacao, valor, data) VALUES (?, ?, ?, ?)",
            (str(uuid.uuid4()), id_sol, valor, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        self.conn.commit()
        return c.rowcount == 1

    def buscar_receita_total_ecotech(self) -> float:
        """Retorna a receita total acumulada da EcoTech."""
        c = self.conn.cursor()
        c.execute("SELECT COALESCE(SUM(valor), 0.0) AS total FROM receita_ecotech")
        return float(c.fetchone()['total'])

    def buscar_historico_receita_ecotech(self):
        """Retorna todas as entradas de receita da EcoTech, mais recentes primeiro."""
        c = self.conn.cursor()
        c.execute("SELECT * FROM receita_ecotech ORDER BY data DESC")
        return c.fetchall()

    def atualizar_preco_subcategoria(self, subcategoria: str, valor_base: float, valor_minimo: float):
        """Atualiza os valores de uma subcategoria na tabela de preços."""
        c = self.conn.cursor()
        c.execute(
            "UPDATE tabela_precos SET valor_base_funcionando = ?, valor_minimo_sucata = ? WHERE subcategoria = ?",
            (valor_base, valor_minimo, subcategoria)
        )
        self.conn.commit()

    def buscar_versao_schema(self) -> int:
        """Retorna a versão mais recente aplicada ao schema."""
        return versao_atual(self.conn)
